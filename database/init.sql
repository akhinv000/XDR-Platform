-- Database initialization for Nexa XDR Platform

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(100),
    ip_address VARCHAR(50) UNIQUE,
    mac_address VARCHAR(50),
    vendor VARCHAR(100),
    operating_system VARCHAR(100),
    os_guess VARCHAR(255),
    asset_type VARCHAR(50),
    status VARCHAR(30) DEFAULT 'Online',
    open_ports TEXT,
    services TEXT,
    risk_score INTEGER DEFAULT 0,
    agent_id VARCHAR(100),
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hostname VARCHAR(100),
    level VARCHAR(20),
    source VARCHAR(100),
    message TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hostname VARCHAR(100),
    severity VARCHAR(20),
    title VARCHAR(100),
    description TEXT,
    status VARCHAR(20) DEFAULT 'Open',
    mitre_tactic VARCHAR(100) DEFAULT 'Unknown',
    mitre_technique VARCHAR(100) DEFAULT 'Unknown',
    source_ip VARCHAR(50) DEFAULT '',
    incident_id INTEGER
);

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    severity VARCHAR(20) DEFAULT 'Medium',
    status VARCHAR(30) DEFAULT 'New',
    mitre_tactic VARCHAR(100) DEFAULT 'General',
    mitre_technique VARCHAR(100) DEFAULT 'General',
    hostname VARCHAR(100) DEFAULT 'Multiple',
    source_ip VARCHAR(50) DEFAULT '',
    alert_count INTEGER DEFAULT 1,
    analyst_notes TEXT DEFAULT '',
    assigned_to VARCHAR(100) DEFAULT 'SOC Operator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS blocked_ips (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(50) UNIQUE NOT NULL,
    reason VARCHAR(255) DEFAULT 'Manual SOC block',
    blocked_by VARCHAR(100) DEFAULT 'SOC Operator',
    status VARCHAR(20) DEFAULT 'Active',
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_endpoints (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    hostname VARCHAR(100) NOT NULL,
    ip_address VARCHAR(50) NOT NULL,
    operating_system VARCHAR(100) DEFAULT 'Unknown',
    os_version VARCHAR(100) DEFAULT '',
    status VARCHAR(30) DEFAULT 'Online',
    api_key VARCHAR(100) NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pending_commands TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS containment_actions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(50) NOT NULL,
    target VARCHAR(100) NOT NULL,
    performed_by VARCHAR(100) DEFAULT 'SOC Operator',
    details TEXT DEFAULT '',
    status VARCHAR(20) DEFAULT 'Executed'
);

-- Default Admin User (Default password: admin123)
INSERT INTO users (username, password)
VALUES ('admin', 'admin123')
ON CONFLICT (username) DO NOTHING;

-- Seed Assets
INSERT INTO assets (hostname, ip_address, operating_system, asset_type, status, open_ports, services, risk_score)
VALUES
('WIN-01', '192.168.1.10', 'Windows 11', 'Windows Endpoint', 'Online', '135,445,3389', 'msrpc, microsoft-ds, ms-wbt-server', 70),
('KALI-01', '192.168.1.20', 'Kali Linux', 'Linux Server', 'Online', '22,80', 'ssh OpenSSH, http Apache', 7),
('UBUNTU-01', '192.168.1.30', 'Ubuntu Server', 'Linux Server', 'Offline', '22', 'ssh OpenSSH', 5)
ON CONFLICT (ip_address) DO NOTHING;