from typing import Optional
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class AssetCreate(BaseModel):
    hostname: str
    ip_address: str
    operating_system: Optional[str] = "Unknown"
    status: Optional[str] = "Online"
    mac_address: Optional[str] = ""
    vendor: Optional[str] = ""
    asset_type: Optional[str] = "Unknown"
    open_ports: Optional[str] = ""
    services: Optional[str] = ""
    risk_score: Optional[int] = 0


class AssetUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    operating_system: Optional[str] = None
    status: Optional[str] = None
    mac_address: Optional[str] = None
    vendor: Optional[str] = None
    asset_type: Optional[str] = None
    open_ports: Optional[str] = None
    services: Optional[str] = None
    risk_score: Optional[int] = None


class LogIngestRequest(BaseModel):
    hostname: str
    message: str
    level: Optional[str] = "Low"
    source: Optional[str] = "System"
    category: Optional[str] = "AUTH"


class ScanRequest(BaseModel):
    cidr: Optional[str] = None