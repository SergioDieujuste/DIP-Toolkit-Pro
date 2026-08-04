import subprocess
import json
import platform

class PrinterInfo:
    """Classe chargée de récupérer les informations sur les imprimantes du système."""

    @staticmethod
    def get_printers():
        """
        Récupère la liste des imprimantes installées avec leurs détails.
        Retourne une liste de dictionnaires.
        """
        printers = []
        system = platform.system()

        if system == "Windows":
            try:
                # Commande PowerShell pour récupérer les imprimantes au format JSON
                ps_command = (
                    "Get-CimInstance Win32_Printer | "
                    "Select-Object Name, DriverName, PortName, PrinterStatus, WorkOffline, IsDefault | "
                    "ConvertTo-Json"
                )
                result = subprocess.run(
                    ["powershell", "-Command", ps_command],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout.strip():
                    data = json.loads(result.stdout)
                    # Si une seule imprimante est retournée, PowerShell renvoie un dict au lieu d'une liste
                    if isinstance(data, dict):
                        data = [data]

                    for item in data:
                        status_str = PrinterInfo._parse_windows_status(
                            item.get("PrinterStatus"),
                            item.get("WorkOffline")
                        )
                        printers.append({
                            "name": item.get("Name", "Inconnue"),
                            "driver": item.get("DriverName", "N/A"),
                            "port": item.get("PortName", "N/A"),
                            "is_default": item.get("IsDefault", False),
                            "offline": item.get("WorkOffline", False),
                            "status": status_str
                        })
            except Exception as e:
                print(f"[PrinterInfo] Erreur lors de la récupération : {e}")

        else:
            # Fallback pour Linux / macOS si besoin (CUPS / lpstat)
            try:
                result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        parts = line.split()
                        if len(parts) >= 2:
                            printers.append({
                                "name": parts[1],
                                "driver": "Système CUPS",
                                "port": "CUPS",
                                "is_default": False,
                                "offline": "disabled" in line,
                                "status": "Prête" if "idle" in line else "Inconnu"
                            })
            except Exception:
                pass

        return printers

    @staticmethod
    def _parse_windows_status(status_code, work_offline):
        """Convertit le code de statut Windows en texte clair."""
        if work_offline:
            return "Hors ligne"
        
        status_map = {
            1: "Autre",
            2: "Inconnu",
            3: "Prête / Idle",
            4: "Impression en cours",
            5: "Préchauffage",
            6: "Arrêt de la transmission",
            7: "Hors ligne"
        }
        return status_map.get(status_code, "Prête")


if __name__ == "__main__":
    # Test rapide en autonome
    printers = PrinterInfo.get_printers()
    for p in printers:
        print(p)