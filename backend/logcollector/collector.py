from typing import Optional
from sqlalchemy.orm import Session

from logcollector.parser import parse_auth_log
from logcollector.updater import update_logs
from alerts.detector import detect_alerts
from alerts.updater import update_alerts


def collect_logs(file_path=None, db: Optional[Session] = None):
    """
    Ingests logs from auth.log, stores them in the database,
    and triggers automated alert detection.
    """
    logs = parse_auth_log(file_path)
    new_logs = update_logs(logs, db=db)

    # Automatically trigger threat detection on newly ingested logs
    detected = detect_alerts(db=db, logs_to_evaluate=logs)
    new_alerts = update_alerts(detected, db=db)

    return {
        "logs_parsed": len(logs),
        "new_logs_inserted": new_logs,
        "new_alerts_generated": new_alerts
    }