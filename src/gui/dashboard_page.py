from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
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

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # ==================================================
        # Titre
        # ==================================================

        title = QLabel("Tableau de bord")
        title.setObjectName("PageTitle")

        subtitle = QLabel(
            "Vue d'ensemble de votre ordinateur et des informations système."
        )
        subtitle.setObjectName("PageSubtitle")
        subtitle.setWordWrap(True)

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # ==================================================
        # Grille des cartes
        # ==================================================

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)

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

        main_layout.addLayout(grid)
        main_layout.addStretch()

        self.setLayout(main_layout)