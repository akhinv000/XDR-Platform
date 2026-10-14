from typing import Optional
from sqlalchemy.orm import Session

from discovery.scanner import run_scan
from discovery.parser import parse_scan
from discovery.updater import update_assets


def discover_assets(network: Optional[str] = None, db: Optional[Session] = None):
    """Orchestrates scanning, XML parsing, and asset database updates."""
    xml_file = run_scan(network=network)
    assets = parse_scan(xml_file)
    update_assets(assets, db=db)
    return len(assets)