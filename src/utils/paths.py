"""Gestion centralisée des chemins de DIP Toolkit Pro.

Deux notions à ne pas confondre :

* resource_path() : fichiers EMBARQUÉS dans l'application (logo, icônes, thème).
  En développement : dossier du projet.
  Dans l'.exe PyInstaller : dossier temporaire d'extraction (sys._MEIPASS).

* data_dir() : fichiers MODIFIABLES par l'utilisateur (paramètres, rapports).
  En développement : dossier du projet.
  Dans l'.exe : dossier où se trouve l'.exe (mode portable, idéal pour une clé USB).
  Si ce dossier n'est pas accessible en écriture (ex. Program Files),
  repli sur %APPDATA%/DIP Toolkit Pro.
"""

import os
import sys
from pathlib import Path

APP_NAME = "DIP Toolkit Pro"


def is_frozen() -> bool:
    """True si l'application tourne depuis un .exe PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def project_root() -> Path:
    """Racine du projet en développement (dossier contenant main.py)."""
    return Path(__file__).resolve().parents[2]


def resource_path(relative: str) -> Path:
    """Chemin absolu d'une ressource embarquée (ex. 'assets/logo/logo.png')."""
    if is_frozen():
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = project_root()
    return base / relative


def app_dir() -> Path:
    """Dossier de l'application : celui de l'.exe, ou la racine du projet."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return project_root()


def _is_writable(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        probe = folder / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def data_dir() -> Path:
    """Dossier où l'application peut écrire ses paramètres et ses données."""
    folder = app_dir()
    if _is_writable(folder):
        return folder

    appdata = os.environ.get("APPDATA") or str(Path.home())
    fallback = Path(appdata) / APP_NAME
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def settings_path() -> Path:
    """Emplacement du fichier de paramètres."""
    return data_dir() / "settings.json"
