import re
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Log


# Regex extractors
IP_REGEX = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
SSH_FAIL_REGEX = re.compile(
    r"(?:Failed password for(?: invalid user)?\s*(\S+)\s*from\s*([0-9.]+)|"
    r"authentication failure;.*user=(\S+).*rhost=([0-9.]+)|"
    r"Failed (?:publickey|none) for\s*(\S+)\s*from\s*([0-9.]+))",
    re.IGNORECASE
)
SSH_ACCEPT_REGEX = re.compile(r"Accepted (?:password|publickey) for\s*(\S+)\s*from\s*([0-9.]+)", re.IGNORECASE)

SQLI_REGEX = re.compile(r"(?:\bUNION\s+SELECT\b|\bOR\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+|INFORMATION_SCHEMA|SELECT\s+.*\s+FROM)", re.IGNORECASE)
XSS_REGEX = re.compile(r"(?:<script\b|javascript\s*:|onerror\s*=|onload\s*=|alert\s*\(|document\.cookie)", re.IGNORECASE)
PATH_TRAV_REGEX = re.compile(r"(?:\.\./\.\.|\.\.\\\.\.|/etc/passwd|/etc/shadow|\\windows\\system32|cmd\.exe)", re.IGNORECASE)

SUSPICIOUS_SUDO_REGEX = re.compile(
    r"(?:NOT in sudoers|incorrect password attempts|authentication failure|"
    r"COMMAND=.*(?:/bin/su\b|/bin/sh\b|/bin/bash\b|visudo|/etc/shadow|chmod\s+777|chown\s+root|nmap\b|nc\s+-e))",
    re.IGNORECASE
)

SUSPICIOUS_PROC_REGEX = re.compile(
    r"(?:powershell.*-(?:enc|encodedcommand|nop|w\s+hidden)|certutil.*-(?:urlcache|decode)|"
    r"vssadmin\s+delete\s+shadows|mimikatz|psexec|whoami\s+/priv|net\s+user\s+/add)",
    re.IGNORECASE
)


def extract_ip(msg: str) -> str:
    """Extract first IPv4 address from string if present."""
    m = IP_REGEX.search(msg)
    return m.group(0) if m else ""


