from database import SessionLocal
from models import Alert


def update_alerts(alerts):

    db = SessionLocal()

    try:

        for item in alerts:

            existing = (
                db.query(Alert)
                .filter(
                    Alert.timestamp == item["timestamp"],
                    Alert.title == item["title"],
                    Alert.description == item["description"]
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

                status="Open"

            )

            db.add(alert)

        db.commit()

    finally:

        db.close()