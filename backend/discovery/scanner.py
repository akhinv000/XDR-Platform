import subprocess
from pathlib import Path

NMAP_PATH = r"C:\Program Files (x86)\Nmap\nmap.exe"
NETWORK = "192.168.56.0/24"


def run_scan():

    xml_file = Path(__file__).parent / "scan.xml"

    command = [
        NMAP_PATH,
        "-O",
        "-sV",
        "-oX",
        str(xml_file),
        NETWORK
    ]

    subprocess.run(command, check=True)

    return xml_file