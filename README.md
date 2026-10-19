# XDR ShieldX

An enterprise-grade Extended Detection and Response (XDR) & Security Operations Center (SOC) platform engineered for real-time telemetry streaming, automated MITRE ATT&CK correlation, autonomous SOAR playbooks, interactive attack storyline causality trees, and instant active containment.

---

## Architecture & Visual Philosophy

- **True OLED Pure Black Canvas**: 100% Flat `#000000` surface eliminating backlight glow, optimized for 24/7 SOC mission controllers.
- **Royal Violet & Electric Lavender Accents**: Razor-thin violet hairlines (`rgba(139, 92, 246, 0.22)`) define structure without visual clutter, with lavender glows for live telemetry alerts.
- **Tactical Edgy Corners**: Sharp `2px - 4px` box radius design delivering a crisp, high-density cyber defense cockpit.
- **Fixed SOC Navigation Dock**: Bottom-pinned crimson session termination and isolated view controllers ensuring uninterrupted telemetry visibility.

---

## Key Capabilities

### 1. Centralized SOC Command Center & DEFCON Matrix
- Real-time KPI velocity counters tracking Monitored Endpoints, MTTD (Mean Time to Detect), Active Alerts, Contained Threats, and Ingested Event Volume.
- Dynamic DEFCON threat escalation banner updating in real-time based on high/critical alert thresholds.
- Live 24-hour Threat Velocity chart correlating event ingestion volume against detected attack spikes.

### 2. Autonomous SOAR Playbook Engine
- Rule-to-action automation engine orchestrating instant remediation without analyst fatigue:
  - **Auth Brute-Force Blackhole**: Auto-bans repeat attacker IPs upon detection of `T1110` credential-stuffing campaigns.
  - **Ransomware / Malicious Execution Quarantine**: Automatically isolates compromised endpoints via local firewall rules upon detection of `T1059` command execution.
  - **Suspicious Process Termination**: Executes remote process kill orders directly on the host agent.
  - **Perimeter Firewall Synchronization**: Streams active blocklists to upstream routers and firewalls.

### 3. Visual Attack Storyline & Process Causality Tree
- Graph-based forensic investigation pane reconstructing parent-child process execution (`cmd.exe` &rarr; `powershell.exe` &rarr; `mimikatz.exe`).
- Node-by-node inspector detailing Process ID (PID), command-line arguments, user context, SHA-256 binary hash, and MITRE tactic mapping.
- **Live Process Kill Action**: Remote execution directive sent through the agent command bus to terminate malicious processes in real-time.

### 4. Threat Intelligence & Multi-Source IOC Enrichment
- Automated on-the-fly reputation scoring for malicious IPv4 addresses, domains, and file hashes.
- Aggregated threat feeds calculating composite risk scores (`0 - 100`) with ASN attribution, geographic origin, and known botnet/C2 flags.

### 5. Active Response & Network Containment ("The R in XDR")
- **One-Click Host Quarantine**: Isolates compromised systems by enforcing strict local firewall rules (`iptables` / Windows Defender Firewall) while maintaining communication with the SOC controller.
- **Perimeter IP Blocklist Feed**: Generates dynamic plaintext firewall blocklists (`GET /response/blocklist.txt`) compatible with pfSense, Fortigate, Palo Alto, and Cisco ASA.
- **Attacker Blackholing**: Instant manual or automated perimeter drops.

### 6. Universal Agent Onboarding & Ingestion
- **Linux 1-Line Installer**: Deploys lightweight systemd service streaming authentication logs (`/var/log/auth.log` or `/var/log/secure`) and executing isolation commands.
- **Windows 1-Line Installer**: PowerShell telemetry collector tracking Windows Security Log Event IDs `4624` (Logon), `4625` (Failed Logon), and `4688` (Process Creation).
- **Network Equipment Syslog**: HTTP syslog webhook endpoint (`POST /api/v1/agent/syslog`) supporting Cisco, Ubiquiti, pfSense, and rsyslog daemons.

### 7. Executive Incident Dossier & Forensic Reporting
- Instant generation of printable, executive-ready incident reports containing executive summaries, affected assets, MITRE ATT&CK breakdowns, and full remediation timelines.

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend Engine** | Python 3.13, FastAPI, SQLAlchemy ORM, Uvicorn (ASGI) |
| **Relational Storage** | PostgreSQL 17 (Dockerized) |
| **Search & Event Blackbox** | OpenSearch 2.19 |
| **SOC Console Frontend** | Pure Vanilla JavaScript (ES6+), Modern Semantic HTML5, CSS3 Variables, Chart.js, Font Awesome 6 Pro |
| **Telemetry Agents** | Linux Bash daemon (`systemd`), Windows PowerShell Agent (`NetFirewall` & Event Log) |

