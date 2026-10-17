from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(100))
    ip_address = Column(String(50), unique=True)
    mac_address = Column(String(50))
    vendor = Column(String(100))
    operating_system = Column(String(100))
    os_guess = Column(String(255))
    asset_type = Column(String(50))
    status = Column(String(30), default="Online")  # Online, Quarantined, Offline
    open_ports = Column(String)
    services = Column(String)
    risk_score = Column(Integer, default=0)
    agent_id = Column(String(100), nullable=True)
    first_seen = Column(DateTime, default=utcnow)
    last_seen = Column(DateTime, default=utcnow)


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utcnow)
    hostname = Column(String(100))
    level = Column(String(20))
    source = Column(String(100))
    message = Column(String)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utcnow)
    hostname = Column(String(100))
    severity = Column(String(20))
    title = Column(String(100))
    description = Column(String)
    status = Column(String(20), default="Open")
    mitre_tactic = Column(String(100), default="Unknown")
    mitre_technique = Column(String(100), default="Unknown")
    source_ip = Column(String(50), default="")
    incident_id = Column(Integer, nullable=True)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    severity = Column(String(20), default="Medium")  # Critical, High, Medium, Low
    status = Column(String(30), default="New")  # New, Investigating, Contained, Resolved, Closed
    mitre_tactic = Column(String(100), default="General")
    mitre_technique = Column(String(100), default="General")
    hostname = Column(String(100), default="Multiple")
    source_ip = Column(String(50), default="")
    alert_count = Column(Integer, default=1)
    analyst_notes = Column(String, default="")
    assigned_to = Column(String(100), default="SOC Operator")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow)


class BlockedIP(Base):
    __tablename__ = "blocked_ips"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(50), unique=True, nullable=False)
    reason = Column(String(255), default="Manual SOC block")
    blocked_by = Column(String(100), default="SOC Operator")
    status = Column(String(20), default="Active")  # Active, Revoked
    blocked_at = Column(DateTime, default=utcnow)


class AgentEndpoint(Base):
    __tablename__ = "agent_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(100), unique=True, index=True, nullable=False)
    hostname = Column(String(100), nullable=False)
    ip_address = Column(String(50), nullable=False)
    operating_system = Column(String(100), default="Unknown")
    os_version = Column(String(100), default="")
    status = Column(String(30), default="Online")  # Online, Quarantined, Offline
    api_key = Column(String(100), nullable=False)
    first_seen = Column(DateTime, default=utcnow)
    last_heartbeat = Column(DateTime, default=utcnow)
    pending_commands = Column(String, default="[]")  # JSON encoded list of command dicts


class ContainmentAction(Base):
    __tablename__ = "containment_actions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utcnow)
    action_type = Column(String(50), nullable=False)  # QUARANTINE_HOST, UNQUARANTINE_HOST, BLOCK_IP, UNBLOCK_IP
    target = Column(String(100), nullable=False)  # IP or Hostname
    performed_by = Column(String(100), default="SOC Operator")
    details = Column(String, default="")
    status = Column(String(20), default="Executed")