from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models import Log, User
from schemas import LogIngestRequest
from auth_utils import get_current_user
from logcollector.collector import collect_logs
from alerts.detector import detect_alerts
from alerts.updater import update_alerts
from opensearch_client import client, is_opensearch_available

router = APIRouter(
    prefix="/logs",
    tags=["Security Logs"]
)


@router.get("/")
def get_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve the latest ingested security and authentication logs."""
    # First attempt OpenSearch if available and containing security data
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
                logs = []
                for hit in hits:
                    source = hit["_source"]
                    logs.append({
                        "id": str(hit["_id"]),
                        "timestamp": source.get("@timestamp", ""),
                        "hostname": source.get("audit_node_name", "OpenSearch Node"),
                        "level": (
                            "High" if source.get("audit_category") in ["FAILED_LOGIN", "SSL_EXCEPTION"]
                            else "Medium" if source.get("audit_category") in ["INDEX_EVENT", "COMPLIANCE_INTERNAL_CONFIG_WRITE"]
                            else "Low"
                        ),
                        "category": source.get("audit_category", "AUDIT"),
                        "source": source.get("audit_request_origin", "REST"),
                        "message": (
                            f"{source.get('audit_rest_request_method', '')} "
                            f"{source.get('audit_rest_request_path', '')} "
                            f"by {source.get('audit_request_effective_user', 'Unknown')}"
                        ).strip()
                    })
                return logs
        except Exception:
            pass

    # Fallback to PostgreSQL logs
    db_logs = (
        db.query(Log)
        .order_by(Log.id.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": str(r.id),
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "hostname": r.hostname or "System",
            "level": r.level or "Low",
            "category": "AUTH",
            "source": r.source or "System",
            "message": r.message or ""
        }
        for r in db_logs
    ]


@router.post("/collect")
def trigger_log_collection(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger automated parsing of auth.log and threat alert detection."""
    summary = collect_logs(db=db)
    return {
        "message": "Log collection and detection completed successfully.",
        "summary": summary
    }


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_single_log(
    log_data: LogIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ingest a single security event in real time and evaluate threat rules."""
    new_log = Log(
        timestamp=datetime.now(timezone.utc),
        hostname=log_data.hostname,
        level=log_data.level or "Low",
        source=log_data.source or "System",
        message=log_data.message
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    # Evaluate threat alert
    detected = detect_alerts(db=db, logs_to_evaluate=[new_log])
    new_alerts = update_alerts(detected, db=db)

    return {
        "message": "Log event ingested successfully.",
        "log_id": new_log.id,
        "alerts_triggered": new_alerts
    }


@router.get("/hunt")
def hunt_logs(
    q: str = "",
    limit: int = 150,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    KQL / Fielded Threat Hunting Query Parser.
    Supports syntax:
      hostname:web-srv-01
      level:Critical / severity:High
      ip:192.168.1.50
      source:auth.log
      message:powershell
      Free-text terms
    """
    import re
    from sqlalchemy import or_, and_

    raw_query = q.strip()
    query_obj = db.query(Log)

    if raw_query:
        tokens = re.findall(r'(?:(\w+):(?:"([^"]+)"|(\S+)))|(?:"([^"]+)"|(\S+))', raw_query)
        filters = []

        for host_k, val_q, val_raw, free_q, free_raw in tokens:
            key = host_k.lower() if host_k else ""
            val = val_q or val_raw or free_q or free_raw or ""
            if not val:
                continue

            if key in ["host", "hostname"]:
                filters.append(Log.hostname.ilike(f"%{val}%"))
            elif key in ["level", "severity"]:
                filters.append(Log.level.ilike(f"%{val}%"))
            elif key in ["source", "src"]:
                filters.append(Log.source.ilike(f"%{val}%"))
            elif key in ["message", "msg", "payload"]:
                filters.append(Log.message.ilike(f"%{val}%"))
            elif key in ["ip", "source_ip", "src_ip"]:
                filters.append(Log.message.ilike(f"%{val}%"))
            else:
                filters.append(or_(
                    Log.message.ilike(f"%{val}%"),
                    Log.hostname.ilike(f"%{val}%")
                ))

        if filters:
            query_obj = query_obj.filter(and_(*filters))

    logs = query_obj.order_by(Log.id.desc()).limit(limit).all()

    return [
        {
            "id": str(r.id),
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "hostname": r.hostname or "System",
            "level": r.level or "Low",
            "category": "HUNT_MATCH",
            "source": r.source or "System",
            "message": r.message or ""
        }
        for r in logs
    ]