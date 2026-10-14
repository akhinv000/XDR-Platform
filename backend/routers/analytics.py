from fastapi import APIRouter
from sqlalchemy import text

from database import SessionLocal
from opensearch_client import client, is_opensearch_available

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/")
def analytics():

    db = SessionLocal()

    # Assets by OS (PostgreSQL)
    assets = db.execute(
        text("""
        SELECT operating_system,
               COUNT(*) AS total
        FROM assets
        GROUP BY operating_system
        """)
    ).mappings().all()

    # Risk Distribution (PostgreSQL)
    risk = db.execute(
        text("""
        SELECT
            CASE
                WHEN risk_score >= 70 THEN 'High'
                WHEN risk_score >= 30 THEN 'Medium'
                ELSE 'Low'
            END AS level,
            COUNT(*) AS total
        FROM assets
        GROUP BY level
        """)
    ).mappings().all()

    logs = []
    alerts = []

    if is_opensearch_available():
        try:
            # Read audit logs from OpenSearch
            response = client.search(
                index="security-auditlog-*",
                body={
                    "size": 1000,
                    "aggs": {
                        "sources": {
                            "terms": {
                                "field": "audit_request_origin.keyword"
                            }
                        }
                    }
                }
            )

            # Logs by Source
            logs = []

            for bucket in response["aggregations"]["sources"]["buckets"]:

                logs.append({
                    "source": bucket["key"],
                    "total": bucket["doc_count"]
                })

            # Alerts by Severity
            severity_count = {
                "High": 0,
                "Medium": 0,
                "Low": 0
            }

            for hit in response["hits"]["hits"]:

                category = hit["_source"].get("audit_category", "")

                if category in [
                    "FAILED_LOGIN",
                    "SSL_EXCEPTION"
                ]:
                    severity_count["High"] += 1

                elif category in [
                    "INDEX_EVENT",
                    "COMPLIANCE_INTERNAL_CONFIG_WRITE"
                ]:
                    severity_count["Medium"] += 1

                else:
                    severity_count["Low"] += 1

            alerts = []

            for severity, total in severity_count.items():

                if total > 0:

                    alerts.append({
                        "severity": severity,
                        "total": total
                    })

        except Exception:
            pass

    if not logs and not alerts:
        # Fallback to PostgreSQL
        logs_res = db.execute(
            text("""
            SELECT source, COUNT(*) AS total
            FROM logs
            GROUP BY source
            ORDER BY total DESC
            LIMIT 10
            """)
        ).mappings().all()

        logs = [{"source": r["source"], "total": r["total"]} for r in logs_res]

        alerts_res = db.execute(
            text("""
            SELECT severity, COUNT(*) AS total
            FROM alerts
            GROUP BY severity
            """)
        ).mappings().all()

        alerts = [{"severity": r["severity"], "total": r["total"]} for r in alerts_res]

    db.close()

    return {

        "assets_by_os": assets,

        "alerts_by_severity": alerts,

        "logs_by_source": logs,

        "risk_distribution": risk

    }