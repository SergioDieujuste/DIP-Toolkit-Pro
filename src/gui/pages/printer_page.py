import os
import subprocess
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QFrame,
    QLabel,
    QComboBox,
    QMessageBox,
)

from .base_page import BasePage


def is_admin():
    """Vérifie si le logiciel est exécuté avec les droits administrateur."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class SpoolerWorker(QThread):
    finished_signal = Signal(bool, str)

    def __init__(self, action_type):
        super().__init__()
        self.action_type = action_type

    def run(self):
        # Si nous ne sommes pas administrateur, on demande l'élévation UAC via PowerShell
        if not is_admin():
            try:
                if self.action_type == "restart":
                    ps_cmd = 'Start-Process cmd -ArgumentList "/c net stop spooler && net start spooler" -Verb RunAs'
                elif self.action_type == "purge":
                    ps_cmd = 'Start-Process cmd -ArgumentList "/c net stop spooler && del /Q /F %systemroot%\\System32\\spool\\PRINTERS\\* && net start spooler" -Verb RunAs'

                res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
                if res.returncode == 0:
                    self.finished_signal.emit(True, "Commande envoyée avec privilèges administrateur (UAC) !")
                else:
                    self.finished_signal.emit(False, "Action annulée par l'utilisateur ou échouée.")
            except Exception as e:
                self.finished_signal.emit(False, f"Erreur d'élévation UAC :\n{str(e)}")
            return

        # Si nous sommes DÉJÀ administrateur, exécution directe
        try:
            if self.action_type == "restart":
                subprocess.run("net stop spooler", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run("net start spooler", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.finished_signal.emit(True, "Spooler d'impression redémarré avec succès !")
            
            elif self.action_type == "purge":
                subprocess.run("net stop spooler", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                spool_dir = r"C:\Windows\System32\spool\PRINTERS"
                if os.path.exists(spool_dir):
                    for file in os.listdir(spool_dir):
                        file_path = os.path.join(spool_dir, file)
                        try:
                            if os.path.isfile(file_path):
                                os.unlink(file_path)
                        except Exception:
                            pass
                
                subprocess.run("net start spooler", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.finished_signal.emit(True, "File d'attente d'impression purgée avec succès !")
        except Exception as e:
            self.finished_signal.emit(False, f"Erreur :\n{str(e)}")


class PrinterPage(BasePage):

    def __init__(self):
        super().__init__(
            "🖨️ Gestion des Imprimantes",
            "Diagnostiquez et débloquez les imprimantes du système en un clic."
        )

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)

        # ----------------------------------------------------
        # 1. CARTE DE SÉLECTION D'IMPRIMANTE
        # ----------------------------------------------------
        select_card = QFrame()
        select_card.setStyleSheet("""
            QFrame {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
        """)
        select_layout = QVBoxLayout(select_card)
        select_layout.setContentsMargins(18, 16, 18, 16)
        select_layout.setSpacing(10)

        title = QLabel("🖨️ Imprimantes détectées sur le système")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #00adb5;")

        self.printer_combo = QComboBox()
        self.printer_combo.setStyleSheet("""
            QComboBox {
                background-color: #141721;
                color: #ffffff;
                border: 1px solid #2e3440;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #1e222d;
                color: #ffffff;
                selection-background-color: #00adb5;
            }
        """)

        select_layout.addWidget(title)
        select_layout.addWidget(self.printer_combo)
        scroll_layout.addWidget(select_card)

        # ----------------------------------------------------
        # 2. BARRE D'ACTIONS TECHNIQUE
        # ----------------------------------------------------
        btn_style = """
            QPushButton {
                background-color: #1e222d;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 10px 16px;
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

        self.btn_refresh = QPushButton("🔄 Actualiser la liste")
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet(btn_style)
        self.btn_refresh.clicked.connect(self.load_printers)

        self.btn_restart_spooler = QPushButton("⚡ Redémarrer le Spooler")
        self.btn_restart_spooler.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_restart_spooler.setStyleSheet(btn_style)
        self.btn_restart_spooler.clicked.connect(lambda: self.run_spooler_action("restart"))

        self.btn_purge_queue = QPushButton("🧹 Purger la file d'attente")
        self.btn_purge_queue.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_purge_queue.setStyleSheet(btn_style)
        self.btn_purge_queue.clicked.connect(lambda: self.run_spooler_action("purge"))

        self.btn_test_page = QPushButton("📄 Imprimer page de test")
        self.btn_test_page.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test_page.setStyleSheet(btn_style)
        self.btn_test_page.clicked.connect(self.print_test_page)

        actions_layout.addWidget(self.btn_refresh)
        actions_layout.addWidget(self.btn_restart_spooler)
        actions_layout.addWidget(self.btn_purge_queue)
        actions_layout.addWidget(self.btn_test_page)
        actions_layout.addStretch()

        scroll_layout.addLayout(actions_layout)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        self.content_layout.addWidget(scroll_area)

        # Charger la liste des imprimantes au démarrage
        self.load_printers()

    def load_printers(self):
        """Récupère la liste des imprimantes installées de manière sécurisée."""
        self.printer_combo.clear()
        printers = []

        # Méthode 1 : Tentative via win32print (méthode native Windows la plus fiable)
        try:
            import win32print
            enum_flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            installed_printers = win32print.EnumPrinters(enum_flags)
            printers = [p[2] for p in installed_printers]
        except Exception:
            pass

        # Méthode 2 : Fallback via PowerShell avec gestion d'encodage explicite
        if not printers:
            try:
                cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-Printer | Select-Object -ExpandProperty Name"'
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    encoding='cp1252', # Gestion des caractères accentués sous Windows FR
                    errors='ignore',
                    shell=True
                )
                if result.returncode == 0:
                    printers = [p.strip() for p in result.stdout.splitlines() if p.strip()]
            except Exception:
                pass

        # Affichage dans la ComboBox
        if printers:
            self.printer_combo.addItems(printers)
        else:
            self.printer_combo.addItem("Aucune imprimante détectée")

    def run_spooler_action(self, action_type):
        """Lance l'action spooler dans un thread secondaire."""
        self.btn_restart_spooler.setEnabled(False)
        self.btn_purge_queue.setEnabled(False)

        self.worker = SpoolerWorker(action_type)
        self.worker.finished_signal.connect(self.on_spooler_finished)
        self.worker.start()

    def on_spooler_finished(self, success, message):
        self.btn_restart_spooler.setEnabled(True)
        self.btn_purge_queue.setEnabled(True)

        if success:
            QMessageBox.information(self, "Action Spooler", f"✅ {message}")
        else:
            QMessageBox.critical(self, "Action Spooler", f"❌ {message}")

    def print_test_page(self):
        """Envoie une page de test à l'imprimante sélectionnée."""
        selected_printer = self.printer_combo.currentText()
        
        if not selected_printer or any(k in selected_printer for k in ["Aucune", "Erreur"]):
            QMessageBox.warning(self, "Page de test", "Veuillez sélectionner une imprimante valide.")
            return

        # Vérification si c'est une imprimante virtuelle (qui ne prend pas en charge les pages de test)
        virtual_printers = ["PDF", "XPS", "OneNote", "Fax"]
        if any(vp.lower() in selected_printer.lower() for vp in virtual_printers):
            QMessageBox.warning(
                self, 
                "Imprimante virtuelle", 
                f"L'imprimante '{selected_printer}' est une imprimante virtuelle.\n"
                "Les pages de test système ne sont pas supportées pour ce type de périphérique."
            )
            return

        try:
            # Commande PowerShell moderne pour lancer la page de test Windows officielle
            ps_command = f'Get-CimInstance Win32_Printer -Filter "Name = \'{selected_printer}\'" | Invoke-CimMethod -MethodName PrintTestPage'
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            QMessageBox.information(
                self, 
                "Page de test", 
                f"✅ Page de test envoyée avec succès à :\n'{selected_printer}'"
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Page de test", 
                f"❌ Échec d'envoi de la page de test.\nAssurez-vous que l'imprimante est bien connectée et en ligne."
            )