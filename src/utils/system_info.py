import platform
import socket
import psutil


def get_system_info():
    """Retourne les principales informations du PC."""

    return {
        "computer": socket.gethostname(),
        "windows": f"{platform.system()} {platform.release()}",
        "processor": platform.processor(),
        "ram": f"{round(psutil.virtual_memory().total / (1024**3))} Go",
        "disk": f"{round(psutil.disk_usage('/').total / (1024**3))} Go",
    }