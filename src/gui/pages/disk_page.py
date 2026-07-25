from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QScrollArea,
    QVBoxLayout,
)

from .base_page import BasePage

from src.diagnostics.disk_info import get_disks
from src.gui.widgets.disk_card import DiskCard


class DiskPage(BasePage):

    def __init__(self):
        super().__init__(
            "💾 Gestion des disques",
            "Visualisez l'utilisation de vos disques et partitions."
        )

        # ==========================================
        # Zone défilante
        # ==========================================

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        container = QWidget()

        grid = QGridLayout()
        grid.setContentsMargins(10, 10, 10, 10)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)

        # ==========================================
        # Création des cartes
        # ==========================================

        disks = get_disks()

        row = 0
        col = 0

        for disk in disks:

            card = DiskCard(disk)

            grid.addWidget(card, row, col)

            col += 1

            if col == 2:
                col = 0
                row += 1

        container.setLayout(grid)

        scroll.setWidget(container)

        # ==========================================
        # Ajout dans BasePage
        # ==========================================

        self.content_layout.addWidget(scroll)