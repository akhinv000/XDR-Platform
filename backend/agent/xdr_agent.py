#!/usr/bin/env python3
"""
XDR BASE - Lightweight Cross-Platform Endpoint Agent
Requires Python 3.6+ standard library only (zero third-party dependencies).
Supports Linux & Windows endpoints.
"""

import os
import sys
import time
import json
import socket
import platform
import subprocess
import urllib.request
import urllib.error
from pathlib import Path


CONFIG_FILE = Path(__file__).parent / "config.json"
TOKEN_FILE = Path(__file__).parent / "agent_token.json"


def get_local_ip():
    """Retrieve primary outbound IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class XDRAgent:
    def __init__(self):
        self.server_url = "http://127.0.0.1:9000"
        self.heartbeat_interval = 15
        self.agent_id = None
        self.api_key = None
        self.load_config()
        self.load_or_register()

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    cfg = json.load(f)
                    self.server_url = cfg.get("server_url", self.server_url).rstrip("/")
                    self.heartbeat_interval = int(cfg.get("heartbeat_interval", 15))
            except Exception as e:
                print(f"[!] Warning reading config: {e}")

    def http_post(self, path, payload, headers=None):
        url = f"{self.server_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("X-Agent-Key", self.api_key)
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def load_or_register(self):
        if TOKEN_FILE.exists():
            try:
                with open(TOKEN_FILE, "r") as f:
                    data = json.load(f)
                    self.agent_id = data.get("agent_id")
                    self.api_key = data.get("api_key")
                    print(f"[*] Loaded registered agent ID: {self.agent_id}")
                    return
            except Exception:
                pass

        # Register with server
        hostname = socket.gethostname()
        ip = get_local_ip()
        os_name = platform.system()
        os_ver = platform.version()

        payload = {
            "hostname": hostname,
            "ip_address": ip,
            "operating_system": os_name,
            "os_version": os_ver,
            "mac_address": ""
        }

        print(f"[*] Registering endpoint '{hostname}' ({ip}) with XDR Server at {self.server_url}...")
        try:
            resp = self.http_post("/api/v1/agent/register", payload)
            self.agent_id = resp["agent_id"]
            self.api_key = resp["api_key"]
            with open(TOKEN_FILE, "w") as f:
                json.dump({"agent_id": self.agent_id, "api_key": self.api_key}, f)
            print(f"[+] Successfully onboarded! Agent ID: {self.agent_id}")
        except Exception as e:
            print(f"[-] Registration failed: {e}")
            sys.exit(1)

    def execute_quarantine(self):
        print("[!] EXECUTING HOST QUARANTINE: Isolating endpoint from network...")
        if platform.system() == "Linux":
            try:
                # Isolate host with iptables: preserve only connection to server
                server_host = self.server_url.split("//")[-1].split(":")[0]
                subprocess.run(["iptables", "-F"], check=False)
                subprocess.run(["iptables", "-P", "INPUT", "DROP"], check=False)
                subprocess.run(["iptables", "-P", "OUTPUT", "DROP"], check=False)
                subprocess.run(["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "9000", "-j", "ACCEPT"], check=False)
                subprocess.run(["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "9000", "-j", "ACCEPT"], check=False)
                subprocess.run(["iptables", "-A", "INPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=False)
                subprocess.run(["iptables", "-A", "OUTPUT", "-m", "conntrack", "--ctstate", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=False)
                print("[+] Linux iptables isolation applied.")
            except Exception as e:
                print(f"[-] Failed to apply Linux iptables: {e}")
        elif platform.system() == "Windows":
            try:
                subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', 'name="XDR_ISOLATE_ALL"', 'dir=in', 'action=block'], check=False)
                print("[+] Windows Firewall isolation rule applied.")
            except Exception as e:
                print(f"[-] Failed to apply Windows Firewall: {e}")

    def execute_unquarantine(self):
        print("[*] Releasing endpoint from quarantine...")
        if platform.system() == "Linux":
            try:
                subprocess.run(["iptables", "-P", "INPUT", "ACCEPT"], check=False)
                subprocess.run(["iptables", "-P", "OUTPUT", "ACCEPT"], check=False)
                subprocess.run(["iptables", "-F"], check=False)
                print("[+] Network connectivity restored.")
            except Exception as e:
                print(f"[-] Error: {e}")
        elif platform.system() == "Windows":
            try:
                subprocess.run(['netsh', 'advfirewall', 'firewall', 'delete', 'rule', 'name="XDR_ISOLATE_ALL"'], check=False)
                print("[+] Windows isolation rule removed.")
            except Exception as e:
                print(f"[-] Error: {e}")

    def execute_block_ip(self, ip):
        print(f"[!] Applying firewall block for IP: {ip}")
        if platform.system() == "Linux":
            try:
                subprocess.run(["iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"], check=False)
            except Exception as e:
                print(f"[-] Error: {e}")
        elif platform.system() == "Windows":
            try:
                subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', f'name="XDR_BLOCK_{ip}"', 'dir=in', 'action=block', f'remoteip={ip}'], check=False)
            except Exception as e:
                print(f"[-] Error: {e}")

    def send_heartbeat(self):
        payload = {
            "agent_id": self.agent_id,
            "cpu_percent": 0.0,
            "memory_percent": 0.0,
            "disk_percent": 0.0,
            "active_connections": 0
        }
        try:
            resp = self.http_post("/api/v1/agent/heartbeat", payload)
            status = resp.get("status")
            commands = resp.get("commands", [])

            for cmd in commands:
                act = cmd.get("action")
                if act == "quarantine":
                    self.execute_quarantine()
                elif act == "unquarantine":
                    self.execute_unquarantine()
                elif act == "block_ip":
                    ip = cmd.get("ip")
                    if ip:
                        self.execute_block_ip(ip)

        except Exception as e:
            print(f"[!] Heartbeat warning: {e}")

    def tail_and_stream_logs(self):
        """Tail local authentication logs and stream events to XDR server."""
        log_paths = [
            Path("/var/log/auth.log"),
            Path("/var/log/secure"),
            Path("/var/log/syslog")
        ]
        target_log = None
        for p in log_paths:
            if p.exists():
                target_log = p
                break

        if not target_log:
            return

        try:
            with open(target_log, "r", errors="ignore") as f:
                f.seek(0, os.SEEK_END)
                while True:
                    line = f.readline()
                    if line:
                        line = line.strip()
                        if line:
                            self.http_post("/api/v1/agent/telemetry", {
                                "agent_id": self.agent_id,
                                "events": [{"message": line, "source": "SyslogTail"}]
                            })
                    else:
                        time.sleep(1)
        except Exception as e:
            print(f"[!] Log tail warning: {e}")

    def run(self):
        print(f"[+] XDR Agent running. Reporting to {self.server_url} every {self.heartbeat_interval}s...")
        while True:
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)


if __name__ == "__main__":
    agent = XDRAgent()
    agent.run()
