# -*- mode: python ; coding: utf-8 -*-
# Compilation : pyinstaller "DIP Toolkit Pro.spec"   (ou lancer build.bat)
#
# Mode par défaut : UN SEUL .exe (pratique pour une clé USB).
# Pour un dossier au lieu d'un fichier unique (démarrage plus rapide, souvent
# moins de fausses alertes antivirus), passer ONEFILE à False.
ONEFILE = True

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    ["wmi", "win32com.client", "pythoncom", "pywintypes"]
    + collect_submodules("src")
)

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

if ONEFILE:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="DIP Toolkit Pro",
        debug=False,
        strip=False,
        upx=False,
        console=False,          # pas de fenêtre noire
        icon="assets/logo/app.ico",
        uac_admin=True,         # demande les droits administrateur au lancement
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="DIP Toolkit Pro",
        debug=False,
        strip=False,
        upx=False,
        console=False,
        icon="assets/logo/app.ico",
        uac_admin=True,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="DIP Toolkit Pro",
    )
