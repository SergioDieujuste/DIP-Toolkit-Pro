from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class SecurityCard(QFrame):
    """Widget de carte personnalisée pour afficher un contrôle de sécurité."""

    def __init__(self, check_data: dict, parent=None):
        super().__init__(parent)
        self.check_data = check_data
        self.setObjectName("security_card")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        # ----------------------------------------------------
        # 1. En-tête : Titre du test + Badge de Statut
        # ----------------------------------------------------
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # Titre du contrôle (ex: Pare-feu Windows)
        title_label = QLabel(self.check_data.get("title", "Contrôle de sécurité"))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        # Détermination de la couleur et du texte du badge
        status = self.check_data.get("status", "Inconnu")
        color_type = self.check_data.get("color", "orange")

        if color_type == "green" or status == "OK":
            status_color = "#2ecc71"  # Vert
            status_symbol = "✔ OK"
        elif color_type == "red" or status == "Danger":
            status_color = "#e74c3c"  # Rouge
            status_symbol = "✖ DANGER"
        else:
            status_color = "#f39c12"  # Orange / Avertissement
            status_symbol = "⚠ AVERTISSEMENT"

        status_label = QLabel(status_symbol)
        status_label.setStyleSheet(
            f"color: {status_color}; font-weight: bold; font-size: 12px; "
            f"border: 1px solid {status_color}; border-radius: 4px; padding: 2px 8px;"
        )
        top_layout.addWidget(status_label)

        layout.addLayout(top_layout)

        # ----------------------------------------------------
        # 2. Description / Détails du test
        # ----------------------------------------------------
        details_text = self.check_data.get("details", "")
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_label.setStyleSheet("color: #a0a5b5; font-size: 12px;")

        layout.addWidget(details_label)

        # Style du conteneur QFrame
        self.setStyleSheet("""
            QFrame#security_card {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#security_card:hover {
                border: 1px solid #00adb5;
            }
        """)