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
        # Zone défilante (QScrollArea)
        # ==========================================

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)

        # ==========================================
        # Grille des cartes
        # ==========================================

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(15)

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

        scroll_layout.addLayout(grid)
        scroll_layout.addStretch()

        scroll_area.setWidget(container)

        # ==========================================
        # Ajout dans BasePage
        # ==========================================

        self.content_layout.addWidget(scroll_area)

        self.setStyleSheet("""
                    QWidget#DashboardPage, QScrollArea, QScrollArea > QWidget > QWidget {
                        background-color: #0f111a;
                    }
                """)