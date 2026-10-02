"""Tests du rapport : analyse (voyants, recommandations) et génération du PDF."""

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.diagnostics import report_analysis as ra  # noqa: E402
from src.diagnostics.report_info import HAS_REPORTLAB, ReportInfo, default_filename  # noqa: E402
from src.utils import company  # noqa: E402

ALL = dict(include_system=True, include_disks=True, include_network=True,
           include_security=True, include_printers=True)


def sample_system(**over):
    s = {
        "hostname": "PC-TEST", "os_name": "Microsoft Windows 11 Pro", "os_version": "10.0.26100",
        "os_build": 26100, "architecture": "64bit", "manufacturer": "ACME", "model": "X1",
        "serial": "SN123", "bios": "1.0", "cpu_name": "CPU Test", "cpu_cores": 4,
        "cpu_threads": 8, "cpu_percent": 10.0, "ram_total_gb": 16.0, "ram_used_gb": 4.0,
        "ram_percent": 25, "uptime_days": 2.0,
    }
    s.update(over)
    return s


def disk(percent, mount="C:\\", is_system=True, removable=False):
    total = 500.0
    used = round(total * percent / 100, 1)
    return {"name": mount, "mount": mount, "filesystem": "NTFS", "total": total,
            "used": used, "free": round(total - used, 1), "percent": percent,
            "is_system": is_system, "removable": removable}


def healthy_data():
    return {
        "generated_at": datetime(2026, 10, 2, 14, 30),
        "system": sample_system(),
        "disks": [disk(40)],
        "network": {"interfaces": [{"name": "Wi-Fi", "ip": "192.168.1.5", "mac": "AA:BB"}],
                    "internet": True},
        "security": [{"title": "Pare-feu Windows", "status": "OK", "color": "green",
                      "details": "ok"}],
        "printers": [],
    }


class TestAnalysis(unittest.TestCase):

    def test_pc_sain_tout_vert(self):
        a = ra.analyze(healthy_data(), ALL)
        self.assertEqual(a["overall"], ra.OK)
        self.assertEqual(a["recommendations"], [])

    def test_seuils_disque(self):
        self.assertEqual(ra.analyze_disks([disk(79)])[0], ra.OK)
        self.assertEqual(ra.analyze_disks([disk(80)])[0], ra.WARNING)
        self.assertEqual(ra.analyze_disks([disk(90)])[0], ra.DANGER)
        status, _, recs = ra.analyze_disks([disk(40), disk(94, "D:\\")])
        self.assertEqual(status, ra.DANGER)  # D: sans info "données" = traité comme système
        self.assertIn("D:\\", recs[0]["text"])

    def test_disque_de_donnees_plein_nest_jamais_critique(self):
        """Cas réel : C: (système) à l'aise, D: (données) presque plein."""
        disks = [disk(40, "C:\\"), disk(94, "D:\\", is_system=False)]
        status, text, recs = ra.analyze_disks(disks)
        self.assertEqual(status, ra.WARNING)
        self.assertEqual(recs[0]["level"], ra.WARNING)
        self.assertIn("pas le disque système", recs[0]["text"])
        # et le verdict global reste orange, pas rouge
        data = healthy_data()
        data["disks"] = disks
        self.assertEqual(ra.analyze(data, ALL)["overall"], ra.WARNING)

    def test_disque_systeme_plein_reste_critique(self):
        disks = [disk(95, "C:\\"), disk(10, "D:\\", is_system=False)]
        status, _, recs = ra.analyze_disks(disks)
        self.assertEqual(status, ra.DANGER)
        self.assertIn("disque du système", recs[0]["text"])

    def test_disque_amovible_ignore(self):
        disks = [disk(40, "C:\\"), disk(99, "E:\\", is_system=False, removable=True)]
        status, text, recs = ra.analyze_disks(disks)
        self.assertEqual(status, ra.OK)
        self.assertEqual(recs, [])
        self.assertIn("40 %", text)

    def test_libelles_type_disque(self):
        self.assertEqual(ra.disk_kind(disk(10)), "système")
        self.assertEqual(ra.disk_kind(disk(10, is_system=False)), "données")
        self.assertEqual(ra.disk_kind(disk(10, removable=True)), "amovible")

    def test_seuils_memoire_et_ram_faible(self):
        self.assertEqual(ra.analyze_memory(sample_system(ram_percent=95))[0], ra.DANGER)
        self.assertEqual(ra.analyze_memory(sample_system(ram_percent=85))[0], ra.WARNING)
        status, _, recs = ra.analyze_memory(sample_system(ram_total_gb=4.0))
        self.assertEqual(status, ra.WARNING)
        self.assertTrue(recs)

    def test_windows_10_et_uptime(self):
        status, _, recs = ra.analyze_system(sample_system(os_name="Microsoft Windows 10 Pro"))
        self.assertEqual(status, ra.WARNING)
        self.assertTrue(any("Windows 10" in r["text"] for r in recs))
        status, _, _ = ra.analyze_system(sample_system(uptime_days=45))
        self.assertEqual(status, ra.WARNING)
        self.assertEqual(ra.analyze_system(sample_system())[0], ra.OK)

    def test_reseau(self):
        self.assertEqual(ra.analyze_network({"interfaces": [], "internet": False})[0], ra.DANGER)
        self.assertEqual(
            ra.analyze_network({"interfaces": [{"name": "x", "ip": "1.1.1.1", "mac": ""}],
                                "internet": False})[0], ra.WARNING)

    def test_securite_et_imprimantes(self):
        checks = [{"title": "UAC", "status": "Danger", "color": "red", "details": "désactivé"}]
        status, _, recs = ra.analyze_security(checks)
        self.assertEqual(status, ra.DANGER)
        self.assertIn("UAC", recs[0]["text"])
        printers = [{"name": "HP", "offline": True, "status": "Hors ligne"}]
        self.assertEqual(ra.analyze_printers(printers)[0], ra.WARNING)

    def test_section_non_verifiee_ne_gache_pas_le_verdict(self):
        data = healthy_data()
        data["security"] = None  # PowerShell en échec, par exemple
        a = ra.analyze(data, ALL)
        self.assertEqual(a["overall"], ra.OK)
        self.assertIn(ra.UNKNOWN, [s["status"] for s in a["summary"]])

    def test_options_desactivees_masquent_les_sections(self):
        a = ra.analyze(healthy_data(), dict(ALL, include_security=False, include_printers=False))
        titles = [s["title"] for s in a["summary"]]
        self.assertNotIn("Sécurité", titles)
        self.assertNotIn("Imprimantes", titles)

    def test_recommandations_triees_par_gravite(self):
        data = healthy_data()
        data["system"] = sample_system(uptime_days=60)
        data["disks"] = [disk(95)]
        levels = [r["level"] for r in ra.analyze(data, ALL)["recommendations"]]
        self.assertEqual(levels[0], ra.DANGER)


