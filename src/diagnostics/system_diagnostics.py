import platform
import socket
import psutil
import wmi


class SystemDiagnostics:

    def get_info(self):

        c = wmi.WMI()

        computer = {}

        computer["Nom du PC"] = socket.gethostname()

        computer["Système"] = (
            f"{platform.system()} {platform.release()}"
        )

        computer["Version"] = platform.version()

        computer["Processeur"] = platform.processor()

        computer["RAM"] = (
            f"{round(psutil.virtual_memory().total / (1024**3))} Go"
        )

        disk = psutil.disk_usage("/")

        computer["Disque"] = (
            f"{round(disk.used/(1024**3))} Go / "
            f"{round(disk.total/(1024**3))} Go"
        )

        try:
            bios = c.Win32_BIOS()[0]
            computer["BIOS"] = bios.SMBIOSBIOSVersion
        except Exception:
            computer["BIOS"] = "Inconnu"

        try:
            system = c.Win32_ComputerSystem()[0]
            computer["Constructeur"] = system.Manufacturer
            computer["Modèle"] = system.Model
        except Exception:
            pass

        return computer