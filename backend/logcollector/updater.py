from database import SessionLocal
from models import Log


def update_logs(logs):

    db = SessionLocal()

    try:

        for item in logs:

            existing = (
                db.query(Log)
                .filter(
                    Log.hostname == item["hostname"],
                    Log.source == item["source"],
                    Log.message == item["message"]
                )
                .first()
            )

            if existing:
                continue

            log = Log(

                timestamp=item["timestamp"],

                hostname=item["hostname"],

                level=item["level"],

                source=item["source"],

                message=item["message"]

            )

            db.add(log)

        db.commit()

    finally:

        db.close()