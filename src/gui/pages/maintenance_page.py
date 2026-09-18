import os
import shutil
import subprocess
import ctypes
import webbrowser
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
    QLabel,
    QTextEdit,
    QMessageBox,
)

from .base_page import BasePage

import sys

def get_asset_path(relative_path):
    """ Renvoie le chemin absolu vers la ressource, fonctionne en dev et pour PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller crée un dossier temporaire dans _MEIPASS
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def is_admin():
    """Vérifie si l'application est exécutée en mode administrateur."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class MaintenanceWorker(QThread):
    """Thread secondaire pour exécuter les commandes lourdes (SFC, DISM, Nettoyage)."""
    output_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, action_type):
        super().__init__()
        self.action_type = action_type

    def run(self):
        if self.action_type == "clean_temp":
            self.clean_temp_files()
        elif self.action_type == "empty_trash":
            self.empty_recycle_bin()
        elif self.action_type in ["sfc", "dism"]:
            self.run_system_repair()

    def clean_temp_files(self):
        self.output_signal.emit("🧹 Suppression des fichiers temporaires en cours...\n")
        temp_folders = [
            os.environ.get("TEMP"),
            r"C:\Windows\Temp"
        ]
        deleted_files = 0
        freed_bytes = 0

        for folder in temp_folders:
            if not folder or not os.path.exists(folder):
                continue
            for root, dirs, files in os.walk(folder):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        size = os.path.getsize(fp)
                        os.remove(fp)
                        freed_bytes += size
                        deleted_files += 1
                    except Exception:
                        pass  # Ignorer les fichiers actuellement utilisés par le système

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        msg = f"Nettoyage terminé ! {deleted_files} fichiers supprimés (~{freed_mb} Mo libérés)."
        self.output_signal.emit(f"✅ {msg}\n")
        self.finished_signal.emit(True, msg)

    def empty_recycle_bin(self):
        self.output_signal.emit("🗑️ Vidage de la corbeille...\n")
        try:
            flags = 7
            result = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
            if result == 0:
                msg = "La corbeille a été vidée avec succès !"
                self.output_signal.emit(f"✅ {msg}\n")
                self.finished_signal.emit(True, msg)
            else:
                msg = "La corbeille est déjà vide ou l'action a été annulée."
                self.output_signal.emit(f"ℹ️ {msg}\n")
                self.finished_signal.emit(True, msg)
        except Exception as e:
            self.output_signal.emit(f"❌ Erreur : {str(e)}\n")
            self.finished_signal.emit(False, str(e))

    def run_system_repair(self):
        cmd_str = ""
        if self.action_type == "sfc":
            cmd_str = "sfc /scannow"
            self.output_signal.emit("⚙️ Lancement de 'sfc /scannow'...\n")
        elif self.action_type == "dism":
            cmd_str = "DISM.exe /Online /Cleanup-Image /RestoreHealth"
            self.output_signal.emit("⚙️ Lancement de DISM...\n")

        if not is_admin():
            self.output_signal.emit("⚠️ Privilèges Administrateur requis.\nDemande d'autorisation UAC en cours...\n")
            try:
                ps_cmd = f'Start-Process cmd -ArgumentList "/k {cmd_str}" -Verb RunAs'
                res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
                
                if res.returncode == 0:
                    msg = f"La commande {self.action_type.upper()} a été lancée dans une fenêtre Administrateur."
                    self.output_signal.emit(f"✅ {msg}\n")
                    self.finished_signal.emit(True, msg)
                else:
                    msg = "L'élévation de privilèges a été refusée ou a échoué."
                    self.output_signal.emit(f"❌ {msg}\n")
                    self.finished_signal.emit(False, msg)
            except Exception as e:
                self.output_signal.emit(f"❌ Erreur UAC : {str(e)}\n")
                self.finished_signal.emit(False, str(e))
            return

        cmd = ["sfc", "/scannow"] if self.action_type == "sfc" else ["DISM.exe", "/Online", "/Cleanup-Image", "/RestoreHealth"]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="cp1252",
                errors="ignore"
            )

            for line in iter(process.stdout.readline, ""):
                if line:
                    self.output_signal.emit(line)

            process.stdout.close()
            process.wait()

            if process.returncode == 0:
                msg = f"Analyse et réparation {self.action_type.upper()} terminées avec succès !"
                self.output_signal.emit(f"\n✅ {msg}\n")
                self.finished_signal.emit(True, msg)
            else:
                msg = f"La commande {self.action_type.upper()} s'est terminée avec le code : {process.returncode}"
                self.output_signal.emit(f"\n⚠️ {msg}\n")
                self.finished_signal.emit(False, msg)
        except Exception as e:
            self.output_signal.emit(f"\n❌ Erreur d'exécution : {str(e)}\n")
            self.finished_signal.emit(False, str(e))


