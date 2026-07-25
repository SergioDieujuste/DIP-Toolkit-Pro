from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QProgressBar,
)


class DiskCard(QFrame):

    def __init__(self, disk):
        super().__init__()

        self.setObjectName("DiskCard")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # ==========================================
        # Nom du disque
        # ==========================================

        self.title = QLabel(f"💾 {disk['name']}")
        self.title.setObjectName("DiskTitle")
        self.title.setAlignment(Qt.AlignCenter)

        # ==========================================
        # Barre d'utilisation
        # ==========================================

        self.progress = QProgressBar()
        self.progress.setObjectName("DiskProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(disk["percent"])

        # ==========================================
        # Pourcentage
        # ==========================================

        self.percent = QLabel(f"{disk['percent']} % utilisé")
        self.percent.setObjectName("DiskPercent")
        self.percent.setAlignment(Qt.AlignCenter)

        # ==========================================
        # Informations
        # ==========================================

        self.total = QLabel(f"Capacité : {disk['total']} Go")
        self.total.setObjectName("DiskInfo")

        self.used = QLabel(f"Utilisé : {disk['used']} Go")
        self.used.setObjectName("DiskInfo")

        self.free = QLabel(f"Libre : {disk['free']} Go")
        self.free.setObjectName("DiskInfo")

        self.fs = QLabel(f"Système de fichiers : {disk['filesystem']}")
        self.fs.setObjectName("DiskInfo")

        # ==========================================
        # Ajout des widgets
        # ==========================================

        layout.addWidget(self.title)
        layout.addWidget(self.progress)
        layout.addWidget(self.percent)

        layout.addSpacing(10)

        layout.addWidget(self.total)
        layout.addWidget(self.used)
        layout.addWidget(self.free)
        layout.addWidget(self.fs)

        layout.addStretch()

        self.setLayout(layout)