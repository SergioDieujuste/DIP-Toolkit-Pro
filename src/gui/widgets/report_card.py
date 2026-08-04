from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QCheckBox, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QThread, Signal

# Import de la logique backend
try:
    from src.diagnostics.report_info import ReportInfo
except ModuleNotFoundError:
    from diagnostics.report_info import ReportInfo


class ReportWorker(QThread):
    """Thread secondaire pour la génération du PDF."""
    finished = Signal(bool, str)

    def __init__(self, filepath: str, options: dict):
        super().__init__()
        self.filepath = filepath
        self.options = options

    def run(self):
        success, message = ReportInfo.generate_pdf(self.filepath, self.options)
        self.finished.emit(success, message)


class ReportCard(QFrame):
    """Widget de formulaire et d'options pour la génération de rapport PDF."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("report_card")

        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(15)

        # ----------------------------------------------------
        # 1. INFORMATIONS DU CLIENT & TECHNICIEN
        # ----------------------------------------------------
        info_title = QLabel("Informations de l'Intervention")
        info_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        layout.addWidget(info_title)

        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(15)

        # Nom du client
        client_box = QVBoxLayout()
        client_label = QLabel("Nom du Client / Entreprise :")
        client_label.setStyleSheet("color: #a0a5b5; font-size: 11px;")
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("Ex: Dupont Informatique")
        self.client_input.setStyleSheet("""
            QLineEdit {
                background-color: #141721;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 6px 10px;
                border-radius: 5px;
            }
            QLineEdit:focus { border: 1px solid #00adb5; }
        """)
        client_box.addWidget(client_label)
        client_box.addWidget(self.client_input)

        # Nom du technicien
        tech_box = QVBoxLayout()
        tech_label = QLabel("Nom du Technicien :")
        tech_label.setStyleSheet("color: #a0a5b5; font-size: 11px;")
        self.tech_input = QLineEdit()
        self.tech_input.setPlaceholderText("Ex: Technicien DIP")
        self.tech_input.setStyleSheet("""
            QLineEdit {
                background-color: #141721;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 6px 10px;
                border-radius: 5px;
            }
            QLineEdit:focus { border: 1px solid #00adb5; }
        """)
        tech_box.addWidget(tech_label)
        tech_box.addWidget(self.tech_input)

        inputs_layout.addLayout(client_box)
        inputs_layout.addLayout(tech_box)
        layout.addLayout(inputs_layout)

        # ----------------------------------------------------
        # 2. SECTIONS À INCLURE (CHECKBOXES)
        # ----------------------------------------------------
        sections_title = QLabel("Sections à Inclure dans le Rapport")
        sections_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF; margin-top: 10px;")
        layout.addWidget(sections_title)

        checkbox_style = """
            QCheckBox { color: #a0a5b5; font-size: 12px; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QCheckBox::indicator:checked { background-color: #00adb5; border-radius: 3px; }
        """

        self.cb_system = QCheckBox("Supervision & Santé Système")
        self.cb_system.setChecked(True)
        self.cb_system.setStyleSheet(checkbox_style)

        self.cb_disks = QCheckBox("Analyse des Disques")
        self.cb_disks.setChecked(True)
        self.cb_disks.setStyleSheet(checkbox_style)

        self.cb_network = QCheckBox("Configuration Réseau & IP")
        self.cb_network.setChecked(True)
        self.cb_network.setStyleSheet(checkbox_style)

        self.cb_security = QCheckBox("Bilan de Sécurité (Pare-feu / Antivirus)")
        self.cb_security.setChecked(True)
        self.cb_security.setStyleSheet(checkbox_style)

        self.cb_printers = QCheckBox("Imprimantes & Périphériques")
        self.cb_printers.setChecked(True)
        self.cb_printers.setStyleSheet(checkbox_style)

        layout.addWidget(self.cb_system)
        layout.addWidget(self.cb_disks)
        layout.addWidget(self.cb_network)
        layout.addWidget(self.cb_security)
        layout.addWidget(self.cb_printers)

        # ----------------------------------------------------
        # 3. BOUTON DE GÉNÉRATION & MESSAGE
        # ----------------------------------------------------
        self.generate_btn = QPushButton(" Générer le Rapport PDF")
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.setStyleSheet("""
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
            QPushButton:disabled { background-color: #3b4252; color: #a0a5b5; }
        """)
        self.generate_btn.clicked.connect(self._select_file_and_generate)
        layout.addWidget(self.generate_btn)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Style de la carte
        self.setStyleSheet("""
            QFrame#report_card {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
        """)

    def _select_file_and_generate(self):
        """Demande l'emplacement de sauvegarde et génère le PDF."""
        default_name = f"Rapport_DIP_{self.client_input.text().strip() or 'Client'}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le Rapport PDF",
            default_name,
            "Fichiers PDF (*.pdf)"
        )

        if not filepath:
            return

        options = {
            'client_name': self.client_input.text().strip() or "Client Standard",
            'tech_name': self.tech_input.text().strip() or "Technicien DIP",
            'include_system': self.cb_system.isChecked(),
            'include_disks': self.cb_disks.isChecked(),
            'include_network': self.cb_network.isChecked(),
            'include_security': self.cb_security.isChecked(),
            'include_printers': self.cb_printers.isChecked()
        }

        self.generate_btn.setEnabled(False)
        self.generate_btn.setText(" Génération en cours...")
        self.status_label.setVisible(False)

        self.worker = ReportWorker(filepath, options)
        self.worker.finished.connect(self._on_pdf_generated)
        self.worker.start()

    def _on_pdf_generated(self, success: bool, message: str):
        """Callback après la génération du PDF."""
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText(" Générer le Rapport PDF")

        color = "#2ecc71" if success else "#e74c3c"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold;")
        self.status_label.setVisible(True)