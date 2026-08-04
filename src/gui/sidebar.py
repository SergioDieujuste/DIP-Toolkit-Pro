from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap

from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QFrame,
)


class Sidebar(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("Sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(8)

        self.buttons = {}

        # ==================================================
        # Logo
        # ==================================================

        logo = QLabel()
        logo.setObjectName("SidebarLogo")

        pixmap = QPixmap("assets/logo/logo-web-transparent.png")

        logo.setPixmap(
            pixmap.scaled(
                170,
                170,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

        logo.setAlignment(Qt.AlignCenter)

        # ==================================================
        # Nom de l'entreprise
        # ==================================================

        company = QLabel("Dépannage Informatique Plus")
        company.setObjectName("CompanyName")
        company.setAlignment(Qt.AlignCenter)
        company.setWordWrap(True)
        company.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 13px; margin-top: 6px;")

        # ==================================================
        # Version
        # ==================================================

        version = QLabel("Version 0.8")
        version.setObjectName("VersionLabel")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #a0a5b5; font-size: 11px;")

        # ==================================================
        # Séparateur
        # ==================================================

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setObjectName("SidebarSeparator")
        line.setStyleSheet("background-color: #2e3440; max-height: 1px; border: none; margin: 8px 0px;")

        layout.addWidget(logo)
        layout.addWidget(company)
        layout.addWidget(version)
        layout.addWidget(line)

        # ==================================================
        # Boutons
        # ==================================================

        icons = Path("assets/icons")

        modules = [
            ("Tableau de bord", "layout-dashboard.svg"),
            ("Diagnostic", "stethoscope.svg"),
            ("Supervision", "chart-line.svg"),
            ("Réseau", "network.svg"),
            ("Disques", "device-floppy.svg"),
            ("Imprimantes", "printer.svg"),
            ("Sécurité", "shield-lock.svg"),
            ("Maintenance", "tool.svg"),
            ("Rapport", "file-export.svg"),
            ("Base de connaissances", "books.svg"),
            ("Paramètres", "settings.svg"),
        ]

        for texte, fichier in modules:

            bouton = QPushButton(texte)
            bouton.setCursor(Qt.CursorShape.PointingHandCursor)

            bouton.setIcon(QIcon(str(icons / fichier)))
            bouton.setIconSize(QSize(20, 20))
            bouton.setMinimumHeight(40)

            self.buttons[texte] = bouton

            layout.addWidget(bouton)

        layout.addStretch()

        # ==================================================
        # Pied de page
        # ==================================================

        footer = QLabel("© Dépannage Informatique Plus")
        footer.setObjectName("SidebarFooter")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #666e80; font-size: 10px; margin-top: 10px;")

        layout.addWidget(footer)

        # ==================================================
        # Feuille de style globale pour la Sidebar
        # ==================================================

        self.setStyleSheet("""
            QWidget#Sidebar {
                background-color: #141721;
                border-right: 1px solid #2e3440;
            }
            QPushButton {
                background-color: transparent;
                color: #a0a5b5;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                text-align: left;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1e222d;
                color: #ffffff;
            }
            QPushButton[active="true"] {
                background-color: #00adb5;
                color: #ffffff;
                font-weight: bold;
            }
        """)

    def set_active_button(self, button_name):

        for name, button in self.buttons.items():

            button.setProperty("active", name == button_name)

            button.style().unpolish(button)
            button.style().polish(button)