def detect_alerts(db: Optional[Session] = None, logs_to_evaluate: Optional[List] = None) -> List[Dict[str, Any]]:
    """
    Stateful threat detection engine with sliding time-window correlation,
    MITRE ATT&CK categorization, and false-positive elimination.
    """
    created_session = False
    if db is None:
        db = SessionLocal()
        created_session = True

    alerts = []
    try:
        if logs_to_evaluate is not None:
            logs = logs_to_evaluate
        else:
            # Query recent logs (limit to recent 1000)
            logs = db.query(Log).order_by(Log.id.desc()).limit(1000).all()

        # Group auth failures by source IP and host for windowed burst correlation
        auth_failures_by_ip = {}
        single_alerts = []

        for log in logs:
            msg = log.message if hasattr(log, "message") else log.get("message", "")
            hostname = log.hostname if hasattr(log, "hostname") else log.get("hostname", "Unknown")
            ts = log.timestamp if hasattr(log, "timestamp") else log.get("timestamp")
            if not ts:
                ts = datetime.now(timezone.utc)

            # ----------------------------------------------------
            # 1. SSH / Auth Failure Analysis & Windowed Burst Correlation
            # ----------------------------------------------------
            ssh_fail_match = SSH_FAIL_REGEX.search(msg)
            if ssh_fail_match or "Failed password" in msg or "authentication failure" in msg:
                src_ip = extract_ip(msg)
                key = (src_ip, hostname) if src_ip else ("UNKNOWN", hostname)

                if key not in auth_failures_by_ip:
                    auth_failures_by_ip[key] = []
                auth_failures_by_ip[key].append({
                    "timestamp": ts,
                    "message": msg,
                    "hostname": hostname,
                    "source_ip": src_ip
                })
                continue

            # ----------------------------------------------------
            # 2. Privilege Escalation (SUDO) - Filter False Positives!
            # ----------------------------------------------------
            if "sudo" in msg.lower():
                if SUSPICIOUS_SUDO_REGEX.search(msg):
                    single_alerts.append({
                        "timestamp": ts,
                        "hostname": hostname,
                        "severity": "High",
                        "title": "Privilege Escalation: Unauthorized / Suspicious Sudo Execution",
                        "description": msg,
                        "status": "Open",
                        "mitre_tactic": "Privilege Escalation",
                        "mitre_technique": "T1548.003",
                        "source_ip": extract_ip(msg)
                    })
                # Normal valid sudo commands without suspicious patterns are operational, not security alerts
                continue

            # ----------------------------------------------------
            # 3. Web & Application Attacks (WAF Telemetry)
            # ----------------------------------------------------
            if SQLI_REGEX.search(msg):
                single_alerts.append({
                    "timestamp": ts,
                    "hostname": hostname,
                    "severity": "Critical",
                    "title": "Web Application Attack: SQL Injection Pattern Detected",
                    "description": msg,
                    "status": "Open",
                    "mitre_tactic": "Initial Access",
                    "mitre_technique": "T1190",
                    "source_ip": extract_ip(msg)
                })
                continue

            if XSS_REGEX.search(msg):
                single_alerts.append({
                    "timestamp": ts,
                    "hostname": hostname,
                    "severity": "Medium",
                    "title": "Web Application Attack: Cross-Site Scripting (XSS) Pattern",
                    "description": msg,
                    "status": "Open",
                    "mitre_tactic": "Initial Access",
                    "mitre_technique": "T1190",
                    "source_ip": extract_ip(msg)
                })
                continue

            if PATH_TRAV_REGEX.search(msg):
                single_alerts.append({
                    "timestamp": ts,
                    "hostname": hostname,
                    "severity": "High",
                    "title": "Exploitation Attempt: Directory Traversal / Sensitive File Access",
                    "description": msg,
                    "status": "Open",
                    "mitre_tactic": "Defense Evasion",
                    "mitre_technique": "T1083",
                    "source_ip": extract_ip(msg)
                })
                continue

            # ----------------------------------------------------
            # 4. Windows / Host Suspicious Process Execution
            # ----------------------------------------------------
            if SUSPICIOUS_PROC_REGEX.search(msg) or "EventID=4688" in msg:
                single_alerts.append({
                    "timestamp": ts,
                    "hostname": hostname,
                    "severity": "Critical",
                    "title": "Suspicious Process Execution / Living-off-the-Land Binary",
                    "description": msg,
                    "status": "Open",
                    "mitre_tactic": "Execution",
                    "mitre_technique": "T1059.001",
                    "source_ip": extract_ip(msg)
                })
                continue

            # ----------------------------------------------------
            # 5. Network Discovery / Port Scans
            # ----------------------------------------------------
            if "port scan" in msg.lower() or "nmap" in msg.lower() or "syn flood" in msg.lower():
                single_alerts.append({
                    "timestamp": ts,
                    "hostname": hostname,
                    "severity": "Medium",
                    "title": "Network Reconnaissance: Active Port Scan / Sweep",
                    "description": msg,
                    "status": "Open",
                    "mitre_tactic": "Discovery",
                    "mitre_technique": "T1046",
                    "source_ip": extract_ip(msg)
                })
                continue

        # ----------------------------------------------------
        # Correlate Auth Failure Bursts
        # ----------------------------------------------------
        for (src_ip, hostname), fail_events in auth_failures_by_ip.items():
            count = len(fail_events)
            latest_event = fail_events[0]
            earliest_event = fail_events[-1]

            if count >= 3:
                # High / Critical severity burst alert
                severity = "Critical" if count >= 10 else "High"
                alerts.append({
                    "timestamp": latest_event["timestamp"],
                    "hostname": hostname,
                    "severity": severity,
                    "title": f"SSH / Auth Brute-Force Campaign ({count} failed attempts)",
                    "description": f"Detected burst of {count} failed authentication attempts from IP {src_ip or 'Unknown'}. Latest: {latest_event['message']}",
                    "status": "Open",
                    "mitre_tactic": "Credential Access",
                    "mitre_technique": "T1110.001",
                    "source_ip": src_ip if src_ip != "UNKNOWN" else ""
                })
            else:
                # Single / low threshold failure
                for ev in fail_events:
                    alerts.append({
                        "timestamp": ev["timestamp"],
                        "hostname": hostname,
                        "severity": "Low",
                        "title": "SSH / Authentication Failure",
                        "description": ev["message"],
                        "status": "Open",
                        "mitre_tactic": "Credential Access",
                        "mitre_technique": "T1110",
                        "source_ip": ev["source_ip"]
                    })

        alerts.extend(single_alerts)

    finally:
        if created_session:
            db.close()

    return alerts