@unittest.skipUnless(HAS_REPORTLAB, "reportlab non installé")
class TestPdf(unittest.TestCase):

    def test_pdf_genere_avec_caracteres_speciaux(self):
        data = healthy_data()
        data["disks"] = [disk(94)]
        data["printers"] = [{"name": "HP <Laser> & Co", "driver": "x", "port": "USB001",
                             "is_default": True, "offline": True, "status": "Hors ligne"}]
        opts = dict(ALL, client_name="Dupont & Fils <SARL>", client_phone="06 00 00 00 00",
                    client_email="a@b.fr", tech_name="Serge")
        analysis = ra.analyze(data, opts)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "r.pdf"
            ReportInfo.build_pdf(str(out), data, analysis, opts, dict(company.DEFAULT_COMPANY))
            raw = out.read_bytes()
            self.assertTrue(raw.startswith(b"%PDF"))
            self.assertGreater(len(raw), 5000)

    def test_generate_pdf_de_bout_en_bout(self):
        """Collecte -> analyse -> PDF, avec la collecte simulée (portable Linux/Windows)."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "r.pdf"
            with mock.patch("src.diagnostics.report_info.collect_all",
                            return_value=healthy_data()), \
                 mock.patch("src.diagnostics.report_info.load_company",
                            return_value=dict(company.DEFAULT_COMPANY)):
                ok, msg = ReportInfo.generate_pdf(str(out), dict(ALL, client_name="X"))
            self.assertTrue(ok, msg)
            self.assertTrue(out.exists())

    def test_erreur_ecriture_message_clair(self):
        with mock.patch("src.diagnostics.report_info.collect_all", side_effect=PermissionError):
            ok, msg = ReportInfo.generate_pdf("x.pdf", ALL)
        self.assertFalse(ok)
        self.assertIn("déjà ouvert", msg)


class TestCollecteDisques(unittest.TestCase):

    def test_repere_disque_systeme_windows(self):
        from src.diagnostics import report_data
        fake = [
            {"name": "C:\\", "mount": "C:\\", "filesystem": "NTFS", "total": 100.0,
             "used": 50.0, "free": 50.0, "percent": 50, "removable": False},
            {"name": "D:\\", "mount": "D:\\", "filesystem": "NTFS", "total": 900.0,
             "used": 850.0, "free": 50.0, "percent": 94, "removable": False},
        ]
        with mock.patch.object(report_data.platform, "system", return_value="Windows"), \
             mock.patch.dict(report_data.os.environ, {"SystemDrive": "C:"}), \
             mock.patch.object(report_data, "get_disks", return_value=fake):
            disks = report_data.collect_disks()
        self.assertEqual([d["is_system"] for d in disks], [True, False])


class TestNomsEtConfig(unittest.TestCase):

    def test_nom_de_fichier_horodate(self):
        name = default_filename("Dupont", "PC DUPONT/1")
        self.assertRegex(name, r"^Rapport_PC_DUPONT_1_\d{8}_\d{4}\.pdf$")

    def test_company_json_cree_et_modifiable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(company, "data_dir", return_value=Path(tmp)):
                c = company.load_company()
                self.assertEqual(c["name"], "Dépannage Informatique Plus")
                f = Path(tmp) / "company.json"
                self.assertTrue(f.exists())
                f.write_text(json.dumps({"name": "Ma Société", "phone": "01"}), encoding="utf-8")
                c = company.load_company()
                self.assertEqual((c["name"], c["phone"]), ("Ma Société", "01"))
                f.write_text("{pas du json", encoding="utf-8")  # fichier cassé -> défauts
                self.assertEqual(company.load_company()["name"], "Dépannage Informatique Plus")

    def test_logo_par_defaut(self):
        self.assertTrue(company.logo_path({"logo": ""}).exists())
        self.assertTrue(company.logo_path({"logo": "C:/introuvable.png"}).exists())


if __name__ == "__main__":
    unittest.main()
