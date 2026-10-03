"""Exécution de commandes PowerShell et lecture de leur résultat JSON.

* Pas de fenêtre noire qui clignote (CREATE_NO_WINDOW), même dans l'.exe sans console.
* Sortie forcée en UTF-8 pour garder les accents.
* Jamais d'exception : on renvoie (False, message) en cas de problème.
"""

import json
import platform
import subprocess

_PREFIX = (
    "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
    "$ProgressPreference='SilentlyContinue'; "
)


def run_powershell(script: str, timeout: int = 30):
    """Lance un script PowerShell. Retourne (ok, sortie_texte_ou_message_erreur)."""
    if platform.system() != "Windows":
        return False, "PowerShell Windows indisponible sur ce système."

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", _PREFIX + script],
            capture_output=True, timeout=timeout, creationflags=flags,
        )
    except subprocess.TimeoutExpired:
        return False, f"Délai dépassé ({timeout} s)."
    except OSError as exc:
        return False, str(exc)

    out = res.stdout.decode("utf-8", errors="replace").strip()
    err = res.stderr.decode("utf-8", errors="replace").strip()
    if res.returncode != 0:
        return False, err or out or f"Code de retour {res.returncode}."
    return True, out


def json_list(text: str) -> list:
    """Convertit la sortie JSON de PowerShell en liste de dictionnaires.

    PowerShell renvoie : rien (aucun résultat), un objet seul, ou une liste.
    Les éléments null sont ignorés.
    """
    text = (text or "").strip()
    if not text:
        return []
    data = json.loads(text)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def json_object(text: str) -> dict:
    """Comme json_list mais pour un résultat attendu sous forme d'un seul objet."""
    text = (text or "").strip()
    if not text:
        return {}
    data = json.loads(text)
    return data if isinstance(data, dict) else {}
