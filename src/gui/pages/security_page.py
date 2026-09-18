import os
import subprocess
import ctypes
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


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class SecurityWorker(QThread):
    output_signal = Signal(str)
    finished_signal = Signal(bool, str)

    def __init__(self, action_type):
        super().__init__()
        self.action_type = action_type

    def run(self):
        if self.action_type == "quick_scan":
            self.run_ps_defender("Start-MpScan -ScanType QuickScan", "Scan rapide Windows Defender")
        elif self.action_type == "update_signatures":
            self.run_ps_defender("Update-MpSignature", "Mise à jour des définitions Defender")
        elif self.action_type in ["enable_fw", "disable_fw"]:
            self.toggle_firewall()

    def run_ps_defender(self, ps_cmd_defender, label):
        self.output_signal.emit(f"🛡️ Lancement : {label}...\n")

        if not is_admin():
            self.output_signal.emit("⚠️ Privilèges Administrateur requis.\nDemande d'autorisation UAC en cours...\n")
            try:
                # Lance PowerShell en tant qu'administrateur avec pause à la fin pour voir le résultat
                ps_cmd = f'Start-Process powershell -ArgumentList "-NoExit -Command {ps_cmd_defender}" -Verb RunAs'
                res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
                
                if res.returncode == 0:
                    msg = f"✅ {label} démarré dans une fenêtre PowerShell Administrateur !"
                    self.output_signal.emit(f"{msg}\n")
                    self.finished_signal.emit(True, msg)
                else:
                    msg = "Action annulée par l'utilisateur."
                    self.output_signal.emit(f"❌ {msg}\n")
                    self.finished_signal.emit(False, msg)
            except Exception as e:
                self.output_signal.emit(f"❌ Erreur UAC : {str(e)}\n")
                self.finished_signal.emit(False, str(e))
            return

        # Si l'application est DÉJÀ lancée en admin
        try:
            full_cmd = f"powershell -Command \"{ps_cmd_defender}\""
            process = subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="cp1252",
                errors="ignore",
                shell=True
            )

            for line in iter(process.stdout.readline, ""):
                if line:
                    self.output_signal.emit(line)

            process.stdout.close()
            process.wait()

            if process.returncode == 0:
                msg = f"✅ {label} terminé avec succès !"
                self.output_signal.emit(f"\n{msg}\n")
                self.finished_signal.emit(True, msg)
            else:
                msg = f"⚠️ {label} terminé avec le code : {process.returncode}"
                self.output_signal.emit(f"\n{msg}\n")
                self.finished_signal.emit(False, msg)
        except Exception as e:
            self.output_signal.emit(f"\n❌ Erreur : {str(e)}\n")
            self.finished_signal.emit(False, str(e))

    def toggle_firewall(self):
        state = "on" if self.action_type == "enable_fw" else "off"
        action_label = "Activation" if state == "on" else "Désactivation"
        self.output_signal.emit(f"🧱 {action_label} du pare-feu Windows...\n")

        cmd = f"netsh advfirewall set allprofiles state {state}"

        if not is_admin():
            self.output_signal.emit("⚠️ Privilèges Administrateur requis.\nDemande UAC en cours...\n")
            ps_cmd = f'Start-Process cmd -ArgumentList "/c {cmd}" -Verb RunAs'
            res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
            if res.returncode == 0:
                msg = f"Pare-feu passé sur {state.upper()}."
                self.output_signal.emit(f"✅ {msg}\n")
                self.finished_signal.emit(True, msg)
            else:
                self.finished_signal.emit(False, "Action refusée.")
            return

        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding="cp1252")
            if res.returncode == 0:
                msg = f"Le pare-feu Windows a été passé sur : {state.upper()}"
                self.output_signal.emit(f"✅ {msg}\n")
                self.finished_signal.emit(True, msg)
            else:
                self.output_signal.emit(f"❌ Erreur : {res.stderr}\n")
                self.finished_signal.emit(False, res.stderr)
        except Exception as e:
            self.output_signal.emit(f"❌ Exception : {str(e)}\n")
            self.finished_signal.emit(False, str(e))


class SecurityPage(BasePage):

    def __init__(self):
        super().__init__(
            "🛡️ Sécurité & Antivirus",
            "Contrôlez l'état de Windows Defender et du pare-feu du système."
        )

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)

        # ----------------------------------------------------
        # BARRE D'ACTIONS
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

        self.btn_scan = QPushButton("🔍 Scan Rapide Defender")
        self.btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_scan.setStyleSheet(btn_style)
        self.btn_scan.clicked.connect(lambda: self.run_action("quick_scan"))

        self.btn_update = QPushButton("🔄 Mettre à jour Defender")
        self.btn_update.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update.setStyleSheet(btn_style)
        self.btn_update.clicked.connect(lambda: self.run_action("update_signatures"))

        self.btn_enable_fw = QPushButton("🧱 Activer Pare-feu")
        self.btn_enable_fw.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_enable_fw.setStyleSheet(btn_style)
        self.btn_enable_fw.clicked.connect(lambda: self.run_action("enable_fw"))

        self.btn_disable_fw = QPushButton("⚠️ Désactiver Pare-feu")
        self.btn_disable_fw.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_disable_fw.setStyleSheet(btn_style)
        self.btn_disable_fw.clicked.connect(lambda: self.run_action("disable_fw"))

        actions_layout.addWidget(self.btn_scan)
        actions_layout.addWidget(self.btn_update)
        actions_layout.addWidget(self.btn_enable_fw)
        actions_layout.addWidget(self.btn_disable_fw)
        actions_layout.addStretch()

        scroll_layout.addLayout(actions_layout)

        # ----------------------------------------------------
        # CONSOLE DE SORTIE
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

        title = QLabel("💻 État des opérations de sécurité")
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
        self.console.setPlaceholderText("Les résultats des analyses s'afficheront ici...")

        console_layout.addWidget(title)
        console_layout.addWidget(self.console)

        scroll_layout.addWidget(console_card)
        scroll_area.setWidget(scroll_content)
        self.content_layout.addWidget(scroll_area)

    def set_buttons_enabled(self, enabled):
        self.btn_scan.setEnabled(enabled)
        self.btn_update.setEnabled(enabled)
        self.btn_enable_fw.setEnabled(enabled)
        self.btn_disable_fw.setEnabled(enabled)

    def run_action(self, action_type):
        self.set_buttons_enabled(False)
        self.console.clear()

        self.worker = SecurityWorker(action_type)
        self.worker.output_signal.connect(self.update_console)
        self.worker.finished_signal.connect(self.on_action_finished)
        self.worker.start()

    def update_console(self, text):
        self.console.append(text.strip())

    def on_action_finished(self, success, message):
        self.set_buttons_enabled(True)
        if success:
            QMessageBox.information(self, "Sécurité", f"✅ {message}")
        else:
            QMessageBox.warning(self, "Sécurité", f"⚠️ {message}")