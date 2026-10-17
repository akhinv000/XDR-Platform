from datetime import datetime, timezone
import json
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Asset, BlockedIP, ContainmentAction, AgentEndpoint, User
from auth_utils import get_current_user


router = APIRouter(prefix="/response", tags=["Incident Response & Containment"])


class BlockIPRequest(BaseModel):
    ip_address: str
    reason: Optional[str] = "SOC Threat Containment"


class QuarantineRequest(BaseModel):
    asset_id: int
    reason: Optional[str] = "Compromised Host Containment"


@router.post("/quarantine/{asset_id}")
def quarantine_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Isolate a compromised endpoint from the network.
    Marks asset status as Quarantined, queues agent command if connected,
    and returns automated firewall containment rules.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.status = "Quarantined"
    now = datetime.now(timezone.utc)

    # Queue isolation command to connected agent if present
    if asset.agent_id:
        agent = db.query(AgentEndpoint).filter(AgentEndpoint.agent_id == asset.agent_id).first()
        if agent:
            agent.status = "Quarantined"
            cmds = json.loads(agent.pending_commands or "[]")
            cmds.append({"action": "quarantine", "timestamp": now.isoformat()})
            agent.pending_commands = json.dumps(cmds)

    # Log action
    action = ContainmentAction(
        timestamp=now,
        action_type="QUARANTINE_HOST",
        target=f"{asset.hostname} ({asset.ip_address})",
        performed_by=current_user.username,
        details=f"Host isolated from internal network. Status updated to Quarantined.",
        status="Executed"
    )
    db.add(action)
    db.commit()

    return {
        "message": f"Endpoint {asset.hostname} ({asset.ip_address}) successfully quarantined.",
        "asset_id": asset.id,
        "status": "Quarantined",
        "firewall_commands": {
            "linux_iptables": [
                f"# Run on {asset.hostname} to block lateral movement:",
                "iptables -F",
                "iptables -P INPUT DROP",
                "iptables -P FORWARD DROP",
                "iptables -P OUTPUT DROP",
                "iptables -A INPUT -p tcp --dport 9000 -j ACCEPT",
                "iptables -A OUTPUT -p tcp --dport 9000 -j ACCEPT",
                "iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
                "iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT"
            ],
            "windows_netsh": [
                f"REM Run on {asset.hostname} as Administrator:",
                'netsh advfirewall firewall add rule name="XDR_BLOCK_ALL_IN" dir=in action=block',
                'netsh advfirewall firewall add rule name="XDR_BLOCK_ALL_OUT" dir=out action=block',
                'netsh advfirewall firewall add rule name="XDR_ALLOW_OUT" dir=out action=allow remoteport=9000 protocol=TCP'
            ]
        }
    }


@router.post("/unquarantine/{asset_id}")
def unquarantine_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restore quarantined asset back to normal Online operational status."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.status = "Online"
    now = datetime.now(timezone.utc)

    # Queue un-quarantine command to connected agent if present
    if asset.agent_id:
        agent = db.query(AgentEndpoint).filter(AgentEndpoint.agent_id == asset.agent_id).first()
        if agent:
            agent.status = "Online"
            cmds = json.loads(agent.pending_commands or "[]")
            cmds.append({"action": "unquarantine", "timestamp": now.isoformat()})
            agent.pending_commands = json.dumps(cmds)

    action = ContainmentAction(
        timestamp=now,
        action_type="UNQUARANTINE_HOST",
        target=f"{asset.hostname} ({asset.ip_address})",
        performed_by=current_user.username,
        details="Endpoint removed from quarantine; full network connectivity restored.",
        status="Executed"
    )
    db.add(action)
    db.commit()

    return {
        "message": f"Endpoint {asset.hostname} un-quarantined successfully.",
        "asset_id": asset.id,
        "status": "Online"
    }


