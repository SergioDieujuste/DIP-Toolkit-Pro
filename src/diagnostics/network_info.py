import socket
import uuid
import psutil


def get_network_info():

    hostname = socket.gethostname()

    try:
        ip = socket.gethostbyname(hostname)
    except Exception:
        ip = "Inconnue"

    mac = ":".join(
        f"{(uuid.getnode() >> ele) & 0xff:02X}"
        for ele in range(40, -1, -8)
    )

    interface = "Inconnue"

    for name, addresses in psutil.net_if_addrs().items():

        for addr in addresses:

            if addr.family == socket.AF_INET:
                interface = name
                break

        if interface != "Inconnue":
            break

    return {

        "hostname": hostname,
        "ip": ip,
        "mac": mac,
        "interface": interface,

    }