---

## Getting Started

### 1. Docker Compose (Recommended)

To spin up PostgreSQL, OpenSearch, and the XDR backend services:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

The REST API will be accessible at `http://127.0.0.1:9000` with interactive Swagger docs at `http://127.0.0.1:9000/docs`.

### 2. Manual Local Setup

```bash
# Clone the repository
git clone https://github.com/akhinv000/XDR-Platform.git
cd XDR-Platform/backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Launch the FastAPI backend server
uvicorn app:app --host 127.0.0.1 --port 9000 --reload
```

### 3. Frontend Dashboard Setup

Serve the `frontend/` directory with Python or any HTTP server:

```bash
python -m http.server 5500 --directory frontend
```

Navigate to `http://127.0.0.1:5500/login.html` in your browser.

- **Default Username**: `admin`
- **Default Password**: `admin123`

---

## Endpoint & Network Device Onboarding

### Linux Endpoints (Ubuntu, Debian, RHEL, CentOS)
Run as `root` on the target machine (replace `<XDR_SERVER_IP>` with your backend IP):

```bash
curl -sSL http://<XDR_SERVER_IP>:9000/api/v1/agent/install.sh | sudo bash
```

### Windows Endpoints & Servers
Run in an elevated **PowerShell as Administrator**:

```powershell
irm http://<XDR_SERVER_IP>:9000/api/v1/agent/install.ps1 | iex
```

### Network Routers, Firewalls & Syslog Forwarders
Configure your router/firewall to POST JSON syslog payloads or forward via `rsyslog`:

```http
POST http://<XDR_SERVER_IP>:9000/api/v1/agent/syslog
Content-Type: application/json

{
  "hostname": "EDGE-FIREWALL-01",
  "messages": [
    "Oct 19 22:30:00 EDGE-FIREWALL-01 sshd[4012]: Failed password for root from 198.51.100.24",
    "Oct 19 22:30:04 EDGE-FIREWALL-01 kernel: [UFW DROP] IN=eth0 SRC=198.51.100.24 PROTO=TCP DPT=22"
  ]
}
```

---

## API Reference Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/login` | Authenticate operator and issue JWT session token | No |
| `GET` | `/dashboard/stats` | Aggregated SOC operational statistics and KPI counters | Yes |
| `GET` | `/incidents/` | Retrieve correlated attack campaigns and incidents | Yes |
| `GET` | `/incidents/{id}` | Detailed forensic incident breakdown and attack timeline | Yes |
| `PUT` | `/incidents/{id}/status` | Update incident status (`New`, `Investigating`, `Contained`, `Closed`) | Yes |
| `POST` | `/incidents/{id}/contain` | Instant host isolation and attacker IP block | Yes |
| `POST` | `/response/quarantine/{id}` | Enforce network quarantine on target endpoint | Yes |
| `POST` | `/response/unquarantine/{id}`| Lift network isolation and restore normal connectivity | Yes |
| `POST` | `/response/block-ip` | Add malicious IP to perimeter containment blocklist | Yes |
| `GET` | `/response/blocklist.txt` | Live plaintext blocklist feed for pfSense / Fortigate / Palo Alto | No |
| `GET` | `/storyline/{incident_id}` | Generate process tree causality graph for incident forensics | Yes |
| `POST` | `/storyline/kill-process` | Queue remote process termination directive to endpoint agent | Yes |
| `GET` | `/threat-intel/enrich` | Multi-source reputation scoring for IPs and hashes | Yes |
| `GET` | `/playbooks/` | List autonomous SOAR playbooks and automation rules | Yes |
| `POST` | `/playbooks/toggle` | Enable or disable automated playbook execution | Yes |
| `POST` | `/playbooks/execute` | Manually trigger a SOAR playbook against an incident | Yes |
| `GET` | `/analytics/mitre-matrix` | Heatmap data of MITRE ATT&CK tactics and techniques | Yes |
| `GET` | `/analytics/threat-velocity` | 24-hour ingestion vs. threat detection telemetry velocity | Yes |
| `GET` | `/analytics/executive-report`| Generate executive incident dossier summary | Yes |
| `POST` | `/api/v1/agent/register` | Register new endpoint and issue API credentials | No |
| `POST` | `/api/v1/agent/heartbeat` | Agent heartbeat check-in & command bus polling | Optional Key |
| `POST` | `/api/v1/agent/telemetry` | Batch stream security events from remote endpoints | Optional Key |
| `POST` | `/api/v1/agent/syslog` | Universal syslog ingestion from network equipment | No |
| `GET` | `/api/v1/agent/install.sh` | Linux single-line installer bootstrap | No |
| `GET` | `/api/v1/agent/install.ps1`| Windows PowerShell installer bootstrap | No |

---

## License

Distributed under the MIT License.
