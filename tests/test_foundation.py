"""Tests de démarrage : vérifient le socle sans lancer l'interface.

Lancer depuis la racine du projet :
    python -m unittest discover -s tests -v
"""

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils import paths  # noqa: E402


class TestPaths(unittest.TestCase):

    def test_ressources_embarquees_presentes(self):
        for rel in (
            "assets/logo/logo-web-transparent.png",
            "assets/logo/app.ico",
            "assets/themes/dip.qss",
            "assets/icons/layout-dashboard.svg",
        ):
            self.assertTrue(paths.resource_path(rel).exists(), rel)

    def test_resource_path_independant_du_dossier_courant(self):
        import os
        old = os.getcwd()
        try:
            os.chdir(tempfile.gettempdir())
            self.assertTrue(
                paths.resource_path("assets/logo/logo-web-transparent.png").exists()
            )
        finally:
            os.chdir(old)

    def test_mode_exe_utilise_meipass_pour_les_ressources(self):
        with tempfile.TemporaryDirectory() as meipass, \
             tempfile.TemporaryDirectory() as exe_dir:
            fake_exe = Path(exe_dir) / "DIP Toolkit Pro.exe"
            with mock.patch.object(sys, "frozen", True, create=True), \
                 mock.patch.object(sys, "_MEIPASS", meipass, create=True), \
                 mock.patch.object(sys, "executable", str(fake_exe)):
                self.assertEqual(paths.resource_path("assets"), Path(meipass) / "assets")
                # Les données modifiables vont à côté de l'.exe (mode portable)
                self.assertEqual(paths.data_dir(), Path(exe_dir).resolve())
                self.assertEqual(paths.settings_path().parent, Path(exe_dir).resolve())


class TestSettings(unittest.TestCase):

    def test_creation_lecture_ecriture(self):
        from src.diagnostics import settings_info
        with tempfile.TemporaryDirectory() as tmp:
            target = str(Path(tmp) / "settings.json")
            with mock.patch.object(settings_info, "SETTINGS_FILE", target):
                s = settings_info.SettingsInfo.load_settings()
                self.assertEqual(s["default_tech_name"], "Technicien DIP")
                self.assertTrue(Path(target).exists())

                s["default_tech_name"] = "Serge"
                ok, _ = settings_info.SettingsInfo.save_settings(s)
                self.assertTrue(ok)
                self.assertEqual(
                    settings_info.SettingsInfo.load_settings()["default_tech_name"], "Serge"
                )
                json.loads(Path(target).read_text(encoding="utf-8"))


class TestImports(unittest.TestCase):
    """Chaque 'from src.x import Y' doit pointer vers un module qui existe."""

    def test_imports_internes_resolus(self):
        problems = []
        for py in (ROOT / "src").rglob("*.py"):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module \
                        and node.module.startswith("src"):
                    base = ROOT.joinpath(*node.module.split("."))
                    if not (base.with_suffix(".py").exists()
                            or (base / "__init__.py").exists()):
                        problems.append(f"{py.relative_to(ROOT)} -> {node.module}")
        self.assertEqual(problems, [])

    def test_plus_de_import_hack(self):
        for py in (ROOT / "src").rglob("*.py"):
            self.assertNotIn("except ModuleNotFoundError",
                             py.read_text(encoding="utf-8"), str(py))

    def test_aucun_chemin_relatif_vers_assets(self):
        for py in list((ROOT / "src").rglob("*.py")) + [ROOT / "main.py"]:
            text = py.read_text(encoding="utf-8")
            self.assertNotIn('Path("assets', text, str(py))
            self.assertNotIn('QPixmap("assets', text, str(py))


if __name__ == "__main__":
    unittest.main()
