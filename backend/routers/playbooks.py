"""
SOAR (Security Orchestration, Automation, and Response) Playbook Engine for XDR BASE
Executes automated rule-to-action containment pipelines when critical threats are detected.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models import Asset, BlockedIP, ContainmentAction, Incident, User
from auth_utils import get_current_user

router = APIRouter(prefix="/playbooks", tags=["SOAR Automation & Playbooks"])

# In-memory configuration store for playbooks (persists while backend runs)
PLAYBOOKS_CONFIG = {
    "playbook-c2-ransomware": {
        "id": "playbook-c2-ransomware",
        "name": "Ransomware & C2 Autonomous Containment",
        "description": "Automatically isolate compromised endpoint and blacklist C2 IP on perimeter firewall when Critical severity or ransomware/C2 indicators are detected.",
        "trigger": "Severity == 'Critical' or MITRE in ['T1059.001', 'T1486', 'T1218.011']",
        "enabled": True,
        "actions": ["Quarantine Host", "Block Perimeter IP", "Append Incident Dossier"],
        "executions_count": 8,
        "last_executed": "2026-10-17T12:45:00Z"
    },
    "playbook-bruteforce-ban": {
        "id": "playbook-bruteforce-ban",
        "name": "Brute-Force Automatic IP Blackhole",
        "description": "Instantly block source IP on active firewall rules when more than 3 failed authentication attempts occur within sliding time window.",
        "trigger": "MITRE == 'T1110.001' or title contains 'Brute-Force'",
        "enabled": True,
        "actions": ["Block Perimeter IP", "Broadcast Agent Blocklist"],
        "executions_count": 14,
        "last_executed": "2026-10-17T12:50:22Z"
    },
    "playbook-privesc-quarantine": {
        "id": "playbook-privesc-quarantine",
        "name": "Privilege Escalation Containment & Forensic Freeze",
        "description": "Marks host risk score to Critical (95+) and generates containment notice on unauthorized sudo / privilege escalation attempts.",
        "trigger": "MITRE == 'T1548.003' or title contains 'Privilege Escalation'",
        "enabled": True,
        "actions": ["Elevate Risk Score (95)", "Notify SOC Operator"],
        "executions_count": 5,
        "last_executed": "2026-10-17T12:30:10Z"
    }
}


def run_soar_playbook(alert_dict: Dict[str, Any], incident: Optional[Incident], db: Session) -> List[str]:
    """
    Evaluates newly created alerts against enabled SOAR playbooks and executes
    autonomous containment actions (Quarantine host, Block IP).
    """
    executed_actions = []
    now = datetime.now(timezone.utc)
    severity = alert_dict.get("severity", "Low")
    mitre_tech = alert_dict.get("mitre_technique", "")
    src_ip = alert_dict.get("source_ip", "").strip()
    hostname = alert_dict.get("hostname", "Unknown")
    title = alert_dict.get("title", "")

    # Playbook 1: Critical Ransomware / C2
    p1 = PLAYBOOKS_CONFIG.get("playbook-c2-ransomware")
    if p1 and p1["enabled"]:
        is_crit = severity == "Critical" or any(t in mitre_tech for t in ["T1059", "T1486", "T1218"])
        if is_crit:
            # 1. Quarantine Host
            if hostname and hostname != "Unknown":
                asset = db.query(Asset).filter(Asset.hostname == hostname).first()
                if asset and asset.status != "Quarantined":
                    asset.status = "Quarantined"
                    action_q = ContainmentAction(
                        timestamp=now,
                        action_type="QUARANTINE_HOST",
                        target=f"{hostname} ({asset.ip_address})",
                        performed_by="SOAR Playbook: Ransomware Auto-Containment",
                        details="Host autonomously isolated due to Critical threat detection.",
                        status="Executed"
                    )
                    db.add(action_q)
                    executed_actions.append(f"Auto-quarantined host '{hostname}'")

            # 2. Block IP
            if src_ip and src_ip not in ["127.0.0.1", "localhost", ""]:
                existing_block = db.query(BlockedIP).filter(BlockedIP.ip_address == src_ip).first()
                if not existing_block:
                    block_entry = BlockedIP(
                        ip_address=src_ip,
                        reason=f"SOAR Auto-Ban: {title}",
                        blocked_by="SOAR Autonomous Engine",
                        status="Active",
                        blocked_at=now
                    )
                    db.add(block_entry)
                    action_b = ContainmentAction(
                        timestamp=now,
                        action_type="BLOCK_IP",
                        target=src_ip,
                        performed_by="SOAR Playbook: Ransomware Auto-Containment",
                        details=f"IP {src_ip} automatically blocked at perimeter firewall.",
                        status="Executed"
                    )
                    db.add(action_b)
                    executed_actions.append(f"Auto-blocked attacker IP '{src_ip}'")

            p1["executions_count"] += 1
            p1["last_executed"] = now.isoformat()

    # Playbook 2: Brute-Force Ban
    p2 = PLAYBOOKS_CONFIG.get("playbook-bruteforce-ban")
    if p2 and p2["enabled"]:
        if "T1110" in mitre_tech or "brute-force" in title.lower():
            if src_ip and src_ip not in ["127.0.0.1", "localhost", ""]:
                existing_block = db.query(BlockedIP).filter(BlockedIP.ip_address == src_ip).first()
                if not existing_block:
                    block_entry = BlockedIP(
                        ip_address=src_ip,
                        reason="SOAR Auto-Ban: Auth Brute-Force Campaign",
                        blocked_by="SOAR Autonomous Engine",
                        status="Active",
                        blocked_at=now
                    )
                    db.add(block_entry)
                    action_b = ContainmentAction(
                        timestamp=now,
                        action_type="BLOCK_IP",
                        target=src_ip,
                        performed_by="SOAR Playbook: Brute-Force Blackhole",
                        details=f"Brute-force attacker {src_ip} automatically dropped.",
                        status="Executed"
                    )
                    db.add(action_b)
                    executed_actions.append(f"Auto-blacklisted brute-force IP '{src_ip}'")

            p2["executions_count"] += 1
            p2["last_executed"] = now.isoformat()

    # If actions were taken, update incident analyst notes
    if executed_actions and incident:
        stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        remediation_note = f"\n[{stamp} SOAR PLAYBOOK EXECUTED]: " + "; ".join(executed_actions)
        incident.analyst_notes = (incident.analyst_notes or "") + remediation_note
        db.commit()

    return executed_actions


@router.get("")
def list_playbooks(current_user: User = Depends(get_current_user)) -> List[Dict[str, Any]]:
    """Return list of all configured automated SOAR playbooks and live metrics."""
    return list(PLAYBOOKS_CONFIG.values())


@router.post("/{playbook_id}/toggle")
def toggle_playbook(
    playbook_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Toggle a playbook's autonomous execution state (Enabled / Disabled)."""
    if playbook_id not in PLAYBOOKS_CONFIG:
        raise HTTPException(status_code=404, detail="Playbook not found")

    pb = PLAYBOOKS_CONFIG[playbook_id]
    pb["enabled"] = not pb["enabled"]
    return {
        "message": f"Playbook '{pb['name']}' is now {'ENABLED' if pb['enabled'] else 'DISABLED'}.",
        "playbook_id": playbook_id,
        "enabled": pb["enabled"]
    }
