from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import SessionLocal
from schemas import AssetCreate, AssetUpdate

router = APIRouter(prefix="/assets", tags=["Asset Inventory"])


@router.get("/")
def get_assets():

    db = SessionLocal()

    assets = db.execute(
        text("""
        SELECT *
        FROM assets
        ORDER BY id
        """)
    ).mappings().all()

    db.close()

    return assets


@router.post("/")
def add_asset(asset: AssetCreate):

    db = SessionLocal()

    db.execute(
        text("""
        INSERT INTO assets
        (hostname, ip_address, operating_system, status)

        VALUES
        (:hostname,:ip,:os,:status)
        """),
        {
            "hostname": asset.hostname,
            "ip": asset.ip_address,
            "os": asset.operating_system,
            "status": asset.status
        }
    )

    db.commit()
    db.close()

    return {"message": "Asset Added"}


@router.put("/{asset_id}")
def update_asset(asset_id: int, asset: AssetUpdate):

    db = SessionLocal()

    result = db.execute(
        text("""
        UPDATE assets

        SET

        hostname=:hostname,

        ip_address=:ip,

        mac_address=:mac,

        vendor=:vendor,

        operating_system=:os,

        asset_type=:type,

        status=:status,

        open_ports=:ports,

        services=:services,

        risk_score=:risk

        WHERE id=:id
        """),
        {
            "hostname": asset.hostname,
            "ip": asset.ip_address,
            "mac": asset.mac_address,
            "vendor": asset.vendor,
            "os": asset.operating_system,
            "type": asset.asset_type,
            "status": asset.status,
            "ports": asset.open_ports,
            "services": asset.services,
            "risk": asset.risk_score,
            "id": asset_id
        }
    )

    db.commit()
    db.close()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {"message": "Asset Updated"}

    db = SessionLocal()

    result = db.execute(
        text("""
        UPDATE assets

        SET

        hostname=:hostname,

        ip_address=:ip,

        operating_system=:os,

        status=:status

        WHERE id=:id
        """),
        {
            "hostname": asset.hostname,
            "ip": asset.ip_address,
            "os": asset.operating_system,
            "status": asset.status,
            "id": asset_id
        }
    )

    db.commit()
    db.close()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {"message": "Asset Updated"}


@router.delete("/{asset_id}")
def delete_asset(asset_id: int):

    db = SessionLocal()

    result = db.execute(
        text("""
        DELETE FROM assets
        WHERE id=:id
        """),
        {"id": asset_id}
    )

    db.commit()
    db.close()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {"message": "Asset Deleted"}