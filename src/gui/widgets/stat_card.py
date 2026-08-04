from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QProgressBar
)
from PySide6.QtCore import Qt


class StatCard(QFrame):

    def __init__(self, titre):
        super().__init__()

        self.setObjectName("StatCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # ----------------------------------------------------
        # 1. TITRE DE LA CARTE
        # ----------------------------------------------------
        self.title = QLabel(titre)
        self.title.setObjectName("CardTitle")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("""
            font-weight: bold; 
            font-size: 14px; 
            color: #00adb5;
        """)

        # ----------------------------------------------------
        # 2. VALEUR EN POURCENTAGE
        # ----------------------------------------------------
        self.value = QLabel("0 %")
        self.value.setObjectName("CardValue")
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #ffffff;
        """)

        # ----------------------------------------------------
        # 3. BARRE DE PROGRESSION
        # ----------------------------------------------------
        self.progress = QProgressBar()
        self.progress.setObjectName("CardProgress")
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #141721;
                border: 1px solid #2e3440;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #00adb5;
                border-radius: 3px;
            }
        """)

        # ----------------------------------------------------
        # 4. STATUT / BADGE
        # ----------------------------------------------------
        self.status = QLabel("Normal")
        self.status.setObjectName("CardStatus")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setProperty("state", "normal")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)

        # ----------------------------------------------------
        # 5. STYLE DE LA CARTE (SOMBRE & TURQUOISE)
        # ----------------------------------------------------
        self.setStyleSheet("""
            QFrame#StatCard {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#StatCard:hover {
                border: 1px solid #00adb5;
            }
        """)

        self._update_status_style("normal")

    def set_value(self, valeur):
        self.progress.setValue(valeur)
        self.value.setText(f"{valeur} %")

        if valeur < 50:
            state = "normal"
            text = "Normal"
        elif valeur < 80:
            state = "warning"
            text = "Élevé"
        else:
            state = "danger"
            text = "Critique"

        self.status.setText(text)
        self.status.setProperty("state", state)
        self._update_status_style(state)

    def _update_status_style(self, state):
        """Met à jour dynamiquement la couleur du badge de statut."""
        colors = {
            "normal": ("#2ecc71", "#1b382b"),   # Vert
            "warning": ("#f39c12", "#3d2e14"),  # Orange
            "danger": ("#e74c3c", "#3d1c1d")    # Rouge
        }
        text_color, bg_color = colors.get(state, colors["normal"])

        self.status.setStyleSheet(f"""
            color: {text_color};
            background-color: {bg_color};
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: bold;
        """)