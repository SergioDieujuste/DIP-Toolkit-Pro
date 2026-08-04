import os
import platform
from datetime import datetime

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class ReportInfo:
    """Classe chargée d'assembler et de générer le rapport PDF d'intervention."""

    @staticmethod
    def generate_pdf(filepath: str, options: dict) -> tuple[bool, str]:
        """
        Génère un fichier PDF récapitulatif.
        options = {
            'client_name': str,
            'tech_name': str,
            'include_system': bool,
            'include_disks': bool,
            'include_network': bool,
            'include_security': bool,
            'include_printers': bool
        }
        """
        if not HAS_REPORTLAB:
            return False, "La bibliothèque 'reportlab' n'est pas installée. Lancez 'pip install reportlab'."

        try:
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=36,
                leftMargin=36,
                topMargin=36,
                bottomMargin=36
            )
            story = []
            styles = getSampleStyleSheet()

            # Styles personnalisés aux couleurs DIP (Sombre/Turquoise)
            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=22,
                textColor=colors.HexColor('#00adb5'),
                spaceAfter=6
            )
            subtitle_style = ParagraphStyle(
                'DocSubtitle',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#666666'),
                spaceAfter=15
            )
            heading_style = ParagraphStyle(
                'SectionHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1e222d'),
                spaceBefore=12,
                spaceAfter=6
            )
            body_style = ParagraphStyle(
                'Body',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#333333'),
                spaceAfter=4
            )

            # ----------------------------------------------------
            # 1. EN-TÊTE DU RAPPORT
            # ----------------------------------------------------
            story.append(Paragraph("Dépannage Informatique Plus", title_style))
            story.append(Paragraph("Rapport de Diagnostic & Intervention Système", subtitle_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#00adb5'), spaceAfter=15))

            # Table d'informations sur l'intervention
            date_str = datetime.now().strftime("%d/%m/%Y à %H:%M")
            info_data = [
                [Paragraph("<b>Client :</b>", body_style), Paragraph(options.get('client_name', 'Client Standard'), body_style)],
                [Paragraph("<b>Technicien :</b>", body_style), Paragraph(options.get('tech_name', 'Technicien DIP'), body_style)],
                [Paragraph("<b>Date de l'analyse :</b>", body_style), Paragraph(date_str, body_style)],
                [Paragraph("<b>Système d'exploitation :</b>", body_style), Paragraph(f"{platform.system()} {platform.release()} ({platform.architecture()[0]})", body_style)]
            ]
            info_table = Table(info_data, colWidths=[130, 380])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
                ('PADDING', (0,0), (-1,-1), 6),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e0e0e0')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 15))

            # ----------------------------------------------------
            # 2. SECTIONS DU RAPPORT SELON OPTIONS
            # ----------------------------------------------------
            if options.get('include_system', True):
                story.append(Paragraph("1. Supervision & Système", heading_style))
                story.append(Paragraph("Analyse globale des ressources CPU, RAM et performances de la machine.", body_style))
                story.append(Spacer(1, 8))

            if options.get('include_disks', True):
                story.append(Paragraph("2. Analyse des Disques", heading_style))
                story.append(Paragraph("Vérification de l'espace de stockage et de la santé des partitions de disque.", body_style))
                story.append(Spacer(1, 8))

            if options.get('include_network', True):
                story.append(Paragraph("3. Configuration Réseau", heading_style))
                story.append(Paragraph("Vérification des adresses IP (Locale/Publique) et connectivité passerelle.", body_style))
                story.append(Spacer(1, 8))

            if options.get('include_security', True):
                story.append(Paragraph("4. État de la Sécurité", heading_style))
                story.append(Paragraph("Bilan des protections système (Pare-feu Windows, Antivirus et UAC).", body_style))
                story.append(Spacer(1, 8))

            if options.get('include_printers', True):
                story.append(Paragraph("5. Périphériques & Imprimantes", heading_style))
                story.append(Paragraph("Liste des imprimantes configurées et vérification du statut en ligne.", body_style))
                story.append(Spacer(1, 8))

            # Pied de page
            story.append(Spacer(1, 20))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cccccc'), spaceAfter=10))
            story.append(Paragraph("<i>Document généré automatiquement par DIP Toolkit Pro.</i>", ParagraphStyle('Footer', parent=body_style, fontSize=8, textColor=colors.gray)))

            # Génération effective du PDF
            doc.build(story)
            return True, f"Rapport PDF généré avec succès dans :\n{filepath}"

        except Exception as e:
            return False, f"Erreur lors de la création du PDF : {e}"