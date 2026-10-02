"""Interprétation des données collectées : voyants et recommandations.

Fonctions pures (aucune dépendance Qt, Windows ou reportlab) : faciles à tester.
Les seuils sont regroupés ici pour pouvoir être ajustés facilement.
"""

OK = "ok"
WARNING = "warning"
DANGER = "danger"
UNKNOWN = "unknown"

STATUS_LABELS = {
    OK: "Bon",
    WARNING: "À surveiller",
    DANGER: "Critique",
    UNKNOWN: "Non vérifié",
}

# --- Seuils ---------------------------------------------------------------
DISK_WARNING_PERCENT = 80
DISK_DANGER_PERCENT = 90
RAM_WARNING_PERCENT = 80
RAM_DANGER_PERCENT = 90
RAM_MIN_RECOMMENDED_GB = 8
CPU_WARNING_PERCENT = 90
UPTIME_WARNING_DAYS = 30

_COLOR_TO_STATUS = {"green": OK, "orange": WARNING, "red": DANGER}
_SEVERITY = {OK: 0, WARNING: 1, DANGER: 2}


def worst(statuses) -> str:
    """Pire statut d'une liste. UNKNOWN est ignoré sauf s'il n'y a rien d'autre."""
    known = [s for s in statuses if s in _SEVERITY]
    if known:
        return max(known, key=lambda s: _SEVERITY[s])
    return UNKNOWN


def _rec(level, text):
    return {"level": level, "text": text}


# --- Analyse par domaine ----------------------------------------------------

def disk_status(d: dict) -> str:
    """Statut d'un disque.

    * Disque système (celui de Windows) : OK / À surveiller (80 %) / Critique (90 %),
      car un disque système plein ralentit ou bloque le PC.
    * Disque de données (D:, etc.) : jamais « Critique », au pire « À surveiller ».
    * Disque amovible (clé USB, disque externe) : informatif, ne dégrade pas le verdict.
    Si on ne sait pas de quel type il s'agit, on le traite comme un disque système.
    """
    if d.get("removable"):
        return OK
    p = d["percent"]
    if p >= DISK_DANGER_PERCENT:
        return DANGER if d.get("is_system", True) else WARNING
    if p >= DISK_WARNING_PERCENT:
        return WARNING
    return OK


def disk_kind(d: dict) -> str:
    """Libellé court du type de disque pour le rapport."""
    if d.get("removable"):
        return "amovible"
    return "système" if d.get("is_system", True) else "données"


def analyze_disks(disks):
    if disks is None:
        return UNKNOWN, "Impossible de lire les disques.", []
    if not disks:
        return UNKNOWN, "Aucun disque détecté.", []

    statuses, recs = [], []

    for d in disks:
        st = disk_status(d)
        statuses.append(st)
        p = d["percent"]
        label = d.get("mount") or d.get("name", "?")
        base = f"Le disque {label} est rempli à {p} % ({d['free']} Go libres)"

        if st == DANGER:
            recs.append(_rec(DANGER,
                f"{base} : c'est le disque du système, il faut libérer de l'espace "
                "rapidement ou prévoir un disque plus grand."))
        elif st == WARNING:
            if d.get("is_system", True):
                recs.append(_rec(WARNING, f"{base} : un nettoyage est conseillé."))
            else:
                recs.append(_rec(WARNING,
                    f"{base} : ce n'est pas le disque système, mais pensez à faire "
                    "du tri ou à archiver des fichiers."))

    status = worst(statuses)

    counted = [d for d in disks if not d.get("removable")] or disks
    system_disks = [d for d in counted if d.get("is_system", True)]
    reference = max(system_disks or counted, key=lambda d: d["percent"])
    if status == OK:
        kind = "disque système" if system_disks else "disque le plus rempli"
        text = f"Espace suffisant ({kind} : {reference['percent']} %)."
    else:
        fullest = max(counted, key=lambda d: d["percent"])
        text = (f"Disque le plus rempli : {fullest['percent']} % "
                f"({fullest.get('mount') or fullest.get('name', '?')}).")
    return status, text, recs


def analyze_memory(system):
    if not system:
        return UNKNOWN, "Mémoire non vérifiée.", []

    p, total = system["ram_percent"], system["ram_total_gb"]
    recs, statuses = [], []

    if p >= RAM_DANGER_PERCENT:
        statuses.append(DANGER)
        recs.append(_rec(DANGER,
            f"La mémoire est utilisée à {p} % : fermer des applications ou ajouter de la RAM."))
    elif p >= RAM_WARNING_PERCENT:
        statuses.append(WARNING)
        recs.append(_rec(WARNING,
            f"La mémoire est utilisée à {p} % : surveiller les applications ouvertes."))
    else:
        statuses.append(OK)

    if total < RAM_MIN_RECOMMENDED_GB:
        statuses.append(WARNING)
        recs.append(_rec(WARNING,
            f"Le PC dispose de {total} Go de RAM : une extension à "
            f"{RAM_MIN_RECOMMENDED_GB} Go ou plus améliorerait nettement la fluidité."))

    status = worst(statuses)
    return status, f"{total} Go installés, {p} % utilisés.", recs


