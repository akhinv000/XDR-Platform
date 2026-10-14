from database import SessionLocal
from models import Log


def detect_alerts():

    db = SessionLocal()

    alerts = []

    logs = db.query(Log).all()

    for log in logs:

        if "Failed password" in log.message:

            alerts.append({

                "timestamp": log.timestamp,

                "hostname": log.hostname,

                "severity": "High",

                "title": "SSH Failed Login",

                "description": log.message

            })

        elif "sudo" in log.message:

            alerts.append({

                "timestamp": log.timestamp,

                "hostname": log.hostname,

                "severity": "Medium",

                "title": "Privilege Escalation",

                "description": log.message

            })

        elif "Accepted password" in log.message:

            alerts.append({

                "timestamp": log.timestamp,

                "hostname": log.hostname,

                "severity": "Low",

                "title": "Successful Login",

                "description": log.message

            })

    db.close()

    return alerts