import os
import shutil
import subprocess
from pathlib import Path

COMMON_NMAP_PATHS = [
    shutil.which("nmap"),
    r"C:\Program Files (x86)\Nmap\nmap.exe",
    r"C:\Program Files\Nmap\nmap.exe",
    "/usr/bin/nmap",
    "/usr/local/bin/nmap",
]


def find_nmap_binary() -> str:
    """Find installed nmap executable across common system paths."""
    for path in COMMON_NMAP_PATHS:
        if path and Path(path).exists():
            return str(path)
    return None


def run_scan(network: str = None):
    """
    Executes an Nmap scan against the specified network subnet.
    If Nmap is not installed, gracefully falls back to existing scan.xml.
    """
    xml_file = Path(__file__).parent / "scan.xml"

    if network is None:
        network = os.getenv("NMAP_NETWORK", "192.168.56.0/24")

    nmap_path = find_nmap_binary()

    if not nmap_path:
        if xml_file.exists():
            return xml_file
        raise FileNotFoundError(
            "Nmap binary not found. Please install Nmap or add it to PATH."
        )

    command = [
        nmap_path,
        "-O",
        "-sV",
        "-oX",
        str(xml_file),
        network
    ]

    try:
        subprocess.run(command, check=True, timeout=300)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, PermissionError) as e:
        # If scan fails (e.g. requires admin raw sockets for -O), fall back to existing xml if available
        if xml_file.exists():
            return xml_file
        raise RuntimeError(f"Nmap scan failed: {e}")

    return xml_file