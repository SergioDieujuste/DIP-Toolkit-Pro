"""Tests : réglages de l'entreprise (logo copié) et historique des rapports."""

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.diagnostics import history  # noqa: E402
from src.diagnostics import report_analysis as ra  # noqa: E402
from src.diagnostics.report_info import HAS_REPORTLAB, ReportInfo  # noqa: E402
from src.utils import company  # noqa: E402

from tests.test_report import ALL, healthy_data  # noqa: E402

LOGO_PNG = ROOT / "assets" / "logo" / "logo-web-transparent.png"


class _TmpDataDir(unittest.TestCase):
    """Redirige le dossier de données vers un dossier temporaire."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        for module in (company, history):
            p = mock.patch.object(module, "data_dir", return_value=self.dir)
            p.start()
            self.addCleanup(p.stop)
        self.addCleanup(self._tmp.cleanup)


class TestSaveCompany(_TmpDataDir):

    def values(self, **over):
        v = {"name": "Ma Société", "tagline": "Bilan", "phone": " 01 02 ", "email": "a@b.fr",
             "website": "", "address": ""}
        v.update(over)
        return v

    def test_enregistre_et_recharge(self):
        ok, _ = company.save_company(self.values())
        self.assertTrue(ok)
        c = company.load_company()
        self.assertEqual((c["name"], c["phone"]), ("Ma Société", "01 02"))  # espaces retirés

    def test_nom_obligatoire(self):
        ok, msg = company.save_company(self.values(name="   "))
        self.assertFalse(ok)
        self.assertIn("obligatoire", msg)
        self.assertEqual(company.load_company()["name"], company.DEFAULT_COMPANY["name"])

    def test_titre_vide_reprend_le_defaut(self):
        company.save_company(self.values(tagline=""))
        self.assertEqual(company.load_company()["tagline"], company.DEFAULT_COMPANY["tagline"])

    def test_logo_copie_a_cote_de_lapplication(self):
        with tempfile.TemporaryDirectory() as other:
            src = Path(other) / "mon logo.png"
            src.write_bytes(LOGO_PNG.read_bytes())
            ok, msg = company.save_company(self.values(), str(src))
            self.assertTrue(ok, msg)
            self.assertTrue((self.dir / "logo_entreprise.png").exists())
            self.assertEqual(company.load_company()["logo"], "logo_entreprise.png")
        # L'image d'origine a disparu (dossier temporaire supprimé) : le logo marche encore
        self.assertEqual(company.logo_path(company.load_company()),
                         self.dir / "logo_entreprise.png")

    def test_logo_inchange_si_none(self):
        with tempfile.TemporaryDirectory() as other:
            src = Path(other) / "l.png"
            src.write_bytes(LOGO_PNG.read_bytes())
            company.save_company(self.values(), str(src))
        company.save_company(self.values(name="Autre nom"), None)
        self.assertEqual(company.load_company()["logo"], "logo_entreprise.png")

    def test_retour_au_logo_dip(self):
        with tempfile.TemporaryDirectory() as other:
            src = Path(other) / "l.png"
            src.write_bytes(LOGO_PNG.read_bytes())
            company.save_company(self.values(), str(src))
        company.save_company(self.values(), "")
        self.assertEqual(company.load_company()["logo"], "")
        self.assertFalse((self.dir / "logo_entreprise.png").exists())
        self.assertEqual(company.logo_path(company.load_company()), LOGO_PNG)

    def test_logo_invalides_refuses(self):
        with tempfile.TemporaryDirectory() as other:
            fake = Path(other) / "faux.png"
            fake.write_text("ceci n'est pas une image")
            self.assertFalse(company.save_company(self.values(), str(fake))[0])
            pdf = Path(other) / "doc.pdf"
            pdf.write_bytes(b"%PDF")
            self.assertIn("PNG ou JPG", company.save_company(self.values(), str(pdf))[1])
            self.assertIn("introuvable",
                          company.save_company(self.values(), str(Path(other) / "x.png"))[1])
        # Un échec ne doit pas modifier la configuration ni laisser de logo copié
        self.assertEqual(company.load_company()["logo"], "")
        self.assertEqual(list(self.dir.glob("logo_entreprise.*")), [])

    def test_logo_deplace_avec_la_cle_usb(self):
        """company.json stocke un nom relatif : il suit le dossier de l'application."""
        (self.dir / "logo_entreprise.png").write_bytes(LOGO_PNG.read_bytes())
        (self.dir / "company.json").write_text(json.dumps({"logo": "logo_entreprise.png"}))
        self.assertEqual(company.logo_path(company.load_company()),
                         self.dir / "logo_entreprise.png")


