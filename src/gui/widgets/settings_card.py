from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QSpinBox, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt

# Import de la logique backend
try:
    from src.diagnostics.settings_info import SettingsInfo
except ModuleNotFoundError:
    from diagnostics.settings_info import SettingsInfo


class SettingsCard(QFrame):
    """Widget de carte pour la gestion des paramètres de l'application."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings_card")

        self.current_settings = SettingsInfo.load_settings()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(15)

        # Style réutilisable pour les champs
        input_style = """
            QLineEdit, QSpinBox {
                background-color: #141721;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 6px 10px;
                border-radius: 5px;
            }
            QLineEdit:focus, QSpinBox:focus { border: 1px solid #00adb5; }
        """

        # ----------------------------------------------------
        # 1. TECHNICIEN PAR DÉFAUT
        # ----------------------------------------------------
        tech_box = QVBoxLayout()
        tech_label = QLabel("Nom du technicien par défaut (pour les rapports) :")
        tech_label.setStyleSheet("color: #a0a5b5; font-size: 12px; font-weight: bold;")
        self.tech_input = QLineEdit()
        self.tech_input.setText(self.current_settings.get("default_tech_name", "Technicien DIP"))
        self.tech_input.setStyleSheet(input_style)
        tech_box.addWidget(tech_label)
        tech_box.addWidget(self.tech_input)
        layout.addLayout(tech_box)

        # ----------------------------------------------------
        # 2. FRÉQUENCE DE RAFRAÎCHISSEMENT (SUPERVISION)
        # ----------------------------------------------------
        refresh_box = QVBoxLayout()
        refresh_label = QLabel("Intervalle de rafraîchissement CPU/RAM (secondes) :")
        refresh_label.setStyleSheet("color: #a0a5b5; font-size: 12px; font-weight: bold;")
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(1, 10)
        self.refresh_spin.setValue(self.current_settings.get("auto_refresh_interval", 2))
        self.refresh_spin.setStyleSheet(input_style)
        refresh_box.addWidget(refresh_label)
        refresh_box.addWidget(self.refresh_spin)
        layout.addLayout(refresh_box)

        # ----------------------------------------------------
        # 3. DOSSIER D'EXPORTATION PAR DÉFAUT
        # ----------------------------------------------------
        dir_box = QVBoxLayout()
        dir_label = QLabel("Dossier d'enregistrement des rapports PDF :")
        dir_label.setStyleSheet("color: #a0a5b5; font-size: 12px; font-weight: bold;")

        dir_input_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setText(self.current_settings.get("default_export_dir", ""))
        self.dir_input.setStyleSheet(input_style)

        browse_btn = QPushButton("Parcourir...")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #141721;
                color: #00adb5;
                border: 1px solid #00adb5;
                padding: 6px 12px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #00adb5; color: #ffffff; }
        """)
        browse_btn.clicked.connect(self._browse_directory)

        dir_input_layout.addWidget(self.dir_input)
        dir_input_layout.addWidget(browse_btn)

        dir_box.addWidget(dir_label)
        dir_box.addLayout(dir_input_layout)
        layout.addLayout(dir_box)

        # ----------------------------------------------------
        # 4. BOUTON SAUVEGARDER & MSG DE CONFIRMATION
        # ----------------------------------------------------
        self.save_btn = QPushButton(" Enregistrer les paramètres")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00adb5;
                color: #ffffff;
                border: none;
                padding: 10px 18px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                margin-top: 10px;
            }
            QPushButton:hover { background-color: #00888f; }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        layout.addWidget(self.save_btn)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Style de la carte
        self.setStyleSheet("""
            QFrame#settings_card {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
        """)

    def _browse_directory(self):
        """Ouvre un sélecteur de dossier."""
        directory = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier d'export", self.dir_input.text()
        )
        if directory:
            self.dir_input.setText(directory)

    def _save_settings(self):
        """Enregistre les valeurs actuelles."""
        new_settings = {
            "default_tech_name": self.tech_input.text().strip(),
            "auto_refresh_interval": self.refresh_spin.value(),
            "default_export_dir": self.dir_input.text().strip(),
            "theme": "Sombre (Turquoise)"
        }

        success, message = SettingsInfo.save_settings(new_settings)
        color = "#2ecc71" if success else "#e74c3c"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        self.status_label.setVisible(True)