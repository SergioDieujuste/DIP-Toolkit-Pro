"""Informations de l'entreprise affichées sur les rapports (nom, logo, coordonnées).

Le fichier company.json est créé à côté de l'application (ou de l'.exe) au premier
lancement. Il se modifie depuis Paramètres > Informations de l'entreprise, ou à la
main avec le Bloc-notes : les changements sont pris en compte au rapport suivant.

Un logo personnalisé est COPIÉ à côté de l'application (logo_entreprise.png/.jpg) :
il continue donc de fonctionner si l'image d'origine est déplacée, ou si la clé USB
change de lettre de lecteur.
"""

import json
import shutil
from pathlib import Path

from src.utils.paths import data_dir, resource_path

DEFAULT_COMPANY = {
    "name": "Dépannage Informatique Plus",
    "tagline": "Rapport de diagnostic informatique",
    "phone": "",
    "email": "",
    "website": "",
    "address": "",
    # Nom (ou chemin) d'un logo personnalisé. Vide = logo DIP intégré.
    "logo": "",
}

LOGO_COPY_NAME = "logo_entreprise"
LOGO_EXTENSIONS = (".png", ".jpg", ".jpeg")
LOGO_MAX_BYTES = 5 * 1024 * 1024


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
    if custom:
        candidate = Path(custom)
        if not candidate.is_absolute():
            candidate = data_dir() / custom
        if candidate.is_file():
            return candidate
    return resource_path("assets/logo/logo-web-transparent.png")


def _validate_logo(source: Path):
    """Retourne un message d'erreur, ou None si le logo est utilisable."""
    if not source.is_file():
        return "Le fichier du logo est introuvable."
    if source.suffix.lower() not in LOGO_EXTENSIONS:
        return "Format de logo non pris en charge : utilisez un fichier PNG ou JPG."
    if source.stat().st_size > LOGO_MAX_BYTES:
        return "Le logo est trop volumineux (5 Mo maximum)."
    try:
        from PIL import Image
        with Image.open(source) as img:
            img.verify()
    except ImportError:
        pass  # Pillow absent : on se contente des contrôles ci-dessus
    except Exception:
        return "Ce fichier n'est pas une image valide."
    return None


def _remove_logo_copies():
    folder = data_dir()
    for ext in LOGO_EXTENSIONS:
        old = folder / f"{LOGO_COPY_NAME}{ext}"
        try:
            old.unlink()
        except OSError:
            pass


def save_company(values: dict, logo_source=None) -> tuple[bool, str]:
    """Enregistre les informations de l'entreprise.

    values      : name, tagline, phone, email, website, address
    logo_source : None = ne pas toucher au logo actuel
                  ""   = revenir au logo DIP intégré
                  chemin = nouveau logo (copié à côté de l'application)
    """
    current = load_company()
    new = {k: str(values.get(k, current.get(k, ""))).strip() for k in DEFAULT_COMPANY
           if k != "logo"}

    if not new["name"]:
        return False, "Le nom de l'entreprise est obligatoire."
    if not new["tagline"]:
        new["tagline"] = DEFAULT_COMPANY["tagline"]

    new["logo"] = current.get("logo", "")

    if logo_source == "":
        _remove_logo_copies()
        new["logo"] = ""
    elif logo_source:
        source = Path(logo_source)
        error = _validate_logo(source)
        if error:
            return False, error
        try:
            target = data_dir() / f"{LOGO_COPY_NAME}{source.suffix.lower()}"
            if source.resolve() != target.resolve():
                _remove_logo_copies()
                shutil.copyfile(source, target)
            new["logo"] = target.name
        except OSError as exc:
            return False, f"Impossible de copier le logo : {exc}"

    try:
        company_file().write_text(json.dumps(new, indent=4, ensure_ascii=False),
                                  encoding="utf-8")
    except OSError as exc:
        return False, f"Impossible d'enregistrer : {exc}"
    return True, "Informations de l'entreprise enregistrées. Elles apparaîtront sur le prochain rapport."
