# XDR BASE

An enterprise Extended Detection and Response (XDR) platform providing real-time security monitoring, automated MITRE ATT&CK threat correlation, active incident response & containment, network asset discovery, and endpoint telemetry streaming.

---

## Key Features

- **Centralized SOC Command Dashboard**: Real-time counter metrics for monitored endpoints, correlated attack incidents, active threats, quarantined hosts, and blocked IPs.
- **MITRE ATT&CK Threat Correlation**: Sliding-window burst correlation that aggregates multi-stage security events into actionable Incidents (e.g., `T1110` Brute Force, `T1548.003` Sudo Privilege Escalation, `T1190` Web Exploits, `T1059` Suspicious Processes).
- **Active Response & Containment ("The R in XDR")**:
  - **One-Click Host Quarantine**: Isolate compromised endpoints from lateral network movement using dynamic firewall rules while preserving SOC communication.
  - **Attacker IP Blocking**: Maintain a live perimeter blocklist that syncs with external firewalls (pfSense, Fortigate, Palo Alto) via plaintext feeds (`/response/blocklist.txt`).
  - **Incident Containment Playbook**: Instantly isolate target hosts and drop attacker IPs from the incident investigation drawer.
- **Universal System & Network Onboarding**:
  - **Linux 1-Line Installer**: Deploys systemd agent, tails auth logs, streams telemetry, and executes automated isolation commands.
  - **Windows 1-Line Installer**: PowerShell agent capturing Event IDs `4625`, `4624`, and `4688`, with Windows Firewall isolation.
  - **Network Syslog Ingestion**: HTTP syslog webhook endpoint (`POST /api/v1/agent/syslog`) compatible with routers, firewalls, and rsyslog daemons.
- **Asset Inventory & Discovery**: Network host discovery and vulnerability assessment via Nmap scans, storing operating systems, MAC addresses, open ports, and risk scores.
- **Hybrid Storage Architecture**: PostgreSQL persistence for assets, users, logs, alerts, incidents, and containment actions, with OpenSearch integration for high-volume log search.

---

## Tech Stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy, Uvicorn
- **Database**: PostgreSQL 17 (Dockerized)
- **Search & Analytics**: OpenSearch 2.19
- **Frontend**: Vanilla JavaScript, HTML5, Modern CSS (100% Sharp Greenlify Theme), Chart.js, Font Awesome

---

## Getting Started

### 1. Quickstart with Docker Compose

To spin up PostgreSQL, OpenSearch, and the XDR Backend in isolated containers:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

The API will be available at `http://127.0.0.1:9000` with interactive Swagger docs at `http://127.0.0.1:9000/docs`.

### 2. Manual Local Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux / macOS

pip install -r requirements.txt
```

Configure your environment variables by copying `.env.example`:
```bash
cp .env.example .env
```

Start the backend API server:
```bash
uvicorn app:app --host 127.0.0.1 --port 9000 --reload
```

### 3. Frontend Setup

Serve the `frontend/` directory with any static server or Python:

```bash
python -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500/login.html` in your browser.

- **Default Username**: `admin`
- **Default Password**: `admin123`

---

## Connecting Systems and Networks to XDR BASE

### Method 1: Connect a Linux Host (Ubuntu, Debian, RHEL, CentOS)

Run this one-liner on the target Linux system as `root` (replace `<XDR_SERVER_IP>` with your XDR backend host IP):

```bash
curl -sSL http://<XDR_SERVER_IP>:9000/api/v1/agent/install.sh | sudo bash
```

**What it does:**
1. Installs the lightweight agent to `/opt/xdr-agent/`.
2. Registers the host with XDR BASE and generates an API key.
3. Tails `/var/log/auth.log` or `/var/log/secure` and streams authentication events in real time.
4. Starts a persistent `systemd` service (`xdr-agent.service`) that checks in with heartbeats every 15 seconds.
5. Listens for SOC quarantine commands to apply local `iptables` isolation rules.

---

### Method 2: Connect a Windows Endpoint or Server

Open **PowerShell as Administrator** on the target Windows machine and run:

```powershell
irm http://<XDR_SERVER_IP>:9000/api/v1/agent/install.ps1 | iex
```

**What it does:**
1. Installs the PowerShell telemetry agent into `$env:ProgramData\XDR-Agent`.
2. Registers the machine and starts streaming Windows Security Log events (Event ID `4625` failed logons, Event ID `4688` process creation).
3. Connects to the XDR command bus for remote Windows Firewall containment.

---

### Method 3: Connect Network Routers, Firewalls & Switches (Syslog)

For network devices (pfSense, Fortigate, Cisco, OPNsense, or standard Linux rsyslog):

#### Option A: Forward Syslog via HTTP Webhook
Send log batches to:
```http
POST http://<XDR_SERVER_IP>:9000/api/v1/agent/syslog
Content-Type: application/json

{
  "hostname": "EDGE-ROUTER-01",
  "messages": [
    "Oct 16 19:30:00 EDGE-ROUTER-01 sshd[1234]: Failed password for root from 203.0.113.5",
    "Oct 16 19:30:02 EDGE-ROUTER-01 kernel: [UFW BLOCK] IN=eth0 SRC=203.0.113.5 DST=192.168.1.1 PROTO=TCP DPT=22"
  ]
}
```

#### Option B: Configure rsyslog on Servers
Add the following to `/etc/rsyslog.d/50-xdr.conf`:
```text
# Forward authentication logs to XDR BASE HTTP ingestion
*.* action(type="omhttp"
           server="<XDR_SERVER_IP>"
           port="9000"
           restpath="api/v1/agent/syslog"
           template="RSYSLOG_TraditionalFileFormat")
```

---

## API Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/login` | Authenticate and obtain JWT access token | No |
| `GET` | `/dashboard/stats` | Aggregated metrics (incidents, alerts, quarantined, blocklist) | Yes |
| `GET` | `/incidents/` | List correlated security incidents & campaigns | Yes |
| `GET` | `/incidents/{id}` | Detailed incident view with correlated attack timeline | Yes |
| `PUT` | `/incidents/{id}/status` | Transition incident status (`New`, `Investigating`, `Contained`, etc.) | Yes |
| `POST` | `/incidents/{id}/contain` | Instant automated containment (quarantine host + block IP) | Yes |
| `POST` | `/response/quarantine/{id}`| Isolate endpoint from network via firewall rules | Yes |
| `POST` | `/response/unquarantine/{id}` | Restore quarantined endpoint to online status | Yes |
| `POST` | `/response/block-ip` | Add malicious IP to perimeter blocklist | Yes |
| `GET` | `/response/blocklist.txt` | Plaintext blocklist feed for external firewalls | No |
| `POST` | `/api/v1/agent/register` | Register new system / endpoint | No |
| `POST` | `/api/v1/agent/heartbeat` | Agent heartbeat check-in & command polling | Optional Key |
| `POST` | `/api/v1/agent/telemetry` | Batch stream security events from remote hosts | Optional Key |
| `POST` | `/api/v1/agent/syslog` | Universal syslog ingestion from network equipment | No |
| `GET` | `/api/v1/agent/install.sh` | Dynamic Linux one-line installer script | No |
| `GET` | `/api/v1/agent/install.ps1` | Dynamic Windows PowerShell installer script | No |

---

## License

MIT License