class MaintenancePage(BasePage):

    def __init__(self):
        super().__init__(
            "🛠️ Maintenance & Nettoyage",
            "Optimisez le système et réparez les erreurs Windows en un clic."
        )

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)

        # ----------------------------------------------------
        # 1. BARRE DE BOUTONS D'ACTION
        # ----------------------------------------------------
        btn_style = """
            QPushButton {
                background-color: #1e222d;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 10px 14px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00adb5;
                border-color: #00adb5;
            }
            QPushButton:disabled {
                background-color: #141721;
                color: #555555;
            }
        """

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        self.btn_clean_temp = QPushButton("🧹 Nettoyer les TEMP")
        self.btn_clean_temp.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clean_temp.setStyleSheet(btn_style)
        self.btn_clean_temp.clicked.connect(lambda: self.run_action("clean_temp"))

        self.btn_empty_trash = QPushButton("🗑️ Vider la corbeille")
        self.btn_empty_trash.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_empty_trash.setStyleSheet(btn_style)
        self.btn_empty_trash.clicked.connect(lambda: self.run_action("empty_trash"))

        self.btn_sfc = QPushButton("⚡ Réparer SFC (scannow)")
        self.btn_sfc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sfc.setStyleSheet(btn_style)
        self.btn_sfc.clicked.connect(lambda: self.run_action("sfc"))

        self.btn_dism = QPushButton("🛡️ Réparer DISM")
        self.btn_dism.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dism.setStyleSheet(btn_style)
        self.btn_dism.clicked.connect(lambda: self.run_action("dism"))

        # --- NOUVEAU BOUTON RUSTDESK ---
        self.btn_rustdesk = QPushButton("🎧 Assistance RustDesk")
        self.btn_rustdesk.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_rustdesk.setStyleSheet(btn_style)
        self.btn_rustdesk.clicked.connect(self.launch_rustdesk)

        actions_layout.addWidget(self.btn_clean_temp)
        actions_layout.addWidget(self.btn_empty_trash)
        actions_layout.addWidget(self.btn_sfc)
        actions_layout.addWidget(self.btn_dism)
        actions_layout.addWidget(self.btn_rustdesk)
        actions_layout.addStretch()

        scroll_layout.addLayout(actions_layout)

        # ----------------------------------------------------
        # 2. CONSOLE DE SORTIE / TERMINAL INTÉGRÉ
        # ----------------------------------------------------
        console_card = QFrame()
        console_card.setStyleSheet("""
            QFrame {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
        """)
        console_layout = QVBoxLayout(console_card)
        console_layout.setContentsMargins(18, 16, 18, 16)
        console_layout.setSpacing(10)

        title = QLabel("💻 Console d'exécution en direct")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #00adb5;")

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet("""
            QTextEdit {
                background-color: #0f111a;
                color: #00ffcc;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #2e3440;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        self.console.setPlaceholderText("Les résultats des actions s'afficheront ici...")

        console_layout.addWidget(title)
        console_layout.addWidget(self.console)

        scroll_layout.addWidget(console_card)
        scroll_area.setWidget(scroll_content)
        self.content_layout.addWidget(scroll_area)

    def set_buttons_enabled(self, enabled):
        self.btn_clean_temp.setEnabled(enabled)
        self.btn_empty_trash.setEnabled(enabled)
        self.btn_sfc.setEnabled(enabled)
        self.btn_dism.setEnabled(enabled)
        self.btn_rustdesk.setEnabled(enabled)

    def run_action(self, action_type):
        self.set_buttons_enabled(False)
        self.console.clear()

        self.worker = MaintenanceWorker(action_type)
        self.worker.output_signal.connect(self.update_console)
        self.worker.finished_signal.connect(self.on_action_finished)
        self.worker.start()

    def update_console(self, text):
        self.console.append(text.strip())

    def on_action_finished(self, success, message):
        self.set_buttons_enabled(True)
        if success:
            QMessageBox.information(self, "Maintenance", f"✅ {message}")
        else:
            QMessageBox.warning(self, "Maintenance", f"⚠️ {message}")

    # --- MÉTHODE POUR LANCER RUSTDESK ---
    def launch_rustdesk(self):
        # Utilisation du chemin dynamique
        rustdesk_path = get_asset_path(os.path.join("assets", "tools", "rustdesk.exe"))

        if os.path.exists(rustdesk_path):
            try:
                subprocess.Popen([rustdesk_path])
                self.console.append("🎧 Lancement de RustDesk effectué.")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de lancer RustDesk : {e}")
        else:
            reply = QMessageBox.question(
                self,
                "RustDesk introuvable",
                f"L'exécutable RustDesk est introuvable dans :\n{rustdesk_path}\n\nSouhaitez-vous ouvrir la page de téléchargement ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                webbrowser.open("https://rustdesk.com/")