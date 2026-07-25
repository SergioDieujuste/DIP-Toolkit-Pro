from PySide6.QtWidgets import (
    QPushButton,
)

from .base_page import BasePage

from src.diagnostics.network_info import get_network_info
from src.gui.widgets.network_card import NetworkCard


class NetworkPage(BasePage):

    def __init__(self):
        super().__init__(
            "🌐 Réseau",
            "Informations sur la connexion réseau de l'ordinateur."
        )

        infos = get_network_info()

        self.card = NetworkCard(infos)

        self.content_layout.addWidget(self.card)

        # ==========================
        # Boutons (fonctionnalités futures)
        # ==========================

        self.refresh_button = QPushButton("🔄 Actualiser")
        self.internet_button = QPushButton("🌐 Tester Internet")
        self.scan_button = QPushButton("📡 Scanner le réseau")
        self.export_button = QPushButton("📄 Exporter")

        self.content_layout.addWidget(self.refresh_button)
        self.content_layout.addWidget(self.internet_button)
        self.content_layout.addWidget(self.scan_button)
        self.content_layout.addWidget(self.export_button)

        self.content_layout.addStretch()