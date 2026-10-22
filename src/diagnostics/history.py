"""Historique des rapports générés (historique.json, à côté de l'application).

Chaque rapport PDF créé est enregistré ici : date, client, poste, verdict, emplacement.
Ce fichier contient des données de clients (noms, téléphones) : sur une clé USB
transportée chez des clients, pensez à la chiffrer (BitLocker).
"""

import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path

from src.utils.paths import data_dir

_lock = threading.Lock()

_FORBIDDEN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                   *(f"LPT{i}" for i in range(1, 10))}


def history_file() -> Path:
    return data_dir() / "historique.json"


# --------------------------------------------------------------------------
# Lecture / écriture
# --------------------------------------------------------------------------
def _read() -> list:
    path = history_file()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError:
        return []
    except ValueError:
        # Fichier abîmé : on le met de côté au lieu de l'écraser en silence
        try:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.replace(path, path.with_name(f"historique.corrompu_{stamp}.json"))
        except OSError:
            pass
        return []
    return [e for e in data if isinstance(e, dict)] if isinstance(data, list) else []


def _write(entries: list):
    path = history_file()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)  # remplacement atomique : jamais de fichier à moitié écrit


def load_history() -> list:
    """Tous les rapports, du plus récent au plus ancien."""
    with _lock:
        entries = _read()
    return sorted(entries, key=lambda e: e.get("date", ""), reverse=True)


# --------------------------------------------------------------------------
# Enregistrement d'un rapport
# --------------------------------------------------------------------------
def build_entry(filepath, data: dict, analysis: dict, options: dict) -> dict:
    system = data.get("system") or {}
    absolute = Path(filepath).resolve()

    # Chemin relatif au dossier de l'application : survit au changement de lettre
    # de lecteur d'une clé USB.
    try:
        relative = str(absolute.relative_to(data_dir().resolve()))
    except ValueError:
        relative = None

    return {
        "id": uuid.uuid4().hex[:10],
        "date": data["generated_at"].isoformat(timespec="seconds"),
        "client_name": options.get("client_name") or "Client",
        "client_phone": options.get("client_phone", ""),
        "client_email": options.get("client_email", ""),
        "tech_name": options.get("tech_name", ""),
        "hostname": system.get("hostname", ""),
        "model": " ".join(x for x in (system.get("manufacturer"), system.get("model")) if x),
        "serial": system.get("serial", ""),
        "overall": analysis["overall"],
        "verdict": analysis["verdict"],
        "recommendations": len(analysis["recommendations"]),
        "filepath": str(absolute),
        "relpath": relative,
    }


def add_entry(entry: dict):
    with _lock:
        entries = _read()
        entries.append(entry)
        _write(entries)


def record_report(filepath, data, analysis, options) -> dict:
    entry = build_entry(filepath, data, analysis, options)
    add_entry(entry)
    return entry


# --------------------------------------------------------------------------
# Consultation
# --------------------------------------------------------------------------
def resolve_file(entry: dict):
    """Chemin réel du PDF, ou None s'il a été déplacé ou supprimé."""
    path = Path(entry.get("filepath", ""))
    if entry.get("filepath") and path.is_file():
        return path
    if entry.get("relpath"):
        candidate = data_dir() / entry["relpath"]
        if candidate.is_file():
            return candidate
    return None


def search(entries: list, text: str) -> list:
    text = (text or "").strip().lower()
    if not text:
        return entries
    keys = ("client_name", "hostname", "tech_name", "model", "serial", "client_phone")
    return [e for e in entries
            if any(text in str(e.get(k, "")).lower() for k in keys)]


def known_clients() -> list:
    """Clients déjà vus, avec leurs dernières coordonnées (pour l'auto-complétion)."""
    seen = {}
    for e in load_history():  # du plus récent au plus ancien : le premier trouvé gagne
        name = (e.get("client_name") or "").strip()
        if name and name.lower() not in seen:
            seen[name.lower()] = {"name": name,
                                  "phone": e.get("client_phone", ""),
                                  "email": e.get("client_email", "")}
    return sorted(seen.values(), key=lambda c: c["name"].lower())


def normalize_phone(text) -> str:
    """Ne garde que les chiffres, et ramène +33 / 0033 au format national (06 12... = 0612...).

    Permet de reconnaître un même numéro écrit « 06 12 34 56 78 », « 06.12.34.56.78 »
    ou « +33 6 12 34 56 78 ».
    """
    digits = "".join(ch for ch in str(text or "") if ch.isdigit())
    if digits.startswith("0033"):
        digits = "0" + digits[4:]
    elif digits.startswith("33") and len(digits) == 11:
        digits = "0" + digits[2:]
    return digits


MIN_PHONE_DIGITS = 6  # en dessous, trop de risques de confondre deux clients


def contact_index() -> dict:
    """Tout ce qu'il faut pour pré-remplir le formulaire à partir d'un nom, d'un
    téléphone ou d'un e-mail déjà connus.

    Retourne {names, phones, emails, by_name, by_phone, by_email} :
    * names / phones / emails : suggestions à afficher (dernières coordonnées de chaque client)
    * by_* : recherche d'un client à partir de la valeur saisie (nom en minuscules,
      téléphone normalisé, e-mail en minuscules). Les anciens numéros et e-mails d'un
      client le retrouvent aussi.
    """
    clients = known_clients()
    by_name = {c["name"].lower(): c for c in clients}
    by_phone, by_email = {}, {}

    for e in load_history():  # du plus récent au plus ancien
        client = by_name.get((e.get("client_name") or "").strip().lower())
        if client is None:
            continue
        phone = normalize_phone(e.get("client_phone"))
        if len(phone) >= MIN_PHONE_DIGITS and phone not in by_phone:
            by_phone[phone] = client
        email = (e.get("client_email") or "").strip().lower()
        if email and email not in by_email:
            by_email[email] = client

    return {
        "names": [c["name"] for c in clients],
        "phones": sorted({c["phone"] for c in clients if c["phone"]}),
        "emails": sorted({c["email"] for c in clients if c["email"]}, key=str.lower),
        "by_name": by_name,
        "by_phone": by_phone,
        "by_email": by_email,
    }


def delete_entry(entry_id: str, delete_file: bool = False) -> bool:
    """Retire un rapport de l'historique (et, si demandé, supprime son PDF)."""
    with _lock:
        entries = _read()
        target = next((e for e in entries if e.get("id") == entry_id), None)
        if target is None:
            return False
        _write([e for e in entries if e.get("id") != entry_id])

    if delete_file:
        pdf = resolve_file(target)
        if pdf is not None:
            try:
                pdf.unlink()
            except OSError:
                pass
    return True


# --------------------------------------------------------------------------
# Classement par client
# --------------------------------------------------------------------------
def safe_folder_name(name: str) -> str:
    """Nom de dossier valide sous Windows à partir d'un nom de client ('' si vide)."""
    cleaned = _FORBIDDEN_CHARS.sub(" ", name or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")[:60].strip(" .")
    if cleaned.upper() in _RESERVED_NAMES:
        cleaned += "_"
    return cleaned


def client_report_dir(base_dir: str, client_name: str) -> Path:
    """<dossier d'export>/<Nom du client>, ou le dossier d'export si pas de client."""
    base = Path(base_dir) if base_dir else Path.home() / "Documents"
    folder = safe_folder_name(client_name)
    return base / folder if folder else base
