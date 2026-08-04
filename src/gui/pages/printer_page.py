import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QThread, Signal

# Import des modules créés précédemment
try:
    from src.diagnostics.printer_info import PrinterInfo
except ModuleNotFoundError:
    # Fallback si le chemin relatif diffère
    from diagnostics.printer_info import PrinterInfo

# Import du widget carte
try:
    from src.gui.widgets.printer_card import PrinterCard
except ModuleNotFoundError:
    from widgets.printer_card import PrinterCard


class PrinterWorker(QThread):
    """Thread secondaire pour exécuter la requête PowerShell sans figer l'interface."""
    finished = Signal(list)

    def run(self):
        printers = PrinterInfo.get_printers()
        self.finished.emit(printers)


class PrinterPage(QWidget):
    """Page affichant la liste des imprimantes installées sur le système."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("printer_page")
        
        self.worker = None
        self.init_ui()
        self.load_printers()

        self.setStyleSheet("""
                    QWidget#DashboardPage, QScrollArea, QScrollArea > QWidget > QWidget {
                        background-color: #0f111a;
                    }
                """)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ----------------------------------------------------
        # 1. EN-TÊTE DE LA PAGE (Titre + Bouton Actualiser)
        # ----------------------------------------------------
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title_label = QLabel("Imprimantes & Périphériques")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        
        subtitle_label = QLabel("Gestion et état des imprimantes connectées ou réseau")
        subtitle_label.setStyleSheet("font-size: 12px; color: #a0a5b5;")

        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        # Bouton Actualiser
        self.refresh_btn = QPushButton(" Actualiser")
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e222d;
                color: #00adb5;
                border: 1px solid #00adb5;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00adb5;
                color: #ffffff;
            }
            QPushButton:disabled {
                border-color: #4c566a;
                color: #4c566a;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_printers)
        header_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(header_layout)

        # ----------------------------------------------------
        # 2. ZONE DÉFILANTE (SCROLL AREA) POUR LES CARTES
        # ----------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

    def load_printers(self):
        """Lance la récupération asynchrone des imprimantes."""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText(" Recherche...")

        # Vider la liste actuelle
        self._clear_cards()

        # Message d'attente
        loading_label = QLabel("Détection des imprimantes en cours...")
        loading_label.setObjectName("loading_label")
        loading_label.setStyleSheet("color: #a0a5b5; font-size: 14px; font-style: italic;")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cards_layout.addWidget(loading_label)

        # Lancer le thread en arrière-plan
        self.worker = PrinterWorker()
        self.worker.finished.connect(self._on_printers_loaded)
        self.worker.start()

    def _on_printers_loaded(self, printers: list):
        """Callback exécutée une fois les données récupérées."""
        self._clear_cards()
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText(" Actualiser")

        if not printers:
            empty_label = QLabel("Aucune imprimante détectée sur ce système.")
            empty_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty_label)
            return

        # Ajouter chaque imprimante sous forme de carte
        for printer in printers:
            card = PrinterCard(printer)
            self.cards_layout.addWidget(card)

    def _clear_cards(self):
        """Supprime tous les widgets enfants du layout de la liste."""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()