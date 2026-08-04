from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout
)


class NetworkCard(QFrame):

    def __init__(self, infos):
        super().__init__()

        self.setObjectName("NetworkCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # ----------------------------------------------------
        # 1. TITRE DE LA CARTE
        # ----------------------------------------------------
        title = QLabel("🌐 Informations réseau")
        title.setObjectName("InfoCardTitle")
        title.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            color: #00adb5; 
            border-bottom: 1px solid #2e3440; 
            padding-bottom: 6px;
        """)
        layout.addWidget(title)

        # ----------------------------------------------------
        # 2. CHAMPS D'INFORMATIONS RÉSEAU
        # ----------------------------------------------------
        champs = [
            ("Nom du PC", infos.get("hostname", "Inconnu")),
            ("Adresse IPv4", infos.get("ip", "Inconnue")),
            ("Carte réseau", infos.get("interface", "Inconnue")),
            ("Adresse MAC", infos.get("mac", "Inconnue")),
        ]

        for nom, valeur in champs:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            key_label = QLabel(f"{nom} :")
            key_label.setStyleSheet("color: #a0a5b5; font-size: 12px; font-weight: bold;")

            val_label = QLabel(str(valeur))
            val_label.setStyleSheet("color: #ffffff; font-size: 12px;")
            val_label.setWordWrap(True)

            row_layout.addWidget(key_label)
            row_layout.addWidget(val_label, stretch=1)

            layout.addLayout(row_layout)

        layout.addStretch()

        # ----------------------------------------------------
        # 3. STYLE DE LA CARTE (SOMBRE & TURQUOISE)
        # ----------------------------------------------------
        self.setStyleSheet("""
            QFrame#NetworkCard {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#NetworkCard:hover {
                border: 1px solid #00adb5;
            }
        """)