def analyze_cpu(system):
    if not system:
        return UNKNOWN, "Processeur non vérifié.", []

    p = system["cpu_percent"]
    if p >= CPU_WARNING_PERCENT:
        return WARNING, f"Charge élevée au moment de l'analyse ({p:.0f} %).", [
            _rec(WARNING,
                 f"Le processeur était très sollicité ({p:.0f} %) pendant l'analyse : "
                 "vérifier les programmes actifs ou lancés au démarrage.")]
    return OK, f"Charge normale ({p:.0f} %).", []


def analyze_system(system):
    """État général : version de Windows et durée depuis le dernier redémarrage."""
    if not system:
        return UNKNOWN, "Système non vérifié.", []

    statuses, recs = [], []
    name = system.get("os_name", "")

    # Windows 10 : fin de support le 14/10/2025 (mises à jour étendues payantes ensuite)
    if "Windows 10" in name:
        statuses.append(WARNING)
        recs.append(_rec(WARNING,
            "Windows 10 n'est plus supporté gratuitement par Microsoft depuis le "
            "14 octobre 2025 : prévoir le passage à Windows 11 (si le PC est "
            "compatible) ou étudier les mises à jour de sécurité étendues (payantes)."))

    days = system.get("uptime_days", 0)
    if days >= UPTIME_WARNING_DAYS:
        statuses.append(WARNING)
        recs.append(_rec(WARNING,
            f"Le PC n'a pas redémarré depuis {int(days)} jours : un redémarrage "
            "est conseillé pour appliquer les mises à jour et libérer la mémoire."))

    if not statuses:
        statuses.append(OK)
    status = worst(statuses)
    text = name if status == OK else f"{name} - points à vérifier."
    return status, text, recs


def analyze_network(network):
    if network is None:
        return UNKNOWN, "Réseau non vérifié.", []

    if not network["interfaces"]:
        return DANGER, "Aucune connexion réseau active.", [
            _rec(DANGER, "Aucune connexion réseau active détectée : vérifier le câble, "
                         "le Wi-Fi ou la box.")]
    if not network["internet"]:
        return WARNING, "Réseau local actif, mais Internet inaccessible.", [
            _rec(WARNING, "Le PC est connecté au réseau local mais n'accède pas à Internet : "
                          "vérifier la box et la configuration DNS.")]
    return OK, "Connecté à Internet.", []


def analyze_security(checks):
    if checks is None:
        return UNKNOWN, "Sécurité non vérifiée.", []
    if not checks:
        return UNKNOWN, "Aucune vérification de sécurité disponible.", []

    statuses, recs = [], []
    for c in checks:
        st = _COLOR_TO_STATUS.get(c.get("color"), UNKNOWN)
        statuses.append(st)
        if st in (WARNING, DANGER):
            recs.append(_rec(st, f"{c['title']} : {c['details']}"))

    status = worst(statuses)
    if status == OK:
        text = "Pare-feu, antivirus et contrôle de compte en ordre."
    else:
        text = "Au moins un point de sécurité à corriger."
    return status, text, recs


def analyze_printers(printers):
    if printers is None:
        return UNKNOWN, "Imprimantes non vérifiées.", []
    if not printers:
        return OK, "Aucune imprimante installée.", []

    offline = [p for p in printers if p.get("offline") or p.get("status") == "Hors ligne"]
    if offline:
        names = ", ".join(p["name"] for p in offline)
        return WARNING, f"{len(offline)} imprimante(s) hors ligne.", [
            _rec(WARNING, f"Imprimante(s) hors ligne : {names}. "
                          "Vérifier l'alimentation, le câble ou la connexion Wi-Fi.")]
    return OK, f"{len(printers)} imprimante(s) installée(s), en ligne.", []


# --- Synthèse globale -------------------------------------------------------

def analyze(data: dict, options: dict) -> dict:
    """Retourne {overall, verdict, summary[], recommendations[]}."""
    summary, recs = [], []

    def add(title, result):
        status, text, r = result
        summary.append({"title": title, "status": status, "text": text})
        recs.extend(r)

    add("Système", analyze_system(data["system"]))

    if options.get("include_system", True):
        add("Processeur", analyze_cpu(data["system"]))
        add("Mémoire", analyze_memory(data["system"]))
    if options.get("include_disks", True):
        add("Stockage", analyze_disks(data["disks"]))
    if options.get("include_network", True):
        add("Réseau", analyze_network(data["network"]))
    if options.get("include_security", True):
        add("Sécurité", analyze_security(data["security"]))
    if options.get("include_printers", True):
        add("Imprimantes", analyze_printers(data["printers"]))

    overall = worst([s["status"] for s in summary])
    recs.sort(key=lambda r: -_SEVERITY.get(r["level"], 0))

    verdicts = {
        OK: "L'ordinateur est en bon état.",
        WARNING: "Quelques points méritent votre attention.",
        DANGER: "Des problèmes nécessitent une intervention.",
        UNKNOWN: "L'état de l'ordinateur n'a pas pu être évalué.",
    }
    return {
        "overall": overall,
        "verdict": verdicts[overall],
        "summary": summary,
        "recommendations": recs,
    }