def make_entry(client="Dupont", hostname="PC1", date=None, **over):
    e = {"id": f"id{client}{hostname}", "date": (date or datetime(2026, 10, 2, 14, 30)).isoformat(),
         "client_name": client, "client_phone": "06", "client_email": "c@x.fr",
         "tech_name": "Serge", "hostname": hostname, "model": "ACME X1", "serial": "SN1",
         "overall": "ok", "verdict": "ok", "recommendations": 0,
         "filepath": "", "relpath": None}
    e.update(over)
    return e


class TestHistory(_TmpDataDir):

    def test_historique_vide(self):
        self.assertEqual(history.load_history(), [])

    def test_ajout_et_tri_du_plus_recent(self):
        d = datetime(2026, 10, 2, 12, 0)
        history.add_entry(make_entry("Ancien", date=d))
        history.add_entry(make_entry("Récent", date=d + timedelta(days=3)))
        history.add_entry(make_entry("Milieu", date=d + timedelta(days=1)))
        self.assertEqual([e["client_name"] for e in history.load_history()],
                         ["Récent", "Milieu", "Ancien"])

    def test_fichier_corrompu_est_mis_de_cote(self):
        (self.dir / "historique.json").write_text("{pas du json")
        self.assertEqual(history.load_history(), [])
        self.assertTrue(list(self.dir.glob("historique.corrompu_*.json")))
        history.add_entry(make_entry())  # on peut continuer à enregistrer
        self.assertEqual(len(history.load_history()), 1)

    def test_recherche(self):
        entries = [make_entry("Dupont", "PC-SALON"), make_entry("Martin", "PORTABLE-02")]
        self.assertEqual(len(history.search(entries, "")), 2)
        self.assertEqual([e["client_name"] for e in history.search(entries, "dup")], ["Dupont"])
        self.assertEqual([e["client_name"] for e in history.search(entries, "portable")], ["Martin"])
        self.assertEqual(history.search(entries, "inconnu"), [])

    def test_clients_connus_derniere_coordonnee(self):
        d = datetime(2026, 10, 2, 12, 0)
        history.add_entry(make_entry("Dupont", "A", date=d, client_phone="01 ancien"))
        history.add_entry(make_entry("Dupont", "B", date=d + timedelta(days=5), client_phone="01 nouveau"))
        history.add_entry(make_entry("Martin", "C", date=d))
        clients = history.known_clients()
        self.assertEqual([c["name"] for c in clients], ["Dupont", "Martin"])
        self.assertEqual(clients[0]["phone"], "01 nouveau")

    def test_normalisation_des_telephones(self):
        for written in ("06 12 34 56 78", "06.12.34.56.78", "0612345678",
                        "+33 6 12 34 56 78", "0033 6 12 34 56 78", " 06-12-34-56-78 "):
            self.assertEqual(history.normalize_phone(written), "0612345678", written)
        self.assertEqual(history.normalize_phone(None), "")
        self.assertEqual(history.normalize_phone("abc"), "")

    def test_retrouver_un_client_par_telephone_ou_email(self):
        d = datetime(2026, 10, 2, 12, 0)
        history.add_entry(make_entry("Dupont", "A", date=d,
                                     client_phone="06 12 34 56 78", client_email="Dupont@Mail.fr"))
        history.add_entry(make_entry("Martin", "B", date=d, client_phone="07 00 00 00 00",
                                     client_email="martin@mail.fr"))
        idx = history.contact_index()

        # Le téléphone se retrouve quelle que soit la façon de l'écrire
        for typed in ("0612345678", "+33 6 12 34 56 78", "06.12.34.56.78"):
            self.assertEqual(idx["by_phone"][history.normalize_phone(typed)]["name"], "Dupont")
        # L'e-mail se retrouve sans tenir compte des majuscules
        self.assertEqual(idx["by_email"]["dupont@mail.fr"]["name"], "Dupont")
        self.assertEqual(idx["by_name"]["martin"]["email"], "martin@mail.fr")
        # Suggestions affichées dans les trois listes
        self.assertEqual(idx["names"], ["Dupont", "Martin"])
        self.assertIn("06 12 34 56 78", idx["phones"])
        self.assertIn("Dupont@Mail.fr", idx["emails"])

    def test_ancien_numero_retrouve_toujours_le_client(self):
        d = datetime(2026, 10, 2, 12, 0)
        history.add_entry(make_entry("Dupont", "A", date=d, client_phone="06 11 11 11 11"))
        history.add_entry(make_entry("Dupont", "B", date=d + timedelta(days=9),
                                     client_phone="06 22 22 22 22"))
        idx = history.contact_index()
        client = idx["by_phone"][history.normalize_phone("06 11 11 11 11")]
        self.assertEqual(client["name"], "Dupont")
        self.assertEqual(client["phone"], "06 22 22 22 22")  # coordonnées les plus récentes

    def test_numeros_trop_courts_ou_vides_ignores(self):
        history.add_entry(make_entry("Dupont", "A", client_phone="112", client_email=""))
        idx = history.contact_index()
        self.assertEqual(idx["by_phone"], {})
        self.assertEqual(idx["by_email"], {})
        self.assertEqual(history.contact_index()["names"], ["Dupont"])

    def test_index_vide(self):
        idx = history.contact_index()
        self.assertEqual((idx["names"], idx["phones"], idx["emails"]), ([], [], []))

    def test_suppression_avec_ou_sans_pdf(self):
        pdf1, pdf2 = self.dir / "a.pdf", self.dir / "b.pdf"
        pdf1.write_bytes(b"%PDF"); pdf2.write_bytes(b"%PDF")
        history.add_entry(make_entry("A", filepath=str(pdf1)))
        history.add_entry(make_entry("B", filepath=str(pdf2)))
        self.assertTrue(history.delete_entry("idAPC1", delete_file=False))
        self.assertTrue(pdf1.exists())                       # PDF conservé
        self.assertTrue(history.delete_entry("idBPC1", delete_file=True))
        self.assertFalse(pdf2.exists())                      # PDF supprimé
        self.assertEqual(history.load_history(), [])
        self.assertFalse(history.delete_entry("inexistant"))

    def test_pdf_retrouve_apres_changement_de_lettre_de_lecteur(self):
        (self.dir / "rapports").mkdir()
        real = self.dir / "rapports" / "r.pdf"
        real.write_bytes(b"%PDF")
        entry = make_entry(filepath="E:\\ancienne\\lettre\\r.pdf", relpath="rapports/r.pdf")
        self.assertEqual(history.resolve_file(entry), real)
        self.assertIsNone(history.resolve_file(make_entry(filepath="Z:\\absent.pdf")))
        self.assertIsNone(history.resolve_file(make_entry(filepath="")))

    def test_noms_de_dossier_clients(self):
        self.assertEqual(history.safe_folder_name("Dupont & Fils"), "Dupont & Fils")
        self.assertEqual(history.safe_folder_name('Café: "Le/Bon" <Coin>?'), "Café Le Bon Coin")
        self.assertEqual(history.safe_folder_name("  ..Martin.. "), "Martin")
        self.assertEqual(history.safe_folder_name("CON"), "CON_")
        self.assertEqual(history.safe_folder_name("   "), "")
        self.assertLessEqual(len(history.safe_folder_name("x" * 200)), 60)

    def test_dossier_par_client(self):
        self.assertEqual(history.client_report_dir("C:/Rapports", "Dupont"),
                         Path("C:/Rapports") / "Dupont")
        self.assertEqual(history.client_report_dir("C:/Rapports", ""), Path("C:/Rapports"))
        self.assertEqual(history.client_report_dir("", "").name, "Documents")


