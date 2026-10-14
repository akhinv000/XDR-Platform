from discovery.parser import parse_scan
from discovery.updater import update_assets
from pathlib import Path

xml_file = Path(__file__).parent / "scan.xml"

assets = parse_scan(xml_file)

update_assets(assets)

print("Assets imported successfully.")