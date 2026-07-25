import os
import psutil

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
)

from src.gui.widgets.stat_card import StatCard


class LiveMonitorPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("LiveMonitorPage")

        # ==================================================
        # Layout principal
        # ==================================================

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # ==================================================
        # Titre
        # ==================================================

        self.title = QLabel("Supervision en temps réel")
        self.title.setObjectName("PageTitle")

        self.subtitle = QLabel(
            "Surveillez l'utilisation du processeur, de la mémoire et du disque en temps réel."
        )
        self.subtitle.setObjectName("PageSubtitle")
        self.subtitle.setWordWrap(True)

        main_layout.addWidget(self.title)
        main_layout.addWidget(self.subtitle)

        # ==================================================
        # Grille des cartes
        # ==================================================

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(20)

        self.cpu = StatCard("🧠 CPU")
        self.ram = StatCard("💾 RAM")
        self.disk = StatCard("💽 Disque")

        grid.addWidget(self.cpu, 0, 0)
        grid.addWidget(self.ram, 0, 1)
        grid.addWidget(self.disk, 1, 0)

        # Réserve la place pour une future carte
        # (Température, Réseau ou GPU)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        main_layout.addLayout(grid)
        main_layout.addStretch()

        self.setLayout(main_layout)

        # ==================================================
        # Rafraîchissement automatique
        # ==================================================

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

        self.update_stats()

    # ==================================================
    # Mise à jour des statistiques
    # ==================================================

    def update_stats(self):

        stats = {
            self.cpu: int(psutil.cpu_percent(interval=None)),
            self.ram: int(psutil.virtual_memory().percent),
            self.disk: int(psutil.disk_usage(os.path.abspath(os.sep)).percent),
        }

        for card, value in stats.items():
            card.set_value(value)