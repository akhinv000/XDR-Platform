from discovery.scanner import run_scan
from discovery.parser import parse_scan
from discovery.updater import update_assets


def discover_assets():

    xml_file = run_scan()

    assets = parse_scan(xml_file)

    update_assets(assets)

    return len(assets)