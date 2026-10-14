from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Asset, User
from schemas import AssetCreate, AssetUpdate
from auth_utils import get_current_user

router = APIRouter(prefix="/assets", tags=["Asset Inventory"])


@router.get("/")
def get_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all monitored assets."""
    assets = db.query(Asset).order_by(Asset.id).all()
    return [
        {
            "id": a.id,
            "hostname": a.hostname or "Unknown",
            "ip_address": a.ip_address,
            "mac_address": a.mac_address or "",
            "vendor": a.vendor or "",
            "operating_system": a.operating_system or "Unknown",
            "os_guess": a.os_guess or "",
            "asset_type": a.asset_type or "Unknown",
            "status": a.status or "Offline",
            "open_ports": a.open_ports or "",
            "services": a.services or "",
            "risk_score": a.risk_score or 0,
            "first_seen": a.first_seen.isoformat() if a.first_seen else "",
            "last_seen": a.last_seen.isoformat() if a.last_seen else "",
        }
        for a in assets
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_asset(
    asset_data: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually register a new asset."""
    existing = db.query(Asset).filter(Asset.ip_address == asset_data.ip_address).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset with IP address {asset_data.ip_address} already exists."
        )

    now = datetime.now(timezone.utc)
    new_asset = Asset(
        hostname=asset_data.hostname,
        ip_address=asset_data.ip_address,
        operating_system=asset_data.operating_system or "Unknown",
        status=asset_data.status or "Online",
        mac_address=asset_data.mac_address or "",
        vendor=asset_data.vendor or "",
        asset_type=asset_data.asset_type or "Unknown",
        open_ports=asset_data.open_ports or "",
        services=asset_data.services or "",
        risk_score=asset_data.risk_score or 0,
        first_seen=now,
        last_seen=now,
    )

    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    return {
        "message": "Asset Added",
        "asset_id": new_asset.id
    }


@router.put("/{asset_id}")
def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update asset metadata and status."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_dict = asset_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(asset, field, value)

    asset.last_seen = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Asset Updated"}


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an asset from the inventory."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()

    return {"message": "Asset Deleted"}