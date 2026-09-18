import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QMessageBox, QFileDialog
)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class ReportCard(QWidget):
    def __init__(self, parent=None, system_info_data=None):
        super().__init__(parent)
        self.system_info = system_info_data or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Style de la carte
        self.setStyleSheet("""
            ReportCard {
                background-color: #1a1d2d;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QTextEdit {
                background-color: #0f111a;
                border: 1px solid #2e344e;
                border-radius: 5px;
                color: #ffffff;
                padding: 8px;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)

        # Champs du formulaire
        layout.addWidget(QLabel("<b>Informations Client & Intervention</b>"))

        self.input_client = QLineEdit()
        self.input_client.setPlaceholderText("Nom du client / Entreprise")
        layout.addWidget(self.input_client)

        self.input_serial = QLineEdit()
        self.input_serial.setPlaceholderText("N° de Série / Tag Machine")
        layout.addWidget(self.input_serial)

        self.input_tech = QLineEdit()
        self.input_tech.setPlaceholderText("Nom du Technicien")
        layout.addWidget(self.input_tech)

        self.input_issue = QTextEdit()
        self.input_issue.setPlaceholderText("Observations / Travaux effectués...")
        self.input_issue.setMaximumHeight(100)
        layout.addWidget(self.input_issue)

        # Bouton d'action
        self.btn_generate = QPushButton("📄 Générer le Rapport PDF")
        self.btn_generate.clicked.connect(self.generate_pdf)
        layout.addWidget(self.btn_generate)

    def generate_pdf(self):
        # Récupération et nettoyage du nom du client
        client_name = self.input_client.text().strip()
        if client_name:
            # Remplace les espaces et caractères spéciaux pour éviter les bugs de fichier
            safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '_', '-')).strip()
            default_filename = f"Rapport_Intervention_{safe_client_name}.pdf"
        else:
            default_filename = "Rapport_Intervention.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le rapport PDF", default_filename, "Fichiers PDF (*.pdf)"
        )
        if not file_path:
            return

        doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        story = []

        # Titre
        title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1E3A8A'))
        story.append(Paragraph("DIP Toolkit Pro - Rapport d'Intervention", title_style))
        story.append(Spacer(1, 15))

        # Métadonnées
        info_data = [
            ["Client :", self.input_client.text() or "N/A", "Technicien :", self.input_tech.text() or "N/A"],
            ["N° de Série :", self.input_serial.text() or "N/A", "Date :", "Aujourd'hui"]
        ]
        t_info = Table(info_data, colWidths=[80, 170, 80, 170])
        t_info.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 15))

        # Travaux réalisés
        story.append(Paragraph("<b>Observations & Travaux effectués :</b>", styles['Heading2']))
        story.append(Paragraph(self.input_issue.toPlainText() or "Aucune note saisie.", styles['Normal']))
        story.append(Spacer(1, 15))

        # Infos système
        story.append(Paragraph("<b>Informations Systèmes Détectées :</b>", styles['Heading2']))
        sys_data = [["Propriété", "Valeur"]]
        for k, v in self.system_info.items():
            sys_data.append([str(k), str(v)])

        if len(sys_data) == 1:
            sys_data.append(["Système", "Données non chargées"])

        t_sys = Table(sys_data, colWidths=[150, 330])
        t_sys.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0,0), (1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
        ]))
        story.append(t_sys)

        try:
            doc.build(story)
            QMessageBox.information(self, "Succès", "Rapport PDF généré avec succès !")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Échec de la génération : {e}")