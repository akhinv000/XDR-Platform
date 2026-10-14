from typing import Optional, List
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Log


def detect_alerts(db: Optional[Session] = None, logs_to_evaluate: Optional[List] = None):
    """
    Evaluates system logs and extracts actionable security alerts
    using heuristic detection signatures.
    """
    created_session = False
    if db is None:
        db = SessionLocal()
        created_session = True

    alerts = []
    try:
        if logs_to_evaluate is not None:
            logs = logs_to_evaluate
        else:
            # Query recent logs (limit to recent 1000 to prevent OOM)
            logs = db.query(Log).order_by(Log.id.desc()).limit(1000).all()

        for log in logs:
            msg = log.message if hasattr(log, "message") else log.get("message", "")
            hostname = log.hostname if hasattr(log, "hostname") else log.get("hostname", "Unknown")
            ts = log.timestamp if hasattr(log, "timestamp") else log.get("timestamp")

            if "Failed password" in msg or "password check failed" in msg or "authentication failure" in msg:
                alerts.append({
                    "timestamp": ts,
                    "hostname": hostname,
                    "severity": "High",
                    "title": "SSH / Auth Failed Login",
                    "description": msg,
                    "status": "Open"
                })

            elif "sudo" in msg:
                alerts.append({
                    "timestamp": ts,
                    "hostname": hostname,
                    "severity": "Medium",
                    "title": "Privilege Escalation Attempt",
                    "description": msg,
                    "status": "Open"
                })

            elif "Accepted password" in msg:
                alerts.append({
                    "timestamp": ts,
                    "hostname": hostname,
                    "severity": "Low",
                    "title": "Successful Login Event",
                    "description": msg,
                    "status": "Open"
                })

    finally:
        if created_session:
            db.close()

    return alerts