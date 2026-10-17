from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Alert, Incident


SEVERITY_WEIGHT = {
    "Critical": 4,
    "High": 3,
    "Medium": 2,
    "Low": 1
}


def update_alerts(alerts: List[Dict[str, Any]], db: Optional[Session] = None) -> int:
    """
    Persists detected alerts into the database and automatically aggregates
    correlated alerts into actionable Incidents.
    """
    created_session = False
    if db is None:
        db = SessionLocal()
        created_session = True

    new_alerts_count = 0
    now = datetime.now(timezone.utc)
    try:
        for item in alerts:
            # Check for existing alert deduplication
            existing = (
                db.query(Alert)
                .filter(
                    Alert.hostname == item["hostname"],
                    Alert.title == item["title"],
                    Alert.description == item["description"],
                )
                .first()
            )

            if existing:
                continue

            # --------------------------------------------------------
            # Automatic Incident Aggregation
            # Look for active incidents for this host or source IP in the last 2 hours
            # --------------------------------------------------------
            source_ip = item.get("source_ip", "")
            hostname = item.get("hostname", "Unknown")
            severity = item.get("severity", "Low")
            mitre_tactic = item.get("mitre_tactic", "Unknown")
            mitre_technique = item.get("mitre_technique", "Unknown")

            time_cutoff = now - timedelta(hours=2)
            active_incident = (
                db.query(Incident)
                .filter(
                    Incident.status.in_(["New", "Investigating"]),
                    Incident.updated_at >= time_cutoff,
                    (Incident.hostname == hostname) | (Incident.source_ip == source_ip if source_ip else False)
                )
                .order_by(Incident.id.desc())
                .first()
            )

            if active_incident:
                # Correlate alert with existing incident
                active_incident.alert_count += 1
                active_incident.updated_at = now
                if SEVERITY_WEIGHT.get(severity, 1) > SEVERITY_WEIGHT.get(active_incident.severity, 1):
                    active_incident.severity = severity
                incident_id = active_incident.id
            else:
                # Create a new Incident
                incident_title = f"{item['title']} on {hostname}"
                if source_ip:
                    incident_title += f" [from {source_ip}]"

                new_incident = Incident(
                    title=incident_title,
                    severity=severity,
                    status="New",
                    mitre_tactic=mitre_tactic,
                    mitre_technique=mitre_technique,
                    hostname=hostname,
                    source_ip=source_ip,
                    alert_count=1,
                    analyst_notes="",
                    assigned_to="SOC Operator",
                    created_at=now,
                    updated_at=now
                )
                db.add(new_incident)
                db.flush()  # Generate ID for foreign reference
                incident_id = new_incident.id

            alert = Alert(
                timestamp=item.get("timestamp", now),
                hostname=hostname,
                severity=severity,
                title=item["title"],
                description=item["description"],
                status=item.get("status", "Open"),
                mitre_tactic=mitre_tactic,
                mitre_technique=mitre_technique,
                source_ip=source_ip,
                incident_id=incident_id
            )

            db.add(alert)
            new_alerts_count += 1

            # Trigger SOAR Automated Playbooks
            try:
                from routers.playbooks import run_soar_playbook
                target_incident = active_incident if active_incident else new_incident
                run_soar_playbook(item, target_incident, db)
            except Exception:
                pass

        db.commit()
    finally:
        if created_session:
            db.close()

    return new_alerts_count