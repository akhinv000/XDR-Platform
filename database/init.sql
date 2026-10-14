CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    hostname VARCHAR(100),
    ip_address VARCHAR(50),
    operating_system VARCHAR(100),
    status VARCHAR(20),
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users(username,password)
VALUES
('admin','admin123');

INSERT INTO assets
(hostname,ip_address,operating_system,status)

VALUES

('WIN-01','192.168.1.10','Windows 11','Online'),

('KALI-01','192.168.1.20','Kali Linux','Online'),

('UBUNTU-01','192.168.1.30','Ubuntu Server','Offline');