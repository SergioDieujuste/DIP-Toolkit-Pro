from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea
)
from PySide6.QtCore import Qt

# Imports des modules avec gestion des chemins
try:
    from src.diagnostics.maintenance_info import MaintenanceInfo
    from src.gui.widgets.maintenance_card import MaintenanceCard
except ModuleNotFoundError:
    from diagnostics.maintenance_info import MaintenanceInfo
    from widgets.maintenance_card import MaintenanceCard


class MaintenancePage(QWidget):
    """Page regroupant les outils de nettoyage et de maintenance rapide."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("maintenance_page")

        self.cards = []
        self.init_ui()
        self.load_tasks()

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
        # 1. EN-TÊTE DE LA PAGE (Titre + Bouton Tout Exécuter)
        # ----------------------------------------------------
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_label = QLabel("Maintenance & Nettoyage")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")

        subtitle_label = QLabel("Outils de purge, nettoyage temporaire et optimisation rapide")
        subtitle_label.setStyleSheet("font-size: 12px; color: #a0a5b5;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Bouton "Tout Exécuter"
        self.run_all_btn = QPushButton(" Tout Exécuter")
        self.run_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e222d;
                color: #00adb5;
                border: 1px solid #00adb5;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00adb5;
                color: #ffffff;
            }
        """)
        self.run_all_btn.clicked.connect(self._run_all_tasks)
        header_layout.addWidget(self.run_all_btn)

        main_layout.addLayout(header_layout)

        # ----------------------------------------------------
        # 2. ZONE DÉFILANTE (SCROLL AREA) POUR LES CARTES
        # ----------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

    def load_tasks(self):
        """Charge les différentes cartes de maintenance."""
        tasks = MaintenanceInfo.get_available_tasks()
        self.cards.clear()

        for task in tasks:
            card = MaintenanceCard(task)
            self.cards_layout.addWidget(card)
            self.cards.append(card)

    def _run_all_tasks(self):
        """Déclenche séquentiellement l'exécution de toutes les cartes."""
        for card in self.cards:
            card._run_maintenance()