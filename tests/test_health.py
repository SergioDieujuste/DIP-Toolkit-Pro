"""Tests de la santé matérielle, mises à jour et stabilité (sans PowerShell réel)."""

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.diagnostics import health_info as hi  # noqa: E402
from src.diagnostics import report_analysis as ra  # noqa: E402
from src.diagnostics import report_data  # noqa: E402
from src.diagnostics.report_info import HAS_REPORTLAB, ReportInfo  # noqa: E402
from src.utils import company  # noqa: E402
from src.utils.powershell import json_list, json_object, run_powershell  # noqa: E402

from tests.test_report import ALL, healthy_data  # noqa: E402

HEALTH_OPTS = dict(ALL, include_health=True, include_updates=True, include_events=True)


class TestPowershellHelpers(unittest.TestCase):

    def test_json_list_formes_de_powershell(self):
        self.assertEqual(json_list(""), [])                       # aucun résultat
        self.assertEqual(json_list('{"a":1}'), [{"a": 1}])        # un seul objet
        self.assertEqual(json_list('[{"a":1},{"a":2}]'), [{"a": 1}, {"a": 2}])
        self.assertEqual(json_list('[null]'), [])                 # @($null)
        self.assertEqual(json_object(''), {})

    def test_json_invalide_leve_valueerror(self):
        with self.assertRaises(ValueError):
            json_list("pas du json")

    def test_hors_windows_pas_de_plantage(self):
        with mock.patch("src.utils.powershell.platform.system", return_value="Linux"):
            ok, msg = run_powershell("Get-Date")
        self.assertFalse(ok)

    def test_collecteur_renvoie_none_si_echec(self):
        with mock.patch.object(hi, "run_powershell", return_value=(False, "refusé")):
            for fn in (hi.collect_disk_health, hi.collect_battery, hi.collect_updates,
                       hi.collect_problem_devices, hi.collect_events):
                self.assertIsNone(fn(), fn.__name__)

    def test_collecteur_renvoie_none_si_json_casse(self):
        with mock.patch.object(hi, "run_powershell", return_value=(True, "<<erreur>>")):
            self.assertIsNone(hi.collect_events())


class TestParsers(unittest.TestCase):

    def test_disques_ignore_usb_et_convertit(self):
        raw = json.loads(json.dumps([
            {"Name": "Samsung SSD 970", "Media": "SSD", "Bus": "NVMe", "Size": 500107862016,
             "Health": "Healthy", "Operational": "OK", "Wear": 3, "Temp": 41, "Hours": 4210,
             "ReadUncorrected": 0, "WriteUncorrected": 0},
            {"Name": "SanDisk Cruzer", "Media": "Unspecified", "Bus": "USB", "Size": 15e9,
             "Health": "Healthy"},
        ]))
        disks = hi.parse_disk_health(raw)
        self.assertEqual(len(disks), 1)
        self.assertEqual(disks[0]["size_gb"], 500)
        self.assertEqual(disks[0]["wear"], 3)

    def test_disques_valeurs_absentes(self):
        d = hi.parse_disk_health([{"Name": "HDD", "Media": "HDD", "Bus": "SATA",
                                   "Size": 1e12, "Health": "Healthy", "Wear": None}])[0]
        self.assertIsNone(d["wear"])
        self.assertEqual(d["errors"], 0)

    def test_batterie(self):
        self.assertEqual(hi.parse_battery({"Present": False}), {"present": False})
        self.assertEqual(hi.parse_battery({}), {"present": False})
        b = hi.parse_battery({"Present": True, "Charge": 88, "Status": 2,
                              "Full": 40000, "Design": 50000, "Cycles": 312})
        self.assertEqual(b["health_percent"], 80)
        self.assertTrue(b["on_ac"])
        self.assertIsNone(hi.parse_battery({"Present": True, "Charge": 50})["health_percent"])

    def test_mises_a_jour(self):
        obj = {"RebootPending": True, "Updates": [
            {"Title": "KB5001 sécurité", "Severity": "Critical", "Type": 1, "Categories": "X"},
            {"Title": "Pilote Intel", "Severity": "", "Type": 2, "Categories": "Pilotes"},
            {"Title": "Outil", "Severity": "", "Type": 1, "Categories": "Updates"},
        ]}
        up = hi.parse_updates(obj)
        self.assertTrue(up["reboot_pending"])
        self.assertEqual([u["is_driver"] for u in up["updates"]], [False, True, False])
        self.assertEqual([u["is_security"] for u in up["updates"]], [True, False, False])
        # Un seul objet (et non une liste) renvoyé par PowerShell
        up = hi.parse_updates({"RebootPending": False, "Updates": obj["Updates"][0]})
        self.assertEqual(len(up["updates"]), 1)

    def test_evenements(self):
        items = ([{"Id": 1001, "Provider": "BugCheck", "Level": 2}] * 2
                 + [{"Id": 41, "Provider": "Microsoft-Windows-Kernel-Power", "Level": 1}] * 3
                 + [{"Id": 6008, "Provider": "EventLog", "Level": 2}] * 2
                 + [{"Id": 10016, "Provider": "DCOM", "Level": 2}] * 40)
        ev = hi.parse_events(items)
        self.assertEqual(ev["bsod"], 2)
        self.assertEqual(ev["unexpected_shutdowns"], 3)   # max(41, 6008), pas la somme
        self.assertEqual(ev["critical"], 3)
        self.assertEqual(ev["top_sources"][0], {"name": "DCOM", "count": 40})


