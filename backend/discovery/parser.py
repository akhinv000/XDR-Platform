import xml.etree.ElementTree as ET


def parse_scan(xml_file):

    tree = ET.parse(str(xml_file))

    root = tree.getroot()

    assets = []

    for host in root.findall("host"):

        status = host.find("status")

        if status is None or status.attrib.get("state") != "up":
            continue

        asset = {}

        # ----------------------------
        # IP Address
        # ----------------------------

        ip = host.find("address[@addrtype='ipv4']")

        if ip is not None:
            asset["ip"] = ip.attrib["addr"]

        # ----------------------------
        # MAC Address
        # ----------------------------

        mac = host.find("address[@addrtype='mac']")

        if mac is not None:

            asset["mac"] = mac.attrib.get("addr", "")

            asset["vendor"] = mac.attrib.get("vendor", "")

        else:

            asset["mac"] = ""

            asset["vendor"] = ""

        # ----------------------------
        # Hostname
        # ----------------------------

        hostname = host.find("hostnames/hostname")

        if hostname is not None:

            asset["hostname"] = hostname.attrib.get("name", "")

        else:

            asset["hostname"] = ""

        # ----------------------------
        # Operating System
        # ----------------------------

        osmatch = host.find("os/osmatch")

        if osmatch is not None:

            asset["os"] = osmatch.attrib.get("name", "Unknown")

        else:

            asset["os"] = "Unknown"

        # ----------------------------
        # Ports & Services
        # ----------------------------

        ports = []

        services = []

        for port in host.findall("ports/port"):

            state = port.find("state")

            if state is None:
                continue

            if state.attrib["state"] != "open":
                continue

            ports.append(port.attrib["portid"])

            service = port.find("service")

            if service is not None:

                name = service.attrib.get("name", "")

                product = service.attrib.get("product", "")

                version = service.attrib.get("version", "")

                services.append(f"{name} {product} {version}".strip())

        asset["ports"] = ports

        asset["services"] = services

        # ----------------------------
        # Friendly Hostname
        # ----------------------------

        if asset["hostname"] == "":

            if "Windows" in asset["os"]:

                asset["hostname"] = "Windows Host"

            elif "Linux" in asset["os"]:

                asset["hostname"] = "Linux Host"

            elif "VirtualBox" in asset["vendor"]:

                asset["hostname"] = "VirtualBox Host"

            else:

                asset["hostname"] = "Unknown Host"

        # ----------------------------
        # Ignore Bad OS Guesses
        # ----------------------------

        if len(asset["ports"]) == 0:

            asset["os"] = "Unknown"

        assets.append(asset)

    return assets