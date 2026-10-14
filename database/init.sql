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
    status VARCHAR(20) DEFAULT 'Online',
    open_ports TEXT,
    services TEXT,
    risk_score INTEGER DEFAULT 0,
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
    status VARCHAR(20) DEFAULT 'Open'
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