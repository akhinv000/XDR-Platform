from sqlalchemy import Column, Integer, String, DateTime
from database import Base
from datetime import datetime


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

    status = Column(String(20))

    open_ports = Column(String)

    services = Column(String)

    risk_score = Column(Integer, default=0)

    first_seen = Column(DateTime, default=datetime.utcnow)

    last_seen = Column(DateTime, default=datetime.utcnow)

class Log(Base):

    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)

    timestamp = Column(DateTime)

    hostname = Column(String(100))

    level = Column(String(20))

    source = Column(String(100))

    message = Column(String)

class Alert(Base):

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)

    timestamp = Column(DateTime)

    hostname = Column(String(100))

    severity = Column(String(20))

    title = Column(String(100))

    description = Column(String)

    status = Column(String(20), default="Open")