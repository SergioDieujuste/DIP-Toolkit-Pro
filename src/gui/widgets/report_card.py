from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QCheckBox, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices

import os
import socket

# Import de la logique backend
from src.diagnostics.report_info import ReportInfo, default_filename
from src.diagnostics.settings_info import SettingsInfo


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
        self.tech_input.setText(SettingsInfo.load_settings().get("default_tech_name", ""))
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

        # Coordonnées du client (facultatives)
        contact_style = """
            QLineEdit {
                background-color: #141721;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 6px 10px;
                border-radius: 5px;
            }
            QLineEdit:focus { border: 1px solid #00adb5; }
        """
        contact_layout = QHBoxLayout()
        contact_layout.setSpacing(15)

        phone_box = QVBoxLayout()
        phone_label = QLabel("Téléphone du client (facultatif) :")
        phone_label.setStyleSheet("color: #a0a5b5; font-size: 11px;")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Ex: 06 12 34 56 78")
        self.phone_input.setStyleSheet(contact_style)
        phone_box.addWidget(phone_label)
        phone_box.addWidget(self.phone_input)

        email_box = QVBoxLayout()
        email_label = QLabel("E-mail du client (facultatif) :")
        email_label.setStyleSheet("color: #a0a5b5; font-size: 11px;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Ex: client@exemple.fr")
        self.email_input.setStyleSheet(contact_style)
        email_box.addWidget(email_label)
        email_box.addWidget(self.email_input)

        contact_layout.addLayout(phone_box)
        contact_layout.addLayout(email_box)
        layout.addLayout(contact_layout)

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

        self.cb_health = QCheckBox("Santé matérielle (disques SMART, batterie)")
        self.cb_health.setChecked(True)
        self.cb_health.setStyleSheet(checkbox_style)

        self.cb_updates = QCheckBox("Mises à jour Windows & pilotes (peut prendre jusqu'à 2 min)")
        self.cb_updates.setChecked(True)
        self.cb_updates.setStyleSheet(checkbox_style)

        self.cb_events = QCheckBox("Stabilité : écrans bleus et arrêts inattendus (7 jours)")
        self.cb_events.setChecked(True)
        self.cb_events.setStyleSheet(checkbox_style)

        layout.addWidget(self.cb_system)
        layout.addWidget(self.cb_disks)
        layout.addWidget(self.cb_network)
        layout.addWidget(self.cb_security)
        layout.addWidget(self.cb_printers)
        layout.addWidget(self.cb_health)
        layout.addWidget(self.cb_updates)
        layout.addWidget(self.cb_events)

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
        settings = SettingsInfo.load_settings()
        default_name = default_filename(
            self.client_input.text().strip(), socket.gethostname()
        )
        start_path = os.path.join(settings.get("default_export_dir", ""), default_name)
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le Rapport PDF",
            start_path,
            "Fichiers PDF (*.pdf)"
        )

        if not filepath:
            return

        options = {
            'client_name': self.client_input.text().strip() or "Client Standard",
            'client_phone': self.phone_input.text().strip(),
            'client_email': self.email_input.text().strip(),
            'tech_name': self.tech_input.text().strip() or "Technicien DIP",
            'include_system': self.cb_system.isChecked(),
            'include_disks': self.cb_disks.isChecked(),
            'include_network': self.cb_network.isChecked(),
            'include_security': self.cb_security.isChecked(),
            'include_printers': self.cb_printers.isChecked(),
            'include_health': self.cb_health.isChecked(),
            'include_updates': self.cb_updates.isChecked(),
            'include_events': self.cb_events.isChecked()
        }

        self.generate_btn.setEnabled(False)
        self.generate_btn.setText(" Analyse en cours (jusqu'à 2 min)...")
        self.status_label.setVisible(False)

        self.last_filepath = filepath
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

        # Ouvre le PDF pour que le technicien le relise avant de le remettre
        if success and getattr(self, "last_filepath", None):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_filepath))