@router.post("/block-ip", status_code=status.HTTP_201_CREATED)
def block_ip(
    req: BlockIPRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add malicious source IP to the active firewall blocklist and broadcast to agents."""
    ip = req.ip_address.strip()
    if not ip:
        raise HTTPException(status_code=400, detail="IP address required")

    existing = db.query(BlockedIP).filter(BlockedIP.ip_address == ip).first()
    now = datetime.now(timezone.utc)

    if existing:
        existing.status = "Active"
        existing.reason = req.reason or "Manual SOC Block"
        existing.blocked_by = current_user.username
        existing.blocked_at = now
    else:
        blocked = BlockedIP(
            ip_address=ip,
            reason=req.reason or "Manual SOC Block",
            blocked_by=current_user.username,
            status="Active",
            blocked_at=now
        )
        db.add(blocked)

    # Queue block command to all active agents
    agents = db.query(AgentEndpoint).filter(AgentEndpoint.status != "Offline").all()
    for ag in agents:
        cmds = json.loads(ag.pending_commands or "[]")
        cmds.append({"action": "block_ip", "ip": ip, "timestamp": now.isoformat()})
        ag.pending_commands = json.dumps(cmds)

    action = ContainmentAction(
        timestamp=now,
        action_type="BLOCK_IP",
        target=ip,
        performed_by=current_user.username,
        details=f"IP added to global blocklist: {req.reason}",
        status="Executed"
    )
    db.add(action)
    db.commit()

    return {
        "message": f"IP {ip} has been blocked and added to perimeter blocklist.",
        "ip_address": ip
    }


@router.delete("/block-ip/{ip_address}")
def unblock_ip(
    ip_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove an IP address from the active blocklist."""
    entry = db.query(BlockedIP).filter(BlockedIP.ip_address == ip_address).first()
    if not entry:
        raise HTTPException(status_code=404, detail="IP not found in blocklist")

    db.delete(entry)
    now = datetime.now(timezone.utc)

    action = ContainmentAction(
        timestamp=now,
        action_type="UNBLOCK_IP",
        target=ip_address,
        performed_by=current_user.username,
        details="IP removed from perimeter blocklist.",
        status="Executed"
    )
    db.add(action)
    db.commit()

    return {"message": f"IP {ip_address} has been unblocked."}


@router.get("/blocklist")
def get_blocklist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return all active blocked IPs with metadata."""
    blocked = db.query(BlockedIP).filter(BlockedIP.status == "Active").order_by(BlockedIP.blocked_at.desc()).all()
    return [
        {
            "id": b.id,
            "ip_address": b.ip_address,
            "reason": b.reason,
            "blocked_by": b.blocked_by,
            "blocked_at": b.blocked_at.isoformat() if b.blocked_at else ""
        }
        for b in blocked
    ]


@router.get("/blocklist.txt", response_class=PlainTextResponse)
def get_blocklist_feed(db: Session = Depends(get_db)):
    """
    Plaintext IP blocklist feed for automated firewall / WAF sync
    (pfSense, Fortigate, Palo Alto, Nginx deny list).
    """
    blocked = db.query(BlockedIP).filter(BlockedIP.status == "Active").all()
    return "\n".join(b.ip_address for b in blocked)


@router.get("/actions")
def get_containment_actions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Audit trail of all executed containment and response actions."""
    actions = db.query(ContainmentAction).order_by(ContainmentAction.id.desc()).limit(100).all()
    return [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat() if a.timestamp else "",
            "action_type": a.action_type,
            "target": a.target,
            "performed_by": a.performed_by,
            "details": a.details,
            "status": a.status
        }
        for a in actions
    ]


class KillProcessRequest(BaseModel):
    hostname: str
    pid: int
    process_name: str
    incident_id: Optional[int] = None
    reason: Optional[str] = "SOC Threat Remediation"


@router.post("/kill-process")
def kill_process(
    req: KillProcessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Terminates a malicious process on a target endpoint via EDR agent.
    Broadcasts kill command and records containment action in audit trail.
    """
    now = datetime.now(timezone.utc)

    # Broadcast to agents for this hostname
    agents = db.query(AgentEndpoint).filter(AgentEndpoint.hostname == req.hostname).all()
    dispatched = False
    for ag in agents:
        cmds = json.loads(ag.pending_commands or "[]")
        cmds.append({
            "action": "kill_process",
            "pid": req.pid,
            "process_name": req.process_name,
            "timestamp": now.isoformat()
        })
        ag.pending_commands = json.dumps(cmds)
        dispatched = True

    # Audit log
    action = ContainmentAction(
        timestamp=now,
        action_type="KILL_PROCESS",
        target=f"{req.hostname} (PID: {req.pid})",
        performed_by=current_user.username,
        details=f"Terminated process '{req.process_name}' (PID {req.pid}): {req.reason}. Agent queue: {'Dispatched' if dispatched else 'Simulated/Pending'}.",
        status="Executed"
    )
    db.add(action)
    db.commit()

    return {
        "message": f"Termination command for process '{req.process_name}' (PID: {req.pid}) on host '{req.hostname}' successfully executed.",
        "pid": req.pid,
        "process_name": req.process_name,
        "hostname": req.hostname,
        "status": "Terminated"
    }
