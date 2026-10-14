# XDR Platform

An enterprise Extended Detection and Response (XDR) platform providing real-time security monitoring, automated alert detection, asset discovery, and analytics.

---

## Features

- **Centralized Security Dashboard**: Real-time counter metrics for monitored assets, active security alerts, high-severity threats, and ingested log events.
- **Asset Inventory & Discovery**: Network host discovery and vulnerability assessment via Nmap scans, storing operating systems, MAC addresses, open ports, and risk scores.
- **Log Aggregation & Threat Detection**: Automated parsing and analysis of system logs with heuristic detection rules for:
  - SSH Brute-Force & Failed Logins
  - Privilege Escalation (`sudo`) attempts
  - Suspicious access and authorization failures
- **Security Analytics**: Chart.js visualizations for OS distribution, alert severity breakdown, log origin tracking, and risk assessment.
- **Hybrid Storage Architecture**: PostgreSQL persistence for assets, users, and events with OpenSearch integration for scalable security audit logs.

---

## Tech Stack

- **Backend**: Python 3.13, FastAPI, SQLAlchemy, Uvicorn
- **Database**: PostgreSQL 17
- **Search & Analytics**: OpenSearch 2.19
- **Frontend**: Vanilla JavaScript, HTML5, Modern CSS, Chart.js, Font Awesome

---

## Getting Started

### 1. Prerequisites

- Python 3.11+
- PostgreSQL
- Docker & Docker Compose (optional for containerized deployment)

### 2. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate # Linux / macOS

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

The API will be available at `http://127.0.0.1:9000` with Swagger docs at `http://127.0.0.1:9000/docs`.

### 3. Frontend Setup

Serve the `frontend/` directory with any static server or Python:

```bash
python -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500/login.html` in your browser.

- **Default Username**: `admin`
- **Default Password**: `admin123`

---

## License

MIT License
