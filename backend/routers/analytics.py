from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth_utils import get_current_user
from opensearch_client import client, is_opensearch_available

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/")
def analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provide aggregated security distributions for SOC visualizations."""
    # Assets grouped by OS
    assets_raw = db.execute(
        text("""
        SELECT COALESCE(operating_system, 'Unknown') AS operating_system,
               COUNT(*) AS total
        FROM assets
        GROUP BY operating_system
        """)
    ).mappings().all()

    # Risk distribution based on port risk score
    risk_raw = db.execute(
        text("""
        SELECT
            CASE
                WHEN risk_score >= 60 THEN 'High'
                WHEN risk_score >= 25 THEN 'Medium'
                ELSE 'Low'
            END AS level,
            COUNT(*) AS total
        FROM assets
        GROUP BY level
        """)
    ).mappings().all()

    logs = []
    alerts = []

    # Attempt OpenSearch for high-volume logs
    if is_opensearch_available():
        try:
            response = client.search(
                index="security-auditlog-*",
                body={
                    "size": 0,
                    "aggs": {
                        "sources": {
                            "terms": {"field": "audit_request_origin.keyword"}
                        }
                    }
                }
            )
            buckets = response.get("aggregations", {}).get("sources", {}).get("buckets", [])
            for bucket in buckets:
                logs.append({
                    "source": bucket["key"],
                    "total": bucket["doc_count"]
                })
        except Exception:
            pass

    # Fallback to PostgreSQL logs & alerts
    if not logs:
        logs_res = db.execute(
            text("""
            SELECT COALESCE(source, 'System') AS source, COUNT(*) AS total
            FROM logs
            GROUP BY source
            ORDER BY total DESC
            LIMIT 10
            """)
        ).mappings().all()
        logs = [{"source": r["source"], "total": r["total"]} for r in logs_res]

    alerts_res = db.execute(
        text("""
        SELECT COALESCE(severity, 'Low') AS severity, COUNT(*) AS total
        FROM alerts
        GROUP BY severity
        """)
    ).mappings().all()
    alerts = [{"severity": r["severity"], "total": r["total"]} for r in alerts_res]

    return {
        "assets_by_os": [{"operating_system": r["operating_system"], "total": r["total"]} for r in assets_raw],
        "alerts_by_severity": alerts,
        "logs_by_source": logs,
        "risk_distribution": [{"level": r["level"], "total": r["total"]} for r in risk_raw]
    }