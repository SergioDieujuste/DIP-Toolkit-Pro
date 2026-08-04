from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QStackedWidget,
)

from src.gui.sidebar import Sidebar

from src.gui.dashboard_page import Dashboard
from src.gui.pages.diagnostic_page import DiagnosticPage
from src.gui.pages.network_page import NetworkPage
from src.gui.pages.disk_page import DiskPage
from src.gui.pages.maintenance_page import MaintenancePage
from src.gui.pages.report_page import ReportPage
from src.gui.pages.settings_page import SettingsPage
from src.gui.pages.live_monitor_page import LiveMonitorPage
from src.gui.pages.printer_page import PrinterPage
from src.gui.pages.security_page import SecurityPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DIP Toolkit Pro")
        self.resize(1400, 850)

        # Style sombre global pour la fenêtre et la zone centrale
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f111a;
            }
            QWidget#CentralWidget {
                background-color: #0f111a;
            }
            QStackedWidget {
                background-color: #0f111a;
            }
        """)

        self.sidebar = Sidebar()

        self.stack = QStackedWidget()
        self.stack.setObjectName("MainStack")

        # ==========================
        # Toutes les pages du logiciel
        # ==========================

        self.pages = {
            "Tableau de bord": Dashboard(),
            "Diagnostic": DiagnosticPage(),
            "Supervision": LiveMonitorPage(),
            "Réseau": NetworkPage(),
            "Disques": DiskPage(),
            "Imprimantes": PrinterPage(),
            "Sécurité": SecurityPage(),
            "Maintenance": MaintenancePage(),
            "Rapport": ReportPage(),
            "Paramètres": SettingsPage(),
        }

        # Ajoute toutes les pages au QStackedWidget
        for page in self.pages.values():
            self.stack.addWidget(page)

        # ==========================
        # Fenêtre principale
        # ==========================

        central = QWidget()
        central.setObjectName("CentralWidget")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.sidebar, 1)
        layout.addWidget(self.stack, 5)

        central.setLayout(layout)

        self.setCentralWidget(central)

        self.connect_navigation()

        # Page affichée au démarrage
        self.change_page("Tableau de bord")

    # ==========================
    # Navigation
    # ==========================

    def connect_navigation(self):

        for nom, bouton in self.sidebar.buttons.items():

            if nom in self.pages:

                bouton.clicked.connect(
                    lambda checked=False, page=nom: self.change_page(page)
                )

    # ==========================
    # Changement de page
    # ==========================

    def change_page(self, page_name):

        if page_name in self.pages:
            self.stack.setCurrentWidget(self.pages[page_name])
            self.update_sidebar(page_name)

    # ==========================
    # Mise à jour du menu
    # ==========================

    def update_sidebar(self, active_page):

        for nom, bouton in self.sidebar.buttons.items():

            bouton.setProperty("active", nom == active_page)

            bouton.style().unpolish(bouton)
            bouton.style().polish(bouton)

            bouton.repaint()

    def closeEvent(self, event):
        """S'exécute automatiquement lors de la fermeture de l'application."""
        # Arrête le timer de la page de supervision s'il existe
        if "Supervision" in self.pages:
            monitor_page = self.pages["Supervision"]
            if hasattr(monitor_page, "timer") and monitor_page.timer.isActive():
                monitor_page.timer.stop()
        
        # Accepte la fermeture de la fenêtre
        event.accept()