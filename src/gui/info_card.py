from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout
)
from PySide6.QtCore import Qt


class InfoCard(QFrame):

    def __init__(self, titre: str, valeur):
        super().__init__()

        self.setObjectName("InfoCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # ----------------------------------------------------
        # 1. TITRE DE LA CARTE
        # ----------------------------------------------------
        self.title = QLabel(titre)
        self.title.setObjectName("InfoCardTitle")
        self.title.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            color: #00adb5; 
            border-bottom: 1px solid #2e3440; 
            padding-bottom: 6px;
        """)
        layout.addWidget(self.title)

        # ----------------------------------------------------
        # 2. CONTENU (Dictionnaire ou Texte brut)
        # ----------------------------------------------------
        if isinstance(valeur, dict):
            # Si valeur est un dictionnaire, on affiche chaque clé/valeur ligne par ligne
            for key, val in valeur.items():
                row_layout = QHBoxLayout()
                row_layout.setSpacing(8)

                key_label = QLabel(f"{key} :")
                key_label.setStyleSheet("color: #a0a5b5; font-size: 12px; font-weight: bold;")

                val_label = QLabel(str(val))
                val_label.setStyleSheet("color: #ffffff; font-size: 12px;")
                val_label.setWordWrap(True)

                row_layout.addWidget(key_label)
                row_layout.addWidget(val_label, stretch=1)
                layout.addLayout(row_layout)
        else:
            # Si c'est du texte simple
            self.value = QLabel(str(valeur))
            self.value.setObjectName("InfoCardValue")
            self.value.setStyleSheet("color: #ffffff; font-size: 13px;")
            self.value.setWordWrap(True)
            layout.addWidget(self.value)

        layout.addStretch()

        # ----------------------------------------------------
        # 3. FEUILLE DE STYLE QSS INTÉGRÉE
        # ----------------------------------------------------
        self.setStyleSheet("""
            QFrame#InfoCard {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#InfoCard:hover {
                border: 1px solid #00adb5;
            }
        """)