from datetime import datetime


def parse_auth_log(file_path):

    logs = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            level = "Low"
            source = "System"

            if "sshd" in line:
                source = "SSH"

            elif "sudo" in line:
                source = "SUDO"

            if "Failed password" in line:
                level = "High"

            elif "Accepted password" in line:
                level = "Low"

            elif "sudo" in line:
                level = "Medium"

            logs.append({

                "timestamp": datetime.utcnow(),

                "hostname": "Kali Linux",

                "level": level,

                "source": source,

                "message": line

            })

    return logs