@unittest.skipUnless(HAS_REPORTLAB, "reportlab non installé")
class TestEnregistrementAutomatique(_TmpDataDir):

    def opts(self):
        return dict(ALL, client_name="Dupont", client_phone="06 11", client_email="d@x.fr",
                    tech_name="Serge")

    def test_un_rapport_genere_est_enregistre(self):
        out = self.dir / "Dupont" / "r.pdf"
        out.parent.mkdir()
        with mock.patch("src.diagnostics.report_info.collect_all", return_value=healthy_data()), \
             mock.patch("src.diagnostics.report_info.load_company",
                        return_value=dict(company.DEFAULT_COMPANY)):
            ok, msg = ReportInfo.generate_pdf(str(out), self.opts())
        self.assertTrue(ok, msg)
        entries = history.load_history()
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual((e["client_name"], e["client_phone"], e["hostname"]),
                         ("Dupont", "06 11", "PC-TEST"))
        self.assertEqual(e["overall"], ra.OK)
        self.assertEqual(e["relpath"], str(Path("Dupont") / "r.pdf"))
        self.assertEqual(history.resolve_file(e), out.resolve())

    def test_echec_historique_ne_bloque_pas_le_rapport(self):
        out = self.dir / "r.pdf"
        with mock.patch("src.diagnostics.report_info.collect_all", return_value=healthy_data()), \
             mock.patch("src.diagnostics.report_info.load_company",
                        return_value=dict(company.DEFAULT_COMPANY)), \
             mock.patch.object(history, "record_report", side_effect=OSError("disque plein")):
            ok, msg = ReportInfo.generate_pdf(str(out), self.opts())
        self.assertTrue(ok, msg)
        self.assertTrue(out.exists())

    def test_rapport_en_echec_n_est_pas_enregistre(self):
        with mock.patch("src.diagnostics.report_info.collect_all", side_effect=PermissionError):
            ok, _ = ReportInfo.generate_pdf(str(self.dir / "x.pdf"), self.opts())
        self.assertFalse(ok)
        self.assertEqual(history.load_history(), [])


if __name__ == "__main__":
    unittest.main()
