"""Collecte des données réelles du poste pour le rapport client.

Chaque section est protégée : si une commande échoue (droits, PowerShell absent...),
la section vaut None et le rapport indique « non vérifié » au lieu de planter.
"""

import os
import platform
import socket
import time
from datetime import datetime

import psutil

from src.diagnostics.disk_info import get_disks
from src.diagnostics.printer_info import PrinterInfo
from src.diagnostics.security_info import SecurityInfo


def _wmi_info() -> dict:
    """Infos matérielles via WMI (Windows uniquement). Retourne {} en cas d'échec."""
    if platform.system() != "Windows":
        return {}

    pythoncom = None
    try:
        import pythoncom  # type: ignore
        pythoncom.CoInitialize()  # obligatoire dans un thread secondaire
    except Exception:
        pythoncom = None

    info = {}
    try:
        import wmi  # type: ignore
        c = wmi.WMI()
        try:
            cpu = c.Win32_Processor()[0]
            info["cpu_name"] = " ".join(str(cpu.Name).split())
        except Exception:
            pass
        try:
            bios = c.Win32_BIOS()[0]
            info["serial"] = str(bios.SerialNumber or "").strip()
            info["bios"] = str(bios.SMBIOSBIOSVersion or "").strip()
        except Exception:
            pass
        try:
            cs = c.Win32_ComputerSystem()[0]
            info["manufacturer"] = str(cs.Manufacturer or "").strip()
            info["model"] = str(cs.Model or "").strip()
        except Exception:
            pass
        try:
            osi = c.Win32_OperatingSystem()[0]
            info["os_caption"] = str(osi.Caption or "").strip()
        except Exception:
            pass
    except Exception:
        pass
    finally:
        if pythoncom is not None:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass
    return info


def _windows_build() -> int:
    try:
        return int(platform.version().split(".")[2])
    except (IndexError, ValueError):
        return 0


def collect_system() -> dict:
    wmi_data = _wmi_info()

    os_name = wmi_data.get("os_caption")
    if not os_name:
        release = platform.release()
        # platform.release() renvoie "10" même sous Windows 11 (build >= 22000)
        if platform.system() == "Windows" and release == "10" and _windows_build() >= 22000:
            release = "11"
        os_name = f"{platform.system()} {release}"

    mem = psutil.virtual_memory()
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime_days = (datetime.now() - boot).total_seconds() / 86400

    return {
        "hostname": socket.gethostname(),
        "os_name": os_name,
        "os_version": platform.version(),
        "os_build": _windows_build(),
        "architecture": platform.architecture()[0],
        "manufacturer": wmi_data.get("manufacturer", ""),
        "model": wmi_data.get("model", ""),
        "serial": wmi_data.get("serial", ""),
        "bios": wmi_data.get("bios", ""),
        "cpu_name": wmi_data.get("cpu_name") or platform.processor() or "Inconnu",
        "cpu_cores": psutil.cpu_count(logical=False) or psutil.cpu_count() or 0,
        "cpu_threads": psutil.cpu_count() or 0,
        # Mesure sur 1 seconde : plus fiable qu'une lecture instantanée
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_total_gb": round(mem.total / 1024**3, 1),
        "ram_used_gb": round(mem.used / 1024**3, 1),
        "ram_percent": int(mem.percent),
        "uptime_days": round(uptime_days, 1),
    }


def _norm_drive(path: str) -> str:
    return str(path).upper().rstrip("\\/")


def collect_disks() -> list:
    """Disques du poste, avec un repère « disque système » (celui qui contient l'OS)."""
    if platform.system() == "Windows":
        system_drive = _norm_drive(os.environ.get("SystemDrive", "C:"))
    else:
        system_drive = _norm_drive("/")

    disks = []
    for d in get_disks():
        if d.get("total", 0) > 0:
            d = dict(d)
            d["is_system"] = _norm_drive(d.get("mount", "")) == system_drive
            disks.append(d)
    return disks


def _internet_ok(timeout: float = 2.0) -> bool:
    """Test simple : connexion TCP vers un DNS public (aucune donnée envoyée)."""
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=timeout):
            return True
    except OSError:
        return False


def collect_network() -> dict:
    interfaces = []
    stats = psutil.net_if_stats()

    for name, addrs in psutil.net_if_addrs().items():
        st = stats.get(name)
        if st is None or not st.isup:
            continue

        ipv4, mac = "", ""
        for a in addrs:
            if a.family == socket.AF_INET:
                ipv4 = a.address
            elif a.family == psutil.AF_LINK:
                mac = a.address.replace("-", ":").upper()

        # On ignore la boucle locale et les adresses auto-attribuées (pas de réseau)
        if not ipv4 or ipv4.startswith("127.") or ipv4.startswith("169.254."):
            continue

        interfaces.append({"name": name, "ip": ipv4, "mac": mac})

    return {"interfaces": interfaces, "internet": _internet_ok()}


def collect_security() -> list:
    return SecurityInfo.get_security_status()


def collect_printers() -> list:
    return PrinterInfo.get_printers()


def _safe(func):
    try:
        return func()
    except Exception as exc:  # une section en échec ne doit pas bloquer le rapport
        print(f"[ReportData] {func.__name__} a échoué : {exc}")
        return None


def collect_all(options: dict) -> dict:
    """Collecte uniquement les sections demandées. None = non vérifié."""
    data = {
        "generated_at": datetime.now(),
        "system": _safe(collect_system),  # toujours nécessaire (nom du poste, OS)
        "disks": None,
        "network": None,
        "security": None,
        "printers": None,
    }
    if options.get("include_disks", True):
        data["disks"] = _safe(collect_disks)
    if options.get("include_network", True):
        data["network"] = _safe(collect_network)
    if options.get("include_security", True):
        data["security"] = _safe(collect_security)
    if options.get("include_printers", True):
        data["printers"] = _safe(collect_printers)
    return data
