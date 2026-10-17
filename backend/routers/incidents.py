from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Incident, Alert, Asset, BlockedIP, ContainmentAction, User
from auth_utils import get_current_user


router = APIRouter(prefix="/incidents", tags=["Case & Incident Management"])


class IncidentStatusUpdate(BaseModel):
    status: str  # New, Investigating, Contained, Resolved, Closed


class IncidentNotesUpdate(BaseModel):
    notes: str


@router.get("/")
def get_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all aggregated security incidents with optional filters."""
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)

    incidents = query.order_by(Incident.updated_at.desc()).limit(100).all()
    return [
        {
            "id": inc.id,
            "title": inc.title,
            "severity": inc.severity,
            "status": inc.status,
            "mitre_tactic": inc.mitre_tactic or "General",
            "mitre_technique": inc.mitre_technique or "General",
            "hostname": inc.hostname or "Unknown",
            "source_ip": inc.source_ip or "",
            "alert_count": inc.alert_count,
            "analyst_notes": inc.analyst_notes or "",
            "assigned_to": inc.assigned_to or "Unassigned",
            "created_at": inc.created_at.isoformat() if inc.created_at else "",
            "updated_at": inc.updated_at.isoformat() if inc.updated_at else "",
        }
        for inc in incidents
    ]


@router.get("/{incident_id}")
def get_incident_detail(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full incident details including all correlated threat alerts."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    alerts = db.query(Alert).filter(Alert.incident_id == incident_id).order_by(Alert.id.desc()).all()
    return {
        "id": inc.id,
        "title": inc.title,
        "severity": inc.severity,
        "status": inc.status,
        "mitre_tactic": inc.mitre_tactic,
        "mitre_technique": inc.mitre_technique,
        "hostname": inc.hostname,
        "source_ip": inc.source_ip,
        "alert_count": inc.alert_count,
        "analyst_notes": inc.analyst_notes,
        "assigned_to": inc.assigned_to,
        "created_at": inc.created_at.isoformat() if inc.created_at else "",
        "updated_at": inc.updated_at.isoformat() if inc.updated_at else "",
        "correlated_alerts": [
            {
                "id": str(a.id),
                "timestamp": a.timestamp.isoformat() if a.timestamp else "",
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "mitre_tactic": a.mitre_tactic,
                "mitre_technique": a.mitre_technique,
                "source_ip": a.source_ip,
                "status": a.status
            }
            for a in alerts
        ]
    }


@router.put("/{incident_id}/status")
def update_incident_status(
    incident_id: int,
    payload: IncidentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Transition an incident lifecycle status."""
    valid_statuses = ["New", "Investigating", "Contained", "Resolved", "Closed"]
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(valid_statuses)}")

    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    inc.status = payload.status
    inc.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": f"Incident #{incident_id} marked as {payload.status}.", "status": inc.status}


@router.post("/{incident_id}/notes")
def update_incident_notes(
    incident_id: int,
    payload: IncidentNotesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Append or update analyst investigation notes."""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    inc.analyst_notes = payload.notes
    inc.assigned_to = current_user.username
    inc.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Analyst notes saved.", "analyst_notes": inc.analyst_notes}


@router.post("/{incident_id}/contain")
def execute_incident_containment(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute full automated containment for an incident:
    1. Quarantines the affected endpoint
    2. Blocks the attacker IP if known
    3. Updates incident status to 'Contained'
    """
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    now = datetime.now(timezone.utc)
    containment_summary = []

    # 1. Quarantine Endpoint
    asset = db.query(Asset).filter(Asset.hostname == inc.hostname).first()
    if asset:
        asset.status = "Quarantined"
        containment_summary.append(f"Host '{asset.hostname}' quarantined.")
        db.add(ContainmentAction(
            timestamp=now,
            action_type="QUARANTINE_HOST",
            target=asset.hostname,
            performed_by=current_user.username,
            details=f"Automated containment triggered from Incident #{incident_id}",
            status="Executed"
        ))

    # 2. Block Attacker IP
    if inc.source_ip:
        existing_block = db.query(BlockedIP).filter(BlockedIP.ip_address == inc.source_ip).first()
        if not existing_block:
            db.add(BlockedIP(
                ip_address=inc.source_ip,
                reason=f"Auto-blocked via Incident #{incident_id} containment",
                blocked_by=current_user.username,
                status="Active",
                blocked_at=now
            ))
            containment_summary.append(f"Source IP '{inc.source_ip}' blocked.")
            db.add(ContainmentAction(
                timestamp=now,
                action_type="BLOCK_IP",
                target=inc.source_ip,
                performed_by=current_user.username,
                details=f"Auto-blocked via Incident #{incident_id} containment",
                status="Executed"
            ))

    inc.status = "Contained"
    inc.updated_at = now
    db.commit()

    return {
        "message": "Incident containment executed successfully.",
        "incident_id": inc.id,
        "status": "Contained",
        "actions_taken": containment_summary
    }
