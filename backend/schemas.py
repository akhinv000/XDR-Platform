from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class AssetCreate(BaseModel):
    hostname: str
    ip_address: str
    operating_system: str
    status: str


class AssetUpdate(BaseModel):
    hostname: str
    ip_address: str
    operating_system: str
    status: str