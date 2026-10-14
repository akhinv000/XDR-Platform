from typing import Optional, List
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Alert


def update_alerts(alerts: List[dict], db: Optional[Session] = None):
    """
    Persists detected alerts into the database, ignoring duplicates.
    """
    created_session = False
    if db is None:
        db = SessionLocal()
        created_session = True

    new_alerts_count = 0
    try:
        for item in alerts:
            existing = (
                db.query(Alert)
                .filter(
                    Alert.hostname == item["hostname"],
                    Alert.title == item["title"],
                    Alert.description == item["description"],
                )
                .first()
            )

            if existing:
                continue

            alert = Alert(
                timestamp=item["timestamp"],
                hostname=item["hostname"],
                severity=item["severity"],
                title=item["title"],
                description=item["description"],
                status=item.get("status", "Open"),
            )

            db.add(alert)
            new_alerts_count += 1

        db.commit()
    finally:
        if created_session:
            db.close()

    return new_alerts_count