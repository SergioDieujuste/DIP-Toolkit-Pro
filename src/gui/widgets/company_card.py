from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from src.utils.company import load_company, logo_path, save_company
from src.utils.paths import resource_path

INPUT_STYLE = """
    QLineEdit {
        background-color: #141721;
        color: #ffffff;
        border: 1px solid #2e3440;
        padding: 6px 10px;
        border-radius: 5px;
    }
    QLineEdit:focus { border: 1px solid #00adb5; }
"""

SECONDARY_BUTTON_STYLE = """
    QPushButton {
        background-color: #141721;
        color: #00adb5;
        border: 1px solid #00adb5;
        padding: 6px 12px;
        border-radius: 5px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #00adb5; color: #ffffff; }
"""


class CompanyCard(QFrame):
    """Nom, logo et coordonnées de l'entreprise affichés sur les rapports clients."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("company_card")

        # None = logo inchangé, "" = revenir au logo DIP, sinon chemin d'un nouveau logo
        self._logo_source = None
        self.init_ui()
        self._load_values()

    # ------------------------------------------------------------------
    def _field(self, label_text, placeholder=""):
        box = QVBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("color: #a0a5b5; font-size: 12px; font-weight: bold;")
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        edit.setStyleSheet(INPUT_STYLE)
        box.addWidget(label)
        box.addWidget(edit)
        return box, edit

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(15)

        intro = QLabel("Ces informations apparaissent en en-tête de chaque rapport PDF remis au client.")
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #a0a5b5; font-size: 12px;")
        layout.addWidget(intro)

        name_box, self.name_input = self._field("Nom de l'entreprise :", "Ex: Dépannage Informatique Plus")
        tagline_box, self.tagline_input = self._field(
            "Titre du rapport :", "Ex: Rapport de diagnostic informatique")
        layout.addLayout(name_box)
        layout.addLayout(tagline_box)

        row1 = QHBoxLayout()
        row1.setSpacing(15)
        phone_box, self.phone_input = self._field("Téléphone :", "Ex: 01 23 45 67 89")
        email_box, self.email_input = self._field("E-mail :", "Ex: contact@exemple.fr")
        row1.addLayout(phone_box)
        row1.addLayout(email_box)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(15)
        web_box, self.website_input = self._field("Site web :", "Ex: www.exemple.fr")
        addr_box, self.address_input = self._field("Adresse :", "Ex: 12 rue des Lilas, 91220 Brétigny")
        row2.addLayout(web_box)
        row2.addLayout(addr_box)
        layout.addLayout(row2)

        # ---------------- Logo ----------------
        logo_label = QLabel("Logo (PNG ou JPG) :")
        logo_label.setStyleSheet("color: #a0a5b5; font-size: 12px; font-weight: bold;")
        layout.addWidget(logo_label)

        logo_row = QHBoxLayout()
        logo_row.setSpacing(15)

        self.logo_preview = QLabel()
        self.logo_preview.setFixedSize(220, 90)
        self.logo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_preview.setStyleSheet(
            "background-color: #141721; border: 1px solid #2e3440; border-radius: 5px;")
        logo_row.addWidget(self.logo_preview)

        logo_buttons = QVBoxLayout()
        choose_btn = QPushButton("Choisir un logo...")
        choose_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        choose_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        choose_btn.clicked.connect(self._choose_logo)

        reset_btn = QPushButton("Revenir au logo DIP")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)
        reset_btn.clicked.connect(self._reset_logo)

        logo_buttons.addWidget(choose_btn)
        logo_buttons.addWidget(reset_btn)
        logo_buttons.addStretch()
        logo_row.addLayout(logo_buttons)
        logo_row.addStretch()
        layout.addLayout(logo_row)

        # ---------------- Enregistrer ----------------
        self.save_btn = QPushButton(" Enregistrer les informations de l'entreprise")
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
        self.save_btn.clicked.connect(self._save)
        layout.addWidget(self.save_btn)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        self.setStyleSheet("""
            QFrame#company_card {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
        """)

    # ------------------------------------------------------------------
    def _load_values(self):
        company = load_company()
        self.name_input.setText(company["name"])
        self.tagline_input.setText(company["tagline"])
        self.phone_input.setText(company["phone"])
        self.email_input.setText(company["email"])
        self.website_input.setText(company["website"])
        self.address_input.setText(company["address"])
        self._logo_source = None
        self._show_logo(logo_path(company))

    def _show_logo(self, path):
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self.logo_preview.setText("Aperçu indisponible")
            return
        self.logo_preview.setPixmap(
            pixmap.scaled(200, 80, Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation))

    def _say(self, message, ok):
        color = "#2ecc71" if ok else "#e74c3c"
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: bold;")
        self.status_label.setVisible(True)

    def _choose_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choisir un logo", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        if QPixmap(path).isNull():
            self._say("Ce fichier n'est pas une image valide.", False)
            return
        self._logo_source = path
        self._show_logo(path)
        self._say("Logo sélectionné : cliquez sur « Enregistrer » pour l'appliquer.", True)

    def _reset_logo(self):
        self._logo_source = ""
        self._show_logo(resource_path("assets/logo/logo-web-transparent.png"))
        self._say("Logo DIP rétabli : cliquez sur « Enregistrer » pour l'appliquer.", True)

    def _save(self):
        values = {
            "name": self.name_input.text(),
            "tagline": self.tagline_input.text(),
            "phone": self.phone_input.text(),
            "email": self.email_input.text(),
            "website": self.website_input.text(),
            "address": self.address_input.text(),
        }
        ok, message = save_company(values, self._logo_source)
        self._say(message, ok)
        if ok:
            self._load_values()
            self._say(message, True)
