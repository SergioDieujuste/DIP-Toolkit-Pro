"""Santé matérielle et logicielle : disques (SMART), batterie, mises à jour Windows,
périphériques en erreur et plantages récents.

Chaque collecteur renvoie None si la vérification est impossible (droits, réseau,
PowerShell absent...). Les fonctions parse_* sont pures et testables sans Windows.
"""

import json

from src.utils.powershell import json_list, json_object, run_powershell

# --------------------------------------------------------------------------
# Scripts PowerShell
# --------------------------------------------------------------------------
_DISK_HEALTH_SCRIPT = r"""
$out = foreach ($d in Get-PhysicalDisk) {
  $r = $d | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue
  [pscustomobject]@{
    Name=[string]$d.FriendlyName; Media=[string]$d.MediaType; Bus=[string]$d.BusType;
    Size=[double]$d.Size; Health=[string]$d.HealthStatus;
    Operational=[string]($d.OperationalStatus -join ',');
    Wear=$r.Wear; Temp=$r.Temperature; Hours=$r.PowerOnHours;
    ReadUncorrected=$r.ReadErrorsUncorrected; WriteUncorrected=$r.WriteErrorsUncorrected
  }
}
@($out) | ConvertTo-Json -Compress
"""

_BATTERY_SCRIPT = r"""
$b = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $b) { '{"Present":false}' } else {
  $full = Get-CimInstance -Namespace root\wmi -ClassName BatteryFullChargedCapacity -ErrorAction SilentlyContinue | Select-Object -First 1
  $stat = Get-CimInstance -Namespace root\wmi -ClassName BatteryStaticData -ErrorAction SilentlyContinue | Select-Object -First 1
  $cyc  = Get-CimInstance -Namespace root\wmi -ClassName BatteryCycleCount -ErrorAction SilentlyContinue | Select-Object -First 1
  [pscustomobject]@{
    Present=$true; Charge=$b.EstimatedChargeRemaining; Status=$b.BatteryStatus;
    Full=$full.FullChargedCapacity; Design=$stat.DesignedCapacity; Cycles=$cyc.CycleCount
  } | ConvertTo-Json -Compress
}
"""

_UPDATES_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$rp = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired') -or (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending')
$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()
$res = $searcher.Search('IsInstalled=0 and IsHidden=0')
$ups = @()
foreach ($u in $res.Updates) {
  $cats = @(); foreach ($c in $u.Categories) { $cats += $c.Name }
  $ups += [pscustomobject]@{ Title=[string]$u.Title; Severity=[string]$u.MsrcSeverity; Type=[int]$u.Type; Categories=($cats -join ', ') }
}
[pscustomobject]@{ RebootPending=$rp; Updates=$ups } | ConvertTo-Json -Depth 4 -Compress
"""

_DRIVERS_SCRIPT = r"""
@(Get-CimInstance Win32_PnPEntity -ErrorAction SilentlyContinue |
  Where-Object { $_.ConfigManagerErrorCode -ne 0 -and $_.ConfigManagerErrorCode -ne 22 } |
  ForEach-Object { [pscustomobject]@{ Name=[string]$_.Name; Code=[int]$_.ConfigManagerErrorCode } }) |
  ConvertTo-Json -Compress
"""

EVENT_DAYS = 7

_EVENTS_SCRIPT = rf"""
$since = (Get-Date).AddDays(-{EVENT_DAYS})
@(Get-WinEvent -FilterHashtable @{{LogName='System'; Level=1,2; StartTime=$since}} -MaxEvents 3000 -ErrorAction SilentlyContinue |
  ForEach-Object {{ [pscustomobject]@{{ Id=[int]$_.Id; Provider=[string]$_.ProviderName; Level=[int]$_.Level }} }}) |
  ConvertTo-Json -Compress
"""


# --------------------------------------------------------------------------
# Utilitaires
# --------------------------------------------------------------------------
def _num(value, default=None):
    """Convertit en nombre ; renvoie `default` si la valeur est absente ou invalide."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------
# Disques (SMART)
# --------------------------------------------------------------------------
def parse_disk_health(items: list) -> list:
    disks = []
    for it in items:
        bus = str(it.get("Bus", ""))
        if bus.upper() == "USB":  # clés et disques externes : ignorés (comme dans le stockage)
            continue
        size = _num(it.get("Size"), 0.0)
        disks.append({
            "name": str(it.get("Name") or "Disque").strip(),
            "media": str(it.get("Media", "")),
            "bus": bus,
            "size_gb": round(size / 1000**3),  # taille « commerciale » (500, 1000 Go...)
            "health": str(it.get("Health", "")),
            "operational": str(it.get("Operational", "")),
            "wear": _num(it.get("Wear")),
            "temp": _num(it.get("Temp")),
            "hours": _num(it.get("Hours")),
            "errors": int((_num(it.get("ReadUncorrected"), 0) or 0)
                          + (_num(it.get("WriteUncorrected"), 0) or 0)),
        })
    return disks


