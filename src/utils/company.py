"""Informations de l'entreprise affichées sur les rapports (nom, logo, coordonnées).

Le fichier company.json est créé à côté de l'application (ou de l'.exe) au premier
lancement. Il peut être modifié avec le Bloc-notes : les changements sont pris en
compte à la génération suivante d'un rapport.
"""

import json
from pathlib import Path

from src.utils.paths import data_dir, resource_path

DEFAULT_COMPANY = {
    "name": "Dépannage Informatique Plus",
    "tagline": "Rapport de diagnostic informatique",
    "phone": "",
    "email": "",
    "website": "",
    "address": "",
    # Chemin d'un logo personnalisé (png/jpg). Vide = logo DIP intégré.
    "logo": "",
}


def company_file() -> Path:
    return data_dir() / "company.json"


def load_company() -> dict:
    """Charge company.json (le crée avec les valeurs par défaut s'il n'existe pas)."""
    path = company_file()
    company = DEFAULT_COMPANY.copy()

    if not path.exists():
        try:
            path.write_text(
                json.dumps(DEFAULT_COMPANY, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass
        return company

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            company.update({k: str(v) for k, v in data.items() if k in DEFAULT_COMPANY})
    except (OSError, ValueError):
        pass
    return company


def logo_path(company: dict) -> Path:
    """Logo à utiliser : celui de company.json s'il existe, sinon le logo DIP."""
    custom = (company.get("logo") or "").strip()
    if custom and Path(custom).is_file():
        return Path(custom)
    return resource_path("assets/logo/logo-web-transparent.png")
