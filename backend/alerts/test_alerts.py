from alerts.detector import detect_alerts
from alerts.updater import update_alerts

alerts = detect_alerts()

update_alerts(alerts)

print(f"{len(alerts)} alerts generated.")