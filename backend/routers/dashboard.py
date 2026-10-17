from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Asset, Alert, Log, User, Incident, BlockedIP, AgentEndpoint
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
    high_alerts = db.query(Alert).filter(Alert.severity.in_(["Critical", "High"]), Alert.status == "Open").count()
    total_logs = db.query(Log).count()
    active_incidents = db.query(Incident).filter(Incident.status.in_(["New", "Investigating"])).count()
    quarantined_assets = db.query(Asset).filter(Asset.status == "Quarantined").count()
    blocked_ips_count = db.query(BlockedIP).filter(BlockedIP.status == "Active").count()
    connected_agents = db.query(AgentEndpoint).filter(AgentEndpoint.status != "Offline").count()

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
        "total_logs": total_logs,
        "active_incidents": active_incidents,
        "quarantined_assets": quarantined_assets,
        "blocked_ips_count": blocked_ips_count,
        "connected_agents": connected_agents
    }