from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame,
)

from src.diagnostics.system_diagnostics import SystemDiagnostics


class DiagnosticPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("DiagnosticPage")

        # ==================================================
        # Layout principal
        # ==================================================

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)

        # ==================================================
        # Titre
        # ==================================================

        self.title = QLabel("Diagnostic système")
        self.title.setObjectName("PageTitle")

        self.subtitle = QLabel(
            "Informations détaillées sur la configuration et l'état de votre ordinateur."
        )
        self.subtitle.setObjectName("PageSubtitle")
        self.subtitle.setWordWrap(True)

        main_layout.addWidget(self.title)
        main_layout.addWidget(self.subtitle)

        # ==================================================
        # Carte contenant les informations
        # ==================================================

        card = QFrame()
        card.setObjectName("InfoCard")

        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(12)

        diag = SystemDiagnostics()
        infos = diag.get_info()

        self.labels = []

        for cle, valeur in infos.items():

            label = QLabel(f"<b>{cle}</b> : {valeur}")
            label.setObjectName("InfoLabel")
            label.setWordWrap(True)

            self.labels.append(label)

            card_layout.addWidget(label)

        card.setLayout(card_layout)

        main_layout.addWidget(card)
        main_layout.addStretch()

        self.setLayout(main_layout)