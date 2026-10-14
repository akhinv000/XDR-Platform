# XDR Platform

An enterprise Extended Detection and Response (XDR) platform providing real-time security monitoring, automated threat alert detection, network asset discovery, and SOC analytics.

---

## Features

- **Centralized SOC Dashboard**: Real-time counter metrics for monitored assets, active security alerts, high-severity threats, and ingested log events.
- **JWT Authentication & Access Control**: Secure login with password verification (bcrypt/salted SHA-256 fallback), constant-time comparisons, and Bearer token protected APIs.
- **Asset Inventory & Discovery**: Network host discovery and vulnerability assessment via Nmap scans, storing operating systems, MAC addresses, open ports, and risk scores.
- **Log Aggregation & Automated Threat Detection**: Automated parsing and analysis of system logs with heuristic detection rules for:
  - SSH Brute-Force & Failed Logins
  - Privilege Escalation (`sudo`) attempts
  - Suspicious access and authorization failures
- **Security Analytics**: Chart.js visualizations for OS distribution, alert severity breakdown, log origin tracking, and risk assessment.
- **Hybrid Storage Architecture**: PostgreSQL persistence for assets, users, logs, and alerts with OpenSearch integration for high-volume security search.

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

### 2. Quickstart with Docker Compose

To spin up PostgreSQL, OpenSearch, and the XDR Backend in isolated containers with persistent storage:

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

The API will be available at `http://127.0.0.1:9000` with interactive Swagger docs at `http://127.0.0.1:9000/docs`.

### 3. Manual Local Setup

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

### 4. Frontend Setup

Serve the `frontend/` directory with any static server or Python:

```bash
python -m http.server 5500 --directory frontend
```

Open `http://127.0.0.1:5500/login.html` in your browser.

- **Default Username**: `admin`
- **Default Password**: `admin123`

---

## API Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/login` | Authenticate and obtain JWT access token | No |
| `GET` | `/auth/me` | Retrieve profile of the authenticated user | Yes |
| `GET` | `/dashboard/stats` | Aggregated dashboard counter statistics | Yes |
| `GET` | `/assets/` | List all discovered and registered assets | Yes |
| `POST` | `/assets/` | Register a new asset manually | Yes |
| `PUT` | `/assets/{id}` | Update asset metadata and status | Yes |
| `DELETE`| `/assets/{id}` | Remove an asset from inventory | Yes |
| `POST` | `/discovery/scan` | Initiate network discovery scan | Yes |
| `GET` | `/alerts/` | List active security alerts | Yes |
| `PUT` | `/alerts/{id}/acknowledge` | Mark an alert as Acknowledged | Yes |
| `GET` | `/logs/` | Query recent security & authentication logs | Yes |
| `POST` | `/logs/collect` | Ingest `auth.log` and trigger threat detection | Yes |
| `POST` | `/logs/ingest` | Ingest single event & evaluate heuristics | Yes |
| `GET` | `/analytics/` | Aggregated data for SOC charts | Yes |

---

## License

MIT License
