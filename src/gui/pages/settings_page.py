from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
)
from PySide6.QtCore import Qt

# Imports des modules avec gestion des chemins
try:
    from src.gui.widgets.settings_card import SettingsCard
except ModuleNotFoundError:
    from widgets.settings_card import SettingsCard


class SettingsPage(QWidget):
    """Page de configuration globale de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_page")

        self.init_ui()

        self.setStyleSheet("""
                    QWidget#DashboardPage, QScrollArea, QScrollArea > QWidget > QWidget {
                        background-color: #0f111a;
                    }
                """)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ----------------------------------------------------
        # 1. EN-TÊTE DE LA PAGE
        # ----------------------------------------------------
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_label = QLabel("Paramètres & Configuration")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")

        subtitle_label = QLabel("Personnalisez le comportement par défaut de DIP Toolkit Pro")
        subtitle_label.setStyleSheet("font-size: 12px; color: #a0a5b5;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # ----------------------------------------------------
        # 2. ZONE DÉFILANTE AVEC LA CARTE DE PARAMÈTRES
        # ----------------------------------------------------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        scroll_content = QWidget()
        cards_layout = QVBoxLayout(scroll_content)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(10)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Ajout de la carte de paramètres
        self.settings_card = SettingsCard()
        cards_layout.addWidget(self.settings_card)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)