from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import ScanRequest
from auth_utils import get_current_user
from services.discovery_service import discover_assets

router = APIRouter(
    prefix="/discovery",
    tags=["Discovery"]
)


@router.post("/scan")
def scan_network(
    scan_req: Optional[ScanRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger network asset discovery and port risk scoring."""
    cidr = scan_req.cidr if scan_req else None
    try:
        total = discover_assets(network=cidr, db=db)
        return {
            "message": "Network scan completed successfully.",
            "assets_discovered": total
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network scan error: {str(e)}"
        )