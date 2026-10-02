from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QVBoxLayout
)

from .base_page import BasePage

from src.diagnostics.network_info import get_network_info
from src.gui.widgets.network_card import NetworkCard


class NetworkPage(BasePage):

    def __init__(self):
        super().__init__(
            "🌐 Réseau",
            "Informations sur la connexion réseau et les interfaces de l'ordinateur."
        )

        # ==================================================
        # Zone défilante (QScrollArea)
        # ==================================================

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)

        # ==================================================
        # Carte des informations réseau
        # ==================================================

        infos = get_network_info()
        self.card = NetworkCard(infos)
        scroll_layout.addWidget(self.card)

        # ==================================================
        # Barre d'actions & Boutons
        # ==================================================

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        # Style réutilisable pour les boutons secondaires
        btn_style = """
            QPushButton {
                background-color: #1e222d;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00adb5;
                border-color: #00adb5;
                color: #ffffff;
            }
        """

        self.refresh_button = QPushButton("🔄 Actualiser")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setStyleSheet(btn_style)

        self.internet_button = QPushButton("🌐 Tester Internet")
        self.internet_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.internet_button.setStyleSheet(btn_style)

        self.scan_button = QPushButton("📡 Scanner le réseau")
        self.scan_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_button.setStyleSheet(btn_style)

        self.export_button = QPushButton("📄 Exporter")
        self.export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_button.setStyleSheet(btn_style)

        actions_layout.addWidget(self.refresh_button)
        actions_layout.addWidget(self.internet_button)
        actions_layout.addWidget(self.scan_button)
        actions_layout.addWidget(self.export_button)
        actions_layout.addStretch()

        scroll_layout.addLayout(actions_layout)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        self.content_layout.addWidget(scroll_area)

        self.setStyleSheet("""
                    QWidget#DashboardPage, QScrollArea, QScrollArea > QWidget > QWidget {
                        background-color: #0f111a;
                    }
                """)