def disk_h(**over):
    d = {"name": "SSD", "media": "SSD", "bus": "NVMe", "size_gb": 512, "health": "Healthy",
         "operational": "OK", "wear": 5.0, "temp": 40.0, "hours": 1000.0, "errors": 0}
    d.update(over)
    return d


class TestAnalyseSante(unittest.TestCase):

    def test_disque_sain(self):
        self.assertEqual(ra.analyze_disk_health([disk_h()])[0], ra.OK)

    def test_disque_defectueux_est_critique(self):
        st, _, recs = ra.analyze_disk_health([disk_h(health="Unhealthy")])
        self.assertEqual(st, ra.DANGER)
        self.assertIn("sauvegarder", recs[0]["text"])

    def test_usure_ssd_et_temperature(self):
        self.assertEqual(ra.analyze_disk_health([disk_h(wear=85.0)])[0], ra.WARNING)
        self.assertEqual(ra.analyze_disk_health([disk_h(wear=95.0)])[0], ra.DANGER)
        self.assertEqual(ra.analyze_disk_health([disk_h(temp=70.0)])[0], ra.WARNING)
        self.assertEqual(ra.analyze_disk_health([disk_h(errors=3)])[0], ra.WARNING)

    def test_donnees_smart_absentes_ne_declenchent_rien(self):
        self.assertEqual(
            ra.analyze_disk_health([disk_h(wear=None, temp=None, hours=None)])[0], ra.OK)

    def test_batterie_jamais_critique(self):
        self.assertIsNone(ra.analyze_battery({"present": False}))
        self.assertEqual(ra.analyze_battery({"present": True, "health_percent": 92})[0], ra.OK)
        self.assertEqual(ra.analyze_battery({"present": True, "health_percent": 70})[0], ra.WARNING)
        self.assertEqual(ra.analyze_battery({"present": True, "health_percent": 30})[0], ra.WARNING)
        self.assertEqual(ra.analyze_battery({"present": True, "health_percent": None})[0], ra.UNKNOWN)
        self.assertEqual(ra.analyze_battery(None)[0], ra.UNKNOWN)

    def test_mises_a_jour(self):
        self.assertEqual(ra.analyze_updates({"reboot_pending": False, "updates": []})[0], ra.OK)
        self.assertEqual(ra.analyze_updates(None)[0], ra.UNKNOWN)
        up = hi.parse_updates({"RebootPending": True, "Updates": [
            {"Title": "a", "Severity": "Critical", "Type": 1, "Categories": ""},
            {"Title": "b", "Severity": "", "Type": 2, "Categories": ""}]})
        st, text, recs = ra.analyze_updates(up)
        self.assertEqual(st, ra.WARNING)
        self.assertIn("2 mises à jour", text)
        self.assertEqual(len(recs), 2)  # mises à jour + redémarrage
        one = ra.analyze_updates({"reboot_pending": False, "updates": [
            {"title": "a", "is_driver": False, "is_security": False}]})
        self.assertIn("1 mise à jour", one[1])

    def test_peripheriques_en_erreur(self):
        self.assertEqual(ra.analyze_drivers([])[0], ra.OK)
        st, _, recs = ra.analyze_drivers([{"name": "Carte Wi-Fi", "code": 28}])
        self.assertEqual(st, ra.WARNING)
        self.assertIn("Carte Wi-Fi", recs[0]["text"])

    def test_stabilite(self):
        calm = {"days": 7, "critical": 0, "errors": 120, "bsod": 0,
                "unexpected_shutdowns": 0, "top_sources": []}
        self.assertEqual(ra.analyze_events(calm)[0], ra.OK)  # 120 erreurs banales = normal
        st, text, recs = ra.analyze_events(dict(calm, bsod=1, unexpected_shutdowns=2))
        self.assertEqual(st, ra.WARNING)
        self.assertIn("1 écran bleu", text)
        self.assertIn("2 arrêts inattendus", text)

    def test_options_desactivees_par_defaut(self):
        titles = [s["title"] for s in ra.analyze(healthy_data(), ALL)["summary"]]
        for t in ("Santé des disques", "Batterie", "Mises à jour", "Pilotes", "Stabilité"):
            self.assertNotIn(t, titles)

    def test_pc_fixe_sans_batterie_masque_la_ligne(self):
        data = healthy_data()
        data.update(disk_health=[disk_h()], battery={"present": False},
                    updates={"reboot_pending": False, "updates": []},
                    problem_devices=[], events={"days": 7, "critical": 0, "errors": 0,
                                                "bsod": 0, "unexpected_shutdowns": 0,
                                                "top_sources": []})
        titles = [s["title"] for s in ra.analyze(data, HEALTH_OPTS)["summary"]]
        self.assertIn("Santé des disques", titles)
        self.assertNotIn("Batterie", titles)
        self.assertEqual(ra.analyze(data, HEALTH_OPTS)["overall"], ra.OK)


