import subprocess
import json
import platform

class SecurityInfo:
    """Classe chargée de vérifier la sécurité globale du système Windows."""

    @staticmethod
    def get_security_status():
        """
        Récupère l'état de l'antivirus, du pare-feu et des protections de base.
        Retourne une liste de dictionnaires représentant chaque point de contrôle.
        """
        checks = []
        if platform.system() != "Windows":
            return checks

        # 1. Vérification du Pare-feu (Firewall)
        checks.append(SecurityInfo._check_firewall())

        # 2. Vérification de l'Antivirus / Windows Defender
        checks.append(SecurityInfo._check_antivirus())

        # 3. Vérification de l'UAC (User Account Control)
        checks.append(SecurityInfo._check_uac())

        return checks

    @staticmethod
    def _check_firewall():
        try:
            ps_cmd = "Get-NetFirewallProfile | Select-Object Name, Enabled | ConvertTo-Json"
            # Ajout de -NoProfile et augmentation du timeout à 15s
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd], 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            
            if res.returncode == 0 and res.stdout.strip():
                profiles = json.loads(res.stdout)
                if isinstance(profiles, dict):
                    profiles = [profiles]
                
                all_enabled = all(p.get("Enabled") is True or p.get("Enabled") == 1 for p in profiles)
                
                if all_enabled:
                    return {
                        "title": "Pare-feu Windows",
                        "status": "OK",
                        "color": "green",
                        "details": "Tous les profils de pare-feu (Domaine, Privé, Public) sont actifs."
                    }
                else:
                    return {
                        "title": "Pare-feu Windows",
                        "status": "Avertissement",
                        "color": "orange",
                        "details": "Au moins un profil de pare-feu est désactivé."
                    }
        except Exception as e:
            print(f"[SecurityInfo] Erreur Firewall : {e}")

        return {
            "title": "Pare-feu Windows",
            "status": "Inconnu",
            "color": "orange",
            "details": "Impossible de vérifier le statut du pare-feu."
        }

    @staticmethod
    def _check_antivirus():
        try:
            # Recherche via WMI SecurityCenter2
            ps_cmd = "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Select-Object displayName, productState | ConvertTo-Json"
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd], 
                capture_output=True, 
                text=True, 
                timeout=15
            )

            if res.returncode == 0 and res.stdout.strip():
                av_data = json.loads(res.stdout)
                if isinstance(av_data, dict):
                    av_data = [av_data]

                if av_data:
                    av_names = [item.get("displayName", "Antivirus") for item in av_data]
                    names_str = ", ".join(av_names)
                    return {
                        "title": "Protection Antivirus",
                        "status": "OK",
                        "color": "green",
                        "details": f"Antivirus détecté(s) : {names_str}."
                    }
        except Exception as e:
            print(f"[SecurityInfo] Erreur Antivirus : {e}")

        return {
            "title": "Protection Antivirus",
            "status": "Avertissement",
            "color": "orange",
            "details": "Aucun antivirus actif ou statut non récupérable via WMI."
        }

    @staticmethod
    def _check_uac():
        try:
            # Vérification de la clé de registre UAC EnableLUA
            cmd = r'reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLUA'
            res = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=5)

            if "0x1" in res.stdout:
                return {
                    "title": "Contrôle de compte (UAC)",
                    "status": "OK",
                    "color": "green",
                    "details": "L'UAC est activé pour protéger contre l'exécution non autorisée."
                }
            elif "0x0" in res.stdout:
                return {
                    "title": "Contrôle de compte (UAC)",
                    "status": "Danger",
                    "color": "red",
                    "details": "L'UAC est désactivé ! Les applications peuvent s'exécuter avec les privilèges admin sans avertissement."
                }
        except Exception as e:
            print(f"[SecurityInfo] Erreur UAC : {e}")

        return {
            "title": "Contrôle de compte (UAC)",
            "status": "Inconnu",
            "color": "orange",
            "details": "Impossible de lire le registre UAC."
        }


if __name__ == "__main__":
    for check in SecurityInfo.get_security_status():
        print(check)