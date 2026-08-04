from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal

# Imports des modules avec gestion des chemins
try:
    from src.diagnostics.security_info import SecurityInfo
    from src.gui.widgets.security_card import SecurityCard
except ModuleNotFoundError:
    from diagnostics.security_info import SecurityInfo
    from widgets.security_card import SecurityCard


class SecurityWorker(QThread):
    """Thread secondaire pour exécuter les vérifications de sécurité sans figer l'interface."""
    finished = Signal(list)

    def run(self):
        checks = SecurityInfo.get_security_status()
        self.finished.emit(checks)


class SecurityPage(QWidget):
    """Page affichant le bilan de sécurité système (Pare-feu, Antivirus, UAC...)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("security_page")

        self.worker = None
        self.init_ui()
        self.load_security_checks()

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
        title_label = QLabel("Sécurité & Protection")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")

        subtitle_label = QLabel("État du pare-feu, de l'antivirus et du contrôle d'accès")
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
        self.refresh_btn.clicked.connect(self.load_security_checks)
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

    def load_security_checks(self):
        """Lance l'analyse asynchrone des paramètres de sécurité."""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText(" Vérification...")

        self._clear_cards()

        # Message pendant la vérification
        loading_label = QLabel("Analyse des protections du système...")
        loading_label.setStyleSheet("color: #a0a5b5; font-size: 14px; font-style: italic;")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cards_layout.addWidget(loading_label)

        # Lancement du Worker Thread
        self.worker = SecurityWorker()
        self.worker.finished.connect(self._on_checks_loaded)
        self.worker.start()

    def _on_checks_loaded(self, checks: list):
        """Callback après réception des données."""
        self._clear_cards()
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText(" Actualiser")

        if not checks:
            empty_label = QLabel("Aucun module de sécurité analysable.")
            empty_label.setStyleSheet("color: #e74c3c; font-size: 14px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.addWidget(empty_label)
            return

        for check in checks:
            card = SecurityCard(check)
            self.cards_layout.addWidget(card)

    def _clear_cards(self):
        """Vide le conteneur des cartes."""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()