def collect_disk_health():
    ok, out = run_powershell(_DISK_HEALTH_SCRIPT, timeout=45)
    if not ok:
        return None
    try:
        return parse_disk_health(json_list(out))
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Batterie
# --------------------------------------------------------------------------
def parse_battery(obj: dict) -> dict:
    if not obj or not obj.get("Present"):
        return {"present": False}

    full, design = _num(obj.get("Full")), _num(obj.get("Design"))
    health = None
    if full and design and design > 0:
        health = max(0, min(100, round(full / design * 100)))

    status = obj.get("Status")
    # BatteryStatus : 1 = sur batterie, 2 = sur secteur, 3-5 = chargée/faible/critique, 6-9 = en charge
    on_ac = _num(status) in (2, 3, 6, 7, 8, 9)

    return {
        "present": True,
        "charge": _num(obj.get("Charge")),
        "on_ac": on_ac,
        "health_percent": health,
        "full_mwh": full,
        "design_mwh": design,
        "cycles": _num(obj.get("Cycles")),
    }


def collect_battery():
    ok, out = run_powershell(_BATTERY_SCRIPT, timeout=30)
    if not ok:
        return None
    try:
        return parse_battery(json_object(out))
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Mises à jour Windows
# --------------------------------------------------------------------------
def parse_updates(obj: dict) -> dict:
    updates = []
    raw = obj.get("Updates") or []
    if isinstance(raw, dict):
        raw = [raw]
    for u in raw:
        if not isinstance(u, dict):
            continue
        severity = str(u.get("Severity", "")).strip().lower()
        cats = str(u.get("Categories", ""))
        is_driver = _num(u.get("Type")) == 2  # 1 = logiciel, 2 = pilote (indépendant de la langue)
        is_security = severity in ("critical", "important") or \
            "security" in cats.lower() or "sécurité" in cats.lower()
        updates.append({
            "title": str(u.get("Title", "")).strip(),
            "is_driver": is_driver,
            "is_security": is_security and not is_driver,
        })
    return {"reboot_pending": bool(obj.get("RebootPending")), "updates": updates}


def collect_updates():
    # La recherche interroge les serveurs Microsoft : 20 à 90 s selon la connexion.
    ok, out = run_powershell(_UPDATES_SCRIPT, timeout=150)
    if not ok:
        return None
    try:
        return parse_updates(json_object(out))
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Pilotes / périphériques en erreur
# --------------------------------------------------------------------------
def parse_problem_devices(items: list) -> list:
    return [{"name": str(i.get("Name") or "Périphérique inconnu").strip(),
             "code": int(_num(i.get("Code"), 0) or 0)} for i in items]


def collect_problem_devices():
    ok, out = run_powershell(_DRIVERS_SCRIPT, timeout=45)
    if not ok:
        return None
    try:
        return parse_problem_devices(json_list(out))
    except ValueError:
        return None


# --------------------------------------------------------------------------
# Journal d'événements (plantages récents)
# --------------------------------------------------------------------------
_BSOD_PROVIDERS = ("bugcheck", "microsoft-windows-wer-systemerrorreporting")


def parse_events(items: list) -> dict:
    bsod = kernel_power = dirty_shutdown = 0
    critical = errors = 0
    sources = {}

    for e in items:
        eid = int(_num(e.get("Id"), 0) or 0)
        provider = str(e.get("Provider", ""))
        level = int(_num(e.get("Level"), 0) or 0)

        if level == 1:
            critical += 1
        else:
            errors += 1
        sources[provider] = sources.get(provider, 0) + 1

        if eid == 1001 and provider.lower() in _BSOD_PROVIDERS:
            bsod += 1
        elif eid == 41 and provider.lower() == "microsoft-windows-kernel-power":
            kernel_power += 1
        elif eid == 6008 and provider.lower() == "eventlog":
            dirty_shutdown += 1

    top = sorted(sources.items(), key=lambda kv: -kv[1])[:5]
    return {
        "days": EVENT_DAYS,
        "critical": critical,
        "errors": errors,
        "bsod": bsod,
        # Kernel-Power 41 et EventLog 6008 décrivent le même incident : on prend le plus élevé
        "unexpected_shutdowns": max(kernel_power, dirty_shutdown),
        "top_sources": [{"name": n, "count": c} for n, c in top],
    }


def collect_events():
    ok, out = run_powershell(_EVENTS_SCRIPT, timeout=60)
    if not ok:
        return None
    try:
        return parse_events(json_list(out))
    except ValueError:
        return None


if __name__ == "__main__":
    # Outil de dépannage : python -m src.diagnostics.health_info
    for fn in (collect_disk_health, collect_battery, collect_problem_devices,
               collect_events, collect_updates):
        print(f"\n=== {fn.__name__} ===")
        print(json.dumps(fn(), indent=2, ensure_ascii=False))
