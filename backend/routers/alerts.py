from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Alert, User
from auth_utils import get_current_user
from alerts.detector import detect_alerts
from alerts.updater import update_alerts
from opensearch_client import client, is_opensearch_available

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.get("/")
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all open and active security alerts."""
    # If OpenSearch is available and holds events, query it
    if is_opensearch_available():
        try:
            response = client.search(
                index="security-auditlog-*",
                body={
                    "size": 100,
                    "sort": [{"@timestamp": {"order": "desc"}}]
                }
            )
            hits = response.get("hits", {}).get("hits", [])
            if hits:
                alerts = []
                for hit in hits:
                    source = hit["_source"]
                    category = source.get("audit_category", "")
                    if category in ["FAILED_LOGIN", "SSL_EXCEPTION"]:
                        severity = "High"
                    elif category in ["INDEX_EVENT", "COMPLIANCE_INTERNAL_CONFIG_WRITE"]:
                        severity = "Medium"
                    else:
                        severity = "Low"

                    alerts.append({
                        "id": str(hit["_id"]),
                        "timestamp": source.get("@timestamp", ""),
                        "hostname": source.get("audit_node_name", "OpenSearch Node"),
                        "severity": severity,
                        "title": category.replace("_", " ").title(),
                        "description": (
                            f"{source.get('audit_rest_request_method', '')} "
                            f"{source.get('audit_rest_request_path', '')} "
                            f"by {source.get('audit_request_effective_user', 'Unknown')}"
                        ).strip(),
                        "status": "Open"
                    })
                return alerts
        except Exception:
            pass

    # Read from PostgreSQL alerts table
    db_alerts = (
        db.query(Alert)
        .order_by(Alert.id.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": str(r.id),
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "hostname": r.hostname or "Unknown",
            "severity": r.severity or "Low",
            "title": r.title or "Security Event",
            "description": r.description or "",
            "status": r.status or "Open"
        }
        for r in db_alerts
    ]


@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge and mark a security alert as reviewed."""
    if alert_id.isdigit():
        alert = db.query(Alert).filter(Alert.id == int(alert_id)).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        alert.status = "Acknowledged"
        db.commit()
        return {
            "message": f"Alert {alert_id} successfully marked as Acknowledged.",
            "status": "Acknowledged"
        }

    return {
        "message": f"Alert {alert_id} acknowledged."
    }


@router.post("/detect")
def trigger_detection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run detection heuristics across existing logs."""
    detected = detect_alerts(db=db)
    new_alerts = update_alerts(detected, db=db)
    return {
        "message": "Detection completed successfully.",
        "new_alerts_created": new_alerts,
        "total_evaluated": len(detected)
    }