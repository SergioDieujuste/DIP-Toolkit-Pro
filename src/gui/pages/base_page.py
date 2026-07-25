from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
)
from PySide6.QtCore import Qt


class BasePage(QWidget):

    def __init__(self, titre, sous_titre=""):
        super().__init__()

        self.setObjectName("BasePage")

        # ==========================================
        # Layout principal
        # ==========================================

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # ==========================================
        # Titre
        # ==========================================

        self.title = QLabel(titre)
        self.title.setObjectName("PageTitle")

        main_layout.addWidget(self.title)

        # ==========================================
        # Sous-titre (optionnel)
        # ==========================================

        if sous_titre:

            self.subtitle = QLabel(sous_titre)
            self.subtitle.setObjectName("PageSubtitle")
            self.subtitle.setWordWrap(True)

            main_layout.addWidget(self.subtitle)

        # ==========================================
        # Zone où les pages ajoutent leur contenu
        # ==========================================

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(20)

        main_layout.addLayout(self.content_layout)

        self.setLayout(main_layout)