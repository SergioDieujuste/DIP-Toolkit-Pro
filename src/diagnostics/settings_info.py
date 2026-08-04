import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "theme": "Sombre (Turquoise)",
    "default_export_dir": os.path.expanduser("~/Documents"),
    "auto_refresh_interval": 2,
    "run_at_startup": False,
    "default_tech_name": "Technicien DIP"
}


class SettingsInfo:
    """Classe chargée de charger et sauvegarder les paramètres de l'application."""

    @staticmethod
    def load_settings() -> dict:
        """Charge les paramètres depuis le fichier JSON ou retourne les valeurs par défaut."""
        if not os.path.exists(SETTINGS_FILE):
            SettingsInfo.save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS.copy()

        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # S'assurer que toutes les clés par défaut existent
                settings = DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except Exception as e:
            print(f"[SettingsInfo] Erreur chargement : {e}")
            return DEFAULT_SETTINGS.copy()

    @staticmethod
    def save_settings(settings: dict) -> tuple[bool, str]:
        """Sauvegarde le dictionnaire de paramètres dans le fichier JSON."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            return True, "Paramètres enregistrés avec succès !"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde : {e}"