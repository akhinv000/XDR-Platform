import re
from datetime import datetime, timezone
from pathlib import Path


def parse_timestamp(token: str) -> datetime:
    """Attempt to parse ISO 8601 or syslog format timestamp."""
    try:
        # ISO 8601 format: 2026-06-30T00:01:39.109658+05:30
        return datetime.fromisoformat(token)
    except Exception:
        pass

    try:
        # Standard syslog format: Jun 30 00:01:39
        current_year = datetime.now().year
        dt = datetime.strptime(token, "%b %d %H:%M:%S")
        return dt.replace(year=current_year)
    except Exception:
        return datetime.now(timezone.utc)


def parse_auth_log(file_path=None):
    """
    Parses an auth.log file into structured log events with accurate timestamps,
    hostnames, and threat levels.
    """
    if file_path is None:
        file_path = Path(__file__).parent / "auth.log"
    else:
        file_path = Path(file_path)

    if not file_path.is_absolute() and not file_path.exists():
        fallback = Path(__file__).parent / file_path.name
        if fallback.exists():
            file_path = fallback

    logs = []
    if not file_path.exists():
        return logs

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            raw_line = line.strip()
            if not raw_line:
                continue

            parts = raw_line.split()
            if len(parts) < 3:
                continue

            # Check if line starts with ISO timestamp
            if "T" in parts[0] and ("+" in parts[0] or "-" in parts[0] or "Z" in parts[0]):
                ts = parse_timestamp(parts[0])
                hostname = parts[1]
                content = " ".join(parts[2:])
            elif len(parts) >= 4 and parts[0] in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
                ts = parse_timestamp(" ".join(parts[0:3]))
                hostname = parts[3]
                content = " ".join(parts[4:])
            else:
                ts = datetime.now(timezone.utc)
                hostname = "System"
                content = raw_line

            # Determine source category
            source = "System"
            if "sshd" in content:
                source = "SSH"
            elif "sudo" in content:
                source = "SUDO"
            elif "pam" in content:
                source = "PAM"

            # Determine threat level
            level = "Low"
            if "Failed password" in content or "authentication failure" in content or "password check failed" in content:
                level = "High"
            elif "sudo" in content or "COMMAND=" in content:
                level = "Medium"
            elif "Accepted password" in content:
                level = "Low"

            logs.append({
                "timestamp": ts,
                "hostname": hostname,
                "level": level,
                "source": source,
                "message": raw_line
            })

    return logs