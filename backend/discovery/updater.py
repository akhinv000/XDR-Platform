from datetime import datetime

from database import SessionLocal
from models import Asset


def calculate_risk(ports):

    score = 0

    ports = set(ports)

    # Critical services
    if "23" in ports:      # Telnet
        score += 40

    if "3389" in ports:    # RDP
        score += 35

    if "445" in ports:     # SMB
        score += 25

    # Medium-risk services
    if "21" in ports:      # FTP
        score += 15

    if "135" in ports:     # RPC
        score += 10

    if "139" in ports:     # NetBIOS
        score += 10

    if "22" in ports:      # SSH
        score += 5

    # Common web services (low risk by themselves)
    if "80" in ports:
        score += 2

    if "443" in ports:
        score += 1

    # Large attack surface
    if len(ports) >= 15:
        score += 10

    elif len(ports) >= 10:
        score += 5

    return min(score, 100)


def detect_asset_type(os_name):

    if "Windows" in os_name:
        return "Windows Endpoint"

    elif "Linux" in os_name:
        return "Linux Server"

    elif "Elasticsearch" in os_name:
        return "Search Server"

    else:
        return "Unknown"


def update_assets(assets):

    db = SessionLocal()

    try:

        for item in assets:

            existing = (
                db.query(Asset)
                .filter(Asset.ip_address == item["ip"])
                .first()
            )

            ports = ",".join(item["ports"])

            services = ", ".join(item["services"])

            risk = calculate_risk(item["ports"])

            asset_type = detect_asset_type(item["os"])

            if existing:

                existing.hostname = item["hostname"]
                existing.mac_address = item.get("mac", "")
                existing.vendor = item.get("vendor", "")
                existing.operating_system = item["os"]
                existing.os_guess = item["os"]
                existing.asset_type = asset_type
                existing.status = "Online"
                existing.open_ports = ports
                existing.services = services
                existing.risk_score = risk
                existing.last_seen = datetime.utcnow()

            else:

                asset = Asset(

                    hostname=item["hostname"],

                    ip_address=item["ip"],

                    mac_address=item.get("mac", ""),

                    vendor=item.get("vendor", ""),

                    operating_system=item["os"],

                    os_guess=item["os"],

                    asset_type=asset_type,

                    status="Online",

                    open_ports=ports,

                    services=services,

                    risk_score=risk,

                    first_seen=datetime.utcnow(),

                    last_seen=datetime.utcnow()

                )

                db.add(asset)

        db.commit()

    finally:

        db.close()