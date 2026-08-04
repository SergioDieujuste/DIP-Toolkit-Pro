import os
import psutil

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QScrollArea,
)

from src.gui.widgets.stat_card import StatCard


class LiveMonitorPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("LiveMonitorPage")

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

        self.title = QLabel("Supervision en temps réel")
        self.title.setObjectName("PageTitle")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")

        self.subtitle = QLabel(
            "Surveillez l'utilisation du processeur, de la mémoire et du disque en temps réel."
        )
        self.subtitle.setObjectName("PageSubtitle")
        self.subtitle.setStyleSheet("font-size: 12px; color: #a0a5b5;")
        self.subtitle.setWordWrap(True)

        title_layout.addWidget(self.title)
        title_layout.addWidget(self.subtitle)

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

        self.cpu = StatCard("🧠 CPU")
        self.ram = StatCard("💾 RAM")
        self.disk = StatCard("💽 Disque")

        grid.addWidget(self.cpu, 0, 0)
        grid.addWidget(self.ram, 0, 1)
        grid.addWidget(self.disk, 1, 0)

        # Réserve la place pour une future carte (Température, Réseau ou GPU)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        scroll_layout.addLayout(grid)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # ==================================================
        # Rafraîchissement automatique
        # ==================================================

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

        self.update_stats()

        self.setStyleSheet("""
                    QWidget#DashboardPage, QScrollArea, QScrollArea > QWidget > QWidget {
                        background-color: #0f111a;
                    }
                """)

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