import os
import json
import uuid
import secrets
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from fastapi.responses import PlainTextResponse, FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from database import get_db
from models import AgentEndpoint, Asset, Log, Alert, User
from auth_utils import get_current_user
from alerts.detector import detect_alerts
from alerts.updater import update_alerts
from logcollector.parser import parse_timestamp


router = APIRouter(prefix="/api/v1/agent", tags=["Agent & System Integration"])


class AgentRegisterRequest(BaseModel):
    hostname: str
    ip_address: str
    operating_system: Optional[str] = "Linux"
    os_version: Optional[str] = ""
    mac_address: Optional[str] = ""


class HeartbeatRequest(BaseModel):
    agent_id: str
    cpu_percent: Optional[float] = 0.0
    memory_percent: Optional[float] = 0.0
    disk_percent: Optional[float] = 0.0
    active_connections: Optional[int] = 0


class TelemetryEvent(BaseModel):
    message: str
    source: Optional[str] = "Agent"
    level: Optional[str] = "Low"
    timestamp: Optional[str] = None


class AgentTelemetryBatch(BaseModel):
    agent_id: str
    events: List[TelemetryEvent]


class SyslogIngestRequest(BaseModel):
    hostname: Optional[str] = "NetworkDevice"
    messages: List[str]


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_agent(req: AgentRegisterRequest, request: Request, db: Session = Depends(get_db)):
    """
    Onboard a new endpoint or network system.
    Issues a persistent agent_id and api_key, and registers or updates the asset inventory.
    """
    client_ip = req.ip_address or request.client.host
    hostname = req.hostname.strip()

    existing = db.query(AgentEndpoint).filter(
        (AgentEndpoint.hostname == hostname) | (AgentEndpoint.ip_address == client_ip)
    ).first()

    now = datetime.now(timezone.utc)
    if existing:
        existing.last_heartbeat = now
        existing.operating_system = req.operating_system
        existing.os_version = req.os_version
        db.commit()
        return {
            "message": f"Agent for '{hostname}' re-registered.",
            "agent_id": existing.agent_id,
            "api_key": existing.api_key,
            "status": existing.status
        }

    agent_id = f"agt_{uuid.uuid4().hex[:12]}"
    api_key = f"xdr_{secrets.token_hex(24)}"

    agent = AgentEndpoint(
        agent_id=agent_id,
        hostname=hostname,
        ip_address=client_ip,
        operating_system=req.operating_system or "Unknown",
        os_version=req.os_version or "",
        status="Online",
        api_key=api_key,
        first_seen=now,
        last_heartbeat=now,
        pending_commands="[]"
    )
    db.add(agent)

    # Automatically register into Asset inventory
    asset = db.query(Asset).filter(Asset.ip_address == client_ip).first()
    if asset:
        asset.agent_id = agent_id
        asset.hostname = hostname
        asset.operating_system = req.operating_system
        asset.status = "Online"
        asset.last_seen = now
    else:
        new_asset = Asset(
            hostname=hostname,
            ip_address=client_ip,
            mac_address=req.mac_address or "",
            operating_system=req.operating_system,
            asset_type=f"{req.operating_system} Endpoint",
            status="Online",
            agent_id=agent_id,
            risk_score=10,
            first_seen=now,
            last_seen=now
        )
        db.add(new_asset)

    db.commit()

    return {
        "message": f"System '{hostname}' successfully onboarded.",
        "agent_id": agent_id,
        "api_key": api_key,
        "status": "Online"
    }


