from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QScrollArea,
    QWidget,
    QLineEdit,
)

from .base_page import BasePage


class KnowledgePage(BasePage):

    def __init__(self):
        super().__init__(
            "📚 Base de connaissances",
            "Guides de dépannage, commandes utiles et fiches mémos pour techniciens."
        )

        # ----------------------------------------------------
        # Zone défilante
        # ----------------------------------------------------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(15)

        # ----------------------------------------------------
        # Barre de recherche
        # ----------------------------------------------------
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Rechercher une commande ou une procédure...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #1e222d;
                color: #ffffff;
                border: 1px solid #2e3440;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00adb5;
            }
        """)
        self.search_bar.textChanged.connect(self.filter_articles)
        self.scroll_layout.addWidget(self.search_bar)

        # ----------------------------------------------------
        # Données de la base de connaissances (Articles)
        # ----------------------------------------------------
        self.articles = [
            {
                "titre": "🛠️ Commandes Réseau Utiles (CMD)",
                "categorie": "Réseau",
                "contenu": (
                    "• <b>ipconfig /flushdns</b> : Vider le cache DNS\n"
                    "• <b>netsh winsock reset</b> : Réinitialiser le catalogue Winsock\n"
                    "• <b>ping -t 8.8.8.8</b> : Ping continu vers les serveurs Google\n"
                    "• <b>nslookup nom-de-domaine.com</b> : Interroger le serveur DNS"
                )
            },
            {
                "titre": "🖨️ Problèmes d'impression fréquents",
                "categorie": "Imprimante",
                "contenu": (
                    "1. <b>Relancer le spooler :</b> net stop spooler && net start spooler\n"
                    "2. <b>Vider le dossier d'impression :</b> C:\\Windows\\System32\\spool\\PRINTERS\n"
                    "3. Déconnecter/reconnecter le câble USB ou tester un ping sur l'IP de l'imprimante."
                )
            },
            {
                "titre": "💻 Réparation système Windows",
                "categorie": "Maintenance",
                "contenu": (
                    "• <b>sfc /scannow</b> : Vérifier et réparer les fichiers système corrompus\n"
                    "• <b>DISM /Online /Cleanup-Image /RestoreHealth</b> : Réparer l'image de Windows\n"
                    "• <b>chkdsk C: /f /r</b> : Analyser et réparer les erreurs de disque au redémarrage"
                )
            }
        ]

        self.cards = []
        for art in self.articles:
            card = self.create_article_card(art["titre"], art["categorie"], art["contenu"])
            self.scroll_layout.addWidget(card)
            self.cards.append((art, card))

        self.scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        self.content_layout.addWidget(scroll_area)

    def create_article_card(self, titre, categorie, contenu):
        """Crée une carte visuelle pour un article."""
        card = QFrame()
        card.setObjectName("KnowledgeCard")
        card.setStyleSheet("""
            QFrame#KnowledgeCard {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#KnowledgeCard:hover {
                border: 1px solid #00adb5;
            }
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        # Header de la carte
        header = QHBoxLayout()
        title_lbl = QLabel(titre)
        title_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #00adb5;")

        cat_lbl = QLabel(categorie)
        cat_lbl.setStyleSheet("""
            color: #a0a5b5; 
            background-color: #141721; 
            padding: 2px 8px; 
            border-radius: 4px; 
            font-size: 11px; 
            font-weight: bold;
        """)

        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(cat_lbl)

        content_lbl = QLabel(contenu)
        content_lbl.setStyleSheet("color: #ffffff; font-size: 12px; line-height: 1.4;")
        content_lbl.setTextFormat(Qt.TextFormat.RichText)
        content_lbl.setWordWrap(True)

        layout.addLayout(header)
        layout.addWidget(content_lbl)

        return card

    def filter_articles(self, text):
        """Filtre les cartes selon la recherche de l'utilisateur."""
        query = text.lower()
        for art, card in self.cards:
            match = (
                query in art["titre"].lower()
                or query in art["categorie"].lower()
                or query in art["contenu"].lower()
            )
            card.setVisible(match)