class TestCollecteParallele(unittest.TestCase):

    def test_seules_les_sections_demandees_sont_collectees(self):
        calls = []

        def fake(name):
            def f():
                calls.append(name)
                return name
            return f

        patches = {
            "collect_system": fake("system"), "collect_disks": fake("disks"),
            "collect_network": fake("network"), "collect_security": fake("security"),
            "collect_printers": fake("printers"),
        }
        with mock.patch.multiple(report_data, **patches), \
             mock.patch.object(hi, "collect_updates", fake("updates")), \
             mock.patch.object(hi, "collect_events", fake("events")), \
             mock.patch.object(hi, "collect_disk_health", fake("disk_health")):
            data = report_data.collect_all({"include_disks": False, "include_network": False,
                                            "include_security": False, "include_printers": False,
                                            "include_health": True})
        self.assertEqual(data["system"], "system")
        self.assertEqual(data["disk_health"], "disk_health")
        self.assertIsNone(data["disks"])
        self.assertIsNone(data["updates"])
        self.assertIsNone(data["events"])
        self.assertNotIn("updates", calls)

    def test_une_section_en_echec_ne_bloque_pas_les_autres(self):
        with mock.patch.object(hi, "collect_events", side_effect=RuntimeError("boom")), \
             mock.patch.object(hi, "collect_updates", return_value={"updates": [],
                                                                    "reboot_pending": False}), \
             mock.patch.object(hi, "collect_problem_devices", return_value=[]):
            data = report_data.collect_all({"include_disks": False, "include_network": False,
                                            "include_security": False, "include_printers": False,
                                            "include_updates": True, "include_events": True})
        self.assertIsNone(data["events"])
        self.assertEqual(data["updates"]["updates"], [])


@unittest.skipUnless(HAS_REPORTLAB, "reportlab non installé")
class TestPdfSante(unittest.TestCase):

    def test_pdf_complet_toutes_sections(self):
        data = healthy_data()
        data.update(
            disk_health=[disk_h(), disk_h(name="WD Blue HDD", media="HDD", health="Warning",
                                          wear=None, temp=None, hours=None)],
            battery={"present": True, "charge": 77, "on_ac": False, "health_percent": 64,
                     "full_mwh": 32000, "design_mwh": 50000, "cycles": 540},
            updates=hi.parse_updates({"RebootPending": True, "Updates": [
                {"Title": f"Mise à jour {i} & test", "Severity": "Critical" if i == 0 else "",
                 "Type": 2 if i == 1 else 1, "Categories": ""} for i in range(15)]}),
            problem_devices=[{"name": "Contrôleur <inconnu>", "code": 28}],
            events={"days": 7, "critical": 2, "errors": 90, "bsod": 1, "unexpected_shutdowns": 2,
                    "top_sources": []},
        )
        opts = dict(HEALTH_OPTS, client_name="Test", tech_name="T")
        analysis = ra.analyze(data, opts)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sante.pdf"
            ReportInfo.build_pdf(str(out), data, analysis, opts, dict(company.DEFAULT_COMPANY))
            self.assertTrue(out.read_bytes().startswith(b"%PDF"))
            Path("/tmp/sante_test.pdf").write_bytes(out.read_bytes())

    def test_pdf_sections_non_verifiees(self):
        data = healthy_data()
        data.update(disk_health=None, battery=None, updates=None, problem_devices=None, events=None)
        opts = dict(HEALTH_OPTS, client_name="Test")
        analysis = ra.analyze(data, opts)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "x.pdf"
            ReportInfo.build_pdf(str(out), data, analysis, opts, dict(company.DEFAULT_COMPANY))
            self.assertGreater(out.stat().st_size, 3000)


if __name__ == "__main__":
    unittest.main()