@router.post("/heartbeat")
def agent_heartbeat(
    req: HeartbeatRequest,
    x_agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
    db: Session = Depends(get_db)
):
    """
    Periodic agent health check.
    Returns any pending containment actions or commands issued by SOC analysts.
    """
    agent = db.query(AgentEndpoint).filter(AgentEndpoint.agent_id == req.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not registered")

    if x_agent_key and isinstance(x_agent_key, str) and agent.api_key != x_agent_key:
        raise HTTPException(status_code=401, detail="Invalid Agent API Key")

    now = datetime.now(timezone.utc)
    agent.last_heartbeat = now

    # Also update asset last seen
    asset = db.query(Asset).filter(Asset.agent_id == agent.agent_id).first()
    if asset:
        asset.last_seen = now
        if agent.status == "Quarantined":
            asset.status = "Quarantined"

    # Fetch and clear pending commands for the agent
    commands = json.loads(agent.pending_commands or "[]")
    agent.pending_commands = "[]"
    db.commit()

    return {
        "status": agent.status,
        "commands": commands
    }


@router.post("/telemetry")
def ingest_agent_telemetry(
    batch: AgentTelemetryBatch,
    x_agent_key: Optional[str] = Header(None, alias="X-Agent-Key"),
    db: Session = Depends(get_db)
):
    """
    Stream real-time log events from remote endpoints directly into XDR.
    Evaluates correlation rules and triggers threat alerts automatically.
    """
    agent = db.query(AgentEndpoint).filter(AgentEndpoint.agent_id == batch.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not registered")

    if x_agent_key and isinstance(x_agent_key, str) and agent.api_key != x_agent_key:
        raise HTTPException(status_code=401, detail="Invalid Agent API Key")

    now = datetime.now(timezone.utc)
    new_logs = []

    for ev in batch.events:
        ts = parse_timestamp(ev.timestamp) if ev.timestamp else now
        log_entry = Log(
            timestamp=ts,
            hostname=agent.hostname,
            level=ev.level or "Low",
            source=ev.source or "Agent",
            message=ev.message
        )
        db.add(log_entry)
        new_logs.append(log_entry)

    db.commit()

    # Trigger detection on ingested logs
    detected = detect_alerts(db=db, logs_to_evaluate=new_logs)
    new_alerts = update_alerts(detected, db=db)

    return {
        "events_received": len(batch.events),
        "alerts_triggered": new_alerts
    }


@router.post("/syslog")
def ingest_syslog(
    req: SyslogIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Universal Syslog ingestion endpoint for network routers, firewalls, and servers
    forwarding logs via rsyslog, syslog-ng, or HTTP webhooks.
    """
    now = datetime.now(timezone.utc)
    new_logs = []

    for raw_msg in req.messages:
        raw_msg = raw_msg.strip()
        if not raw_msg:
            continue

        log_entry = Log(
            timestamp=now,
            hostname=req.hostname or "SyslogDevice",
            level="Low",
            source="Syslog",
            message=raw_msg
        )
        db.add(log_entry)
        new_logs.append(log_entry)

    db.commit()

    detected = detect_alerts(db=db, logs_to_evaluate=new_logs)
    new_alerts = update_alerts(detected, db=db)

    return {
        "received": len(req.messages),
        "alerts_triggered": new_alerts
    }


@router.get("/endpoints")
def list_connected_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all onboarded endpoints and their real-time connection status."""
    now = datetime.now(timezone.utc)
    agents = db.query(AgentEndpoint).order_by(AgentEndpoint.last_heartbeat.desc()).all()

    results = []
    for ag in agents:
        # If no heartbeat for > 60 seconds, mark as Inactive
        diff_seconds = (now - ag.last_heartbeat.replace(tzinfo=timezone.utc)).total_seconds() if ag.last_heartbeat else 9999
        live_status = ag.status
        if diff_seconds > 60 and ag.status != "Quarantined":
            live_status = "Offline"

        results.append({
            "agent_id": ag.agent_id,
            "hostname": ag.hostname,
            "ip_address": ag.ip_address,
            "operating_system": ag.operating_system,
            "os_version": ag.os_version,
            "status": live_status,
            "last_heartbeat": ag.last_heartbeat.isoformat() if ag.last_heartbeat else "",
            "seconds_since_heartbeat": int(diff_seconds)
        })

    return results


@router.get("/install.sh", response_class=PlainTextResponse)
def get_linux_installer(request: Request):
    """Dynamically generated Linux one-liner installer script."""
    server_url = f"{request.base_url}".rstrip("/")
    script = f"""#!/bin/bash
# ==========================================================
# XDR BASE - Universal Linux Agent Onboarding Script
# ==========================================================
set -e

SERVER_URL="{server_url}"
AGENT_DIR="/opt/xdr-agent"

echo "===================================================="
echo " [XDR BASE] Installing Security Telemetry Agent"
echo " Server: $SERVER_URL"
echo "===================================================="

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "[-] Please run as root (sudo bash install.sh)"
  exit 1
fi

# Ensure python3 is available
if ! command -v python3 &> /dev/null; then
    echo "[*] Installing python3..."
    if command -v apt-get &> /dev/null; then
        apt-get update && apt-get install -y python3
    elif command -v yum &> /dev/null; then
        yum install -y python3
    fi
fi

mkdir -p "$AGENT_DIR"
cd "$AGENT_DIR"

# Download lightweight agent runner
echo "[*] Fetching agent executable..."
curl -sSL "$SERVER_URL/api/v1/agent/xdr_agent.py" -o "$AGENT_DIR/xdr_agent.py"

# Write configuration
cat <<EOF > "$AGENT_DIR/config.json"
{{
    "server_url": "$SERVER_URL",
    "heartbeat_interval": 15
}}
EOF

# Install systemd service
cat <<EOF > /etc/systemd/system/xdr-agent.service
[Unit]
Description=XDR BASE Security Telemetry & Response Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$AGENT_DIR
ExecStart=/usr/bin/python3 $AGENT_DIR/xdr_agent.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable xdr-agent.service
systemctl restart xdr-agent.service

echo "[+] XDR Agent successfully installed and running!"
systemctl status xdr-agent.service --no-pager
"""
    return script


@router.get("/install.ps1", response_class=PlainTextResponse)
def get_windows_installer(request: Request):
    """Dynamically generated Windows PowerShell one-liner installer script."""
    server_url = f"{request.base_url}".rstrip("/")
    script = f"""# ==========================================================
# XDR BASE - Windows Telemetry Agent Onboarding Script
# ==========================================================
$ServerUrl = "{server_url}"
$InstallDir = "$env:ProgramData\\XDR-Agent"

Write-Host "====================================================" -ForegroundColor Green
Write-Host " [XDR BASE] Installing Windows Security Agent" -ForegroundColor Green
Write-Host " Server: $ServerUrl" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {{
    Write-Warning "[-] Please run PowerShell as Administrator."
    Exit 1
}}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null

Write-Host "[*] Downloading agent script..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "$ServerUrl/api/v1/agent/xdr_agent.ps1" -OutFile "$InstallDir\\xdr_agent.ps1" -UseBasicParsing

$Config = @{{
    server_url = "$ServerUrl"
    heartbeat_interval = 15
}} | ConvertTo-Json

$Config | Set-Content -Path "$InstallDir\\config.json"

Write-Host "[+] Agent configured. Starting background monitoring job..." -ForegroundColor Green
Start-Process powershell.exe -ArgumentList "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$InstallDir\\xdr_agent.ps1`""

Write-Host "[+] XDR Windows Agent is now active and streaming telemetry to $ServerUrl" -ForegroundColor Green
"""
    return script


@router.get("/xdr_agent.py")
def download_python_agent():
    """Download the standalone Python agent script."""
    agent_path = Path(__file__).parent.parent / "agent" / "xdr_agent.py"
    if not agent_path.exists():
        raise HTTPException(status_code=404, detail="Agent script not found")
    return FileResponse(path=str(agent_path), filename="xdr_agent.py", media_type="text/x-python")


@router.get("/xdr_agent.ps1")
def download_powershell_agent():
    """Download the standalone PowerShell agent script."""
    agent_path = Path(__file__).parent.parent / "agent" / "xdr_agent.ps1"
    if not agent_path.exists():
        raise HTTPException(status_code=404, detail="PowerShell agent script not found")
    return FileResponse(path=str(agent_path), filename="xdr_agent.ps1", media_type="text/plain")

