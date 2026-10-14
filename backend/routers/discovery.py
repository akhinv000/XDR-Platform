from fastapi import APIRouter
from services.discovery_service import discover_assets

router = APIRouter(
    prefix="/discovery",
    tags=["Discovery"]
)


@router.post("/scan")
def scan_network():

    total = discover_assets()

    return {
        "message": "Network scan completed successfully.",
        "assets_discovered": total
    }