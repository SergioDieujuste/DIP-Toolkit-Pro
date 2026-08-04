from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class PrinterCard(QFrame):
    """Widget de carte personnalisée pour afficher une imprimante."""

    def __init__(self, printer_data: dict, parent=None):
        super().__init__(parent)
        self.printer_data = printer_data
        self.setObjectName("printer_card")

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        # ----------------------------------------------------
        # 1. En-tête : Nom de l'imprimante + Statut + Badge DÉFAUT
        # ----------------------------------------------------
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # Nom de l'imprimante
        name_label = QLabel(self.printer_data.get("name", "Imprimante inconnue"))
        name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        top_layout.addWidget(name_label)

        # Badge "Par défaut" si c'est le cas
        if self.printer_data.get("is_default", False):
            default_badge = QLabel("Par défaut")
            default_badge.setStyleSheet(
                "background-color: #00adb5; color: #ffffff; "
                "font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;"
            )
            top_layout.addWidget(default_badge)

        top_layout.addStretch()

        # Pastille & Texte de statut
        status_text = self.printer_data.get("status", "Inconnu")
        is_offline = self.printer_data.get("offline", False)

        if is_offline or status_text == "Hors ligne":
            status_color = "#e74c3c"  # Rouge
            status_text = "Hors ligne"
        elif "Prête" in status_text or status_text == "Idle":
            status_color = "#2ecc71"  # Vert
        else:
            status_color = "#f39c12"  # Orange (Impression en cours, avertissement...)

        status_label = QLabel(f"● {status_text}")
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold; font-size: 12px;")
        top_layout.addWidget(status_label)

        layout.addLayout(top_layout)

        # ----------------------------------------------------
        # 2. Détails : Pilote & Port
        # ----------------------------------------------------
        details_layout = QHBoxLayout()
        details_layout.setSpacing(20)

        driver_text = f"<b>Pilote :</b> {self.printer_data.get('driver', 'N/A')}"
        driver_label = QLabel(driver_text)
        driver_label.setStyleSheet("color: #a0a5b5; font-size: 11px;")

        port_text = f"<b>Port :</b> {self.printer_data.get('port', 'N/A')}"
        port_label = QLabel(port_text)
        port_label.setStyleSheet("color: #a0a5b5; font-size: 11px;")

        details_layout.addWidget(driver_label)
        details_layout.addWidget(port_label)
        details_layout.addStretch()

        layout.addLayout(details_layout)

        # Style de la carte / conteneur
        self.setStyleSheet("""
            QFrame#printer_card {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#printer_card:hover {
                border: 1px solid #00adb5;
            }
        """)