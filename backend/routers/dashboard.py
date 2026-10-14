from fastapi import APIRouter
from sqlalchemy import text

from database import SessionLocal
from opensearch_client import client, is_opensearch_available

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats")
def dashboard_stats():

    db = SessionLocal()

    try:
        # Assets remain in PostgreSQL
        total_assets = db.execute(
            text("SELECT COUNT(*) FROM assets")
        ).scalar() or 0

        # Read security events from OpenSearch if available
        if is_opensearch_available():
            try:
                response = client.search(
                    index="security-auditlog-*",
                    body={
                        "size": 1000
                    }
                )

                logs = response["hits"]["hits"]
                total_logs = len(logs)
                active_alerts = total_logs
                high_alerts = 0

                for hit in logs:
                    category = hit["_source"].get("audit_category", "")
                    if category in [
                        "FAILED_LOGIN",
                        "SSL_EXCEPTION"
                    ]:
                        high_alerts += 1

            except Exception:
                total_logs = db.execute(text("SELECT COUNT(*) FROM logs")).scalar() or 0
                active_alerts = db.execute(text("SELECT COUNT(*) FROM alerts WHERE status = 'Open'")).scalar() or 0
                high_alerts = db.execute(text("SELECT COUNT(*) FROM alerts WHERE severity = 'High'")).scalar() or 0
        else:
            total_logs = db.execute(text("SELECT COUNT(*) FROM logs")).scalar() or 0
            active_alerts = db.execute(text("SELECT COUNT(*) FROM alerts WHERE status = 'Open'")).scalar() or 0
            high_alerts = db.execute(text("SELECT COUNT(*) FROM alerts WHERE severity = 'High'")).scalar() or 0

        return {
            "total_assets": total_assets,
            "active_alerts": active_alerts,
            "high_alerts": high_alerts,
            "total_logs": total_logs
        }

    finally:
        db.close()