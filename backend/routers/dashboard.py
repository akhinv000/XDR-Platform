from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Asset, Alert, Log, User
from auth_utils import get_current_user
from opensearch_client import client, is_opensearch_available

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregate core security metrics for the main SOC dashboard."""
    total_assets = db.query(Asset).count()
    active_alerts = db.query(Alert).filter(Alert.status == "Open").count()
    high_alerts = db.query(Alert).filter(Alert.severity == "High", Alert.status == "Open").count()
    total_logs = db.query(Log).count()

    # Incorporate OpenSearch security logs if running
    if is_opensearch_available():
        try:
            response = client.count(index="security-auditlog-*")
            os_logs_count = response.get("count", 0)
            if os_logs_count > 0:
                total_logs += os_logs_count
        except Exception:
            pass

    return {
        "total_assets": total_assets,
        "active_alerts": active_alerts,
        "high_alerts": high_alerts,
        "total_logs": total_logs
    }