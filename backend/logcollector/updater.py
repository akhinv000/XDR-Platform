from typing import Optional, List
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Log


def update_logs(logs: List[dict], db: Optional[Session] = None):
    """
    Persists structured logs to PostgreSQL, avoiding duplicate entries.
    """
    created_session = False
    if db is None:
        db = SessionLocal()
        created_session = True

    new_logs_count = 0
    try:
        # Load existing log signatures for fast in-memory deduplication
        existing_signatures = set()
        recent_logs = db.query(Log.hostname, Log.source, Log.message).limit(2000).all()
        for r in recent_logs:
            existing_signatures.add((r[0], r[1], r[2]))

        for item in logs:
            sig = (item["hostname"], item["source"], item["message"])
            if sig in existing_signatures:
                continue

            log = Log(
                timestamp=item["timestamp"],
                hostname=item["hostname"],
                level=item["level"],
                source=item["source"],
                message=item["message"]
            )
            db.add(log)
            existing_signatures.add(sig)
            new_logs_count += 1

        db.commit()
    finally:
        if created_session:
            db.close()

    return new_logs_count