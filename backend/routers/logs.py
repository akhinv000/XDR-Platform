from fastapi import APIRouter
from opensearch_client import client, is_opensearch_available

router = APIRouter(
    prefix="/logs",
    tags=["Security Logs"]
)


@router.get("/")
def get_logs():

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

            logs = []

            for hit in response["hits"]["hits"]:

                source = hit["_source"]

                logs.append({

                    "id": hit["_id"],

                    "timestamp": source.get("@timestamp", ""),

                    "hostname": source.get("audit_node_name", ""),

                    "level": (
                        "High"
                        if source.get("audit_category") in [
                            "FAILED_LOGIN",
                            "SSL_EXCEPTION"
                        ]
                        else "Medium"
                        if source.get("audit_category") in [
                            "INDEX_EVENT",
                            "COMPLIANCE_INTERNAL_CONFIG_WRITE"
                        ]
                        else "Low"
                    ),

                    "category": source.get("audit_category", ""),

                    "source": source.get("audit_request_origin", ""),

                    "message": (
                        f"{source.get('audit_rest_request_method', '')} "
                        f"{source.get('audit_rest_request_path', '')} "
                        f"by {source.get('audit_request_effective_user', 'Unknown')}"
                    ).strip()

                })

            return logs

        except Exception:
            pass

    from database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db_logs = db.execute(
            text("SELECT id, timestamp, hostname, level, source, message FROM logs ORDER BY id DESC LIMIT 100")
        ).mappings().all()

        return [
            {
                "id": str(r["id"]),
                "timestamp": r["timestamp"].isoformat() if r["timestamp"] else "",
                "hostname": r["hostname"] or "",
                "level": r["level"] or "Low",
                "category": "AUTH",
                "source": r["source"] or "",
                "message": r["message"] or ""
            }
            for r in db_logs
        ]
    finally:
        db.close()