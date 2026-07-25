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

        layout = QVBoxLayout()
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

        # ==================================================
        # Version
        # ==================================================

        version = QLabel("Version 0.8")
        version.setObjectName("VersionLabel")
        version.setAlignment(Qt.AlignCenter)

        # ==================================================
        # Séparateur
        # ==================================================

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setObjectName("SidebarSeparator")

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

            bouton.setIcon(QIcon(str(icons / fichier)))
            bouton.setIconSize(QSize(20, 20))
            bouton.setMinimumHeight(42)

            self.buttons[texte] = bouton

            layout.addWidget(bouton)

        layout.addStretch()

        # ==================================================
        # Pied de page
        # ==================================================

        footer = QLabel("© Dépannage Informatique Plus")
        footer.setObjectName("SidebarFooter")
        footer.setAlignment(Qt.AlignCenter)

        layout.addWidget(footer)

        self.setLayout(layout)

    def set_active_button(self, button_name):

        for name, button in self.buttons.items():

            button.setProperty("active", name == button_name)

            button.style().unpolish(button)
            button.style().polish(button)