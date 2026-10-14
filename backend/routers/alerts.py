from fastapi import APIRouter
from opensearch_client import client, is_opensearch_available

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.get("/")
def get_alerts():

    if is_opensearch_available():
        try:
            response = client.search(
                index="security-auditlog-*",
                body={
                    "size": 100,
                    "sort": [
                        {
                            "@timestamp": {
                                "order": "desc"
                            }
                        }
                    ]
                }
            )

            alerts = []

            for hit in response["hits"]["hits"]:

                source = hit["_source"]

                category = source.get("audit_category", "")

                if category in ["FAILED_LOGIN", "SSL_EXCEPTION"]:
                    severity = "High"
                elif category in ["INDEX_EVENT", "COMPLIANCE_INTERNAL_CONFIG_WRITE"]:
                    severity = "Medium"
                else:
                    severity = "Low"

                alerts.append({

                    "id": hit["_id"],

                    "timestamp": source.get("@timestamp", ""),

                    "hostname": source.get("audit_node_name", ""),

                    "severity": severity,

                    "title": category.replace("_", " ").title(),

                    "description": (
                        f"{source.get('audit_rest_request_method', '')} "
                        f"{source.get('audit_rest_request_path', '')} "
                        f"by {source.get('audit_request_effective_user', 'Unknown')}"
                    ).strip(),

                    "status": "Open"

                })

            return alerts

        except Exception:
            pass

    from database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db_alerts = db.execute(
            text("SELECT id, timestamp, hostname, severity, title, description, status FROM alerts ORDER BY id DESC LIMIT 100")
        ).mappings().all()

        return [
            {
                "id": str(r["id"]),
                "timestamp": r["timestamp"].isoformat() if r["timestamp"] else "",
                "hostname": r["hostname"] or "",
                "severity": r["severity"] or "Low",
                "title": r["title"] or "",
                "description": r["description"] or "",
                "status": r["status"] or "Open"
            }
            for r in db_alerts
        ]
    finally:
        db.close()


@router.put("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str):

    return {
        "message": "Alert acknowledged (demo mode)"
    }