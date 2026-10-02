import os
import shutil
import tempfile
import subprocess
import platform

class MaintenanceInfo:
    """Classe regroupant les actions de nettoyage et maintenance du système."""

    @staticmethod
    def get_available_tasks():
        """Retourne la liste des tâches de maintenance disponibles."""
        return [
            {
                "id": "clean_temp",
                "title": "Nettoyage des Fichiers Temporaires",
                "description": "Supprime les fichiers temporaires de l'utilisateur et du système (%TEMP%).",
                "action_name": "Nettoyer"
            },
            {
                "id": "flush_dns",
                "title": "Vidage du Cache DNS",
                "description": "Réinitialise le cache de résolution DNS Windows pour résoudre les problèmes de connexion.",
                "action_name": "Vider DNS"
            },
            {
                "id": "empty_recycle",
                "title": "Vidage de la Corbeille",
                "description": "Purge définitivement tous les fichiers se trouvant dans la corbeille Windows.",
                "action_name": "Vider Corbeille"
            }
        ]

    @staticmethod
    def run_task(task_id: str) -> tuple[bool, str]:
        """
        Exécute la tâche spécifiée par son ID.
        Retourne (Succès: bool, Message: str).
        """
        if platform.system() != "Windows":
            return False, "Fonctionnalité réservée à Windows."

        if task_id == "clean_temp":
            return MaintenanceInfo._clean_temp_files()
        elif task_id == "flush_dns":
            return MaintenanceInfo._flush_dns()
        elif task_id == "empty_recycle":
            return MaintenanceInfo._empty_recycle_bin()
        else:
            return False, "Tâche inconnue."

    @staticmethod
    def _clean_temp_files() -> tuple[bool, str]:
        deleted_count = 0
        freed_bytes = 0
        
        # Chemins des dossiers temporaires
        temp_dirs = [tempfile.gettempdir(), r"C:\Windows\Temp"]

        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    try:
                        file_path = os.path.join(root, f)
                        freed_bytes += os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception:
                        # Ignorer les fichiers verrouillés/utilisés
                        pass

        freed_mb = freed_bytes / (1024 * 1024)
        return True, f"Nettoyage terminé : {deleted_count} fichiers supprimés (~{freed_mb:.1f} Mo libérés)."

    @staticmethod
    def _flush_dns() -> tuple[bool, str]:
        try:
            res = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if res.returncode == 0:
                return True, "Le cache de résolution DNS a été vidé avec succès."
            else:
                return False, "Échec lors du vidage du cache DNS."
        except Exception as e:
            return False, f"Erreur : {e}"

    @staticmethod
    def _empty_recycle_bin() -> tuple[bool, str]:
        try:
            ps_cmd = "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                timeout=10
            )
            return True, "La corbeille a été vidée."
        except Exception as e:
            return False, f"Erreur lors du vidage de la corbeille : {e}"