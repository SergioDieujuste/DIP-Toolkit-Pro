from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QScrollArea
)

from src.gui.info_card import InfoCard
from src.utils.system_info import get_system_info


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("DashboardPage")

        infos = get_system_info()

        # ==================================================
        # Layout principal
        # ==================================================

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ==================================================
        # En-tête (Titre & Sous-titre)
        # ==================================================

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("Tableau de bord")
        title.setObjectName("PageTitle")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")

        subtitle = QLabel(
            "Vue d'ensemble de votre ordinateur et des informations système."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setStyleSheet("font-size: 12px; color: #a0a5b5;")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        main_layout.addLayout(title_layout)

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
        # Grille des cartes
        # ==================================================

        grid = QGridLayout()
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(15)

        self.pc_card = InfoCard(
            "💻 Ordinateur",
            infos["computer"]
        )

        self.windows_card = InfoCard(
            "🪟 Windows",
            infos["windows"]
        )

        self.cpu_card = InfoCard(
            "⚙️ Processeur",
            infos["processor"]
        )

        self.ram_card = InfoCard(
            "🧠 RAM",
            infos["ram"]
        )

        self.disk_card = InfoCard(
            "💾 Disque",
            infos["disk"]
        )

        grid.addWidget(self.pc_card, 0, 0)
        grid.addWidget(self.windows_card, 0, 1)

        grid.addWidget(self.cpu_card, 1, 0)
        grid.addWidget(self.ram_card, 1, 1)

        grid.addWidget(self.disk_card, 2, 0)

        scroll_layout.addLayout(grid)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.setStyleSheet("""
            QWidget#DashboardPage, QScrollArea, QScrollArea > QWidget > QWidget {
                background-color: #0f111a;
            }
        """)