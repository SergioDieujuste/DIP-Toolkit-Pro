from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QScrollArea,
)

from src.diagnostics.system_diagnostics import SystemDiagnostics


class DiagnosticPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setObjectName("DiagnosticPage")

        # ==================================================
        # Layout principal
        # ==================================================

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ==================================================
        # En-tête (Titre & Sous-titre)
        # ==================================================

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        self.title = QLabel("Diagnostic système")
        self.title.setObjectName("PageTitle")
        self.title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")

        self.subtitle = QLabel(
            "Informations détaillées sur la configuration et l'état de votre ordinateur."
        )
        self.subtitle.setObjectName("PageSubtitle")
        self.subtitle.setStyleSheet("font-size: 12px; color: #a0a5b5;")
        self.subtitle.setWordWrap(True)

        title_layout.addWidget(self.title)
        title_layout.addWidget(self.subtitle)

        main_layout.addLayout(title_layout)

        # ==================================================
        # Zone défilante (QScrollArea)
        # ==================================================

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(15)

        # ==================================================
        # Carte contenant les informations
        # ==================================================

        card = QFrame()
        card.setObjectName("DiagnosticCard")
        card.setStyleSheet("""
            QFrame#DiagnosticCard {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#DiagnosticCard:hover {
                border: 1px solid #00adb5;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(12)

        diag = SystemDiagnostics()
        infos = diag.get_info()

        self.labels = []

        for cle, valeur in infos.items():
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)

            key_label = QLabel(f"{cle} :")
            key_label.setStyleSheet("color: #00adb5; font-size: 13px; font-weight: bold;")

            val_label = QLabel(str(valeur))
            val_label.setStyleSheet("color: #ffffff; font-size: 13px;")
            val_label.setWordWrap(True)

            row_layout.addWidget(key_label)
            row_layout.addWidget(val_label, stretch=1)

            card_layout.addLayout(row_layout)
            self.labels.append((key_label, val_label))

        scroll_layout.addWidget(card)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.setStyleSheet("""
                    QWidget#DashboardPage, QScrollArea, QScrollArea > QWidget > QWidget {
                        background-color: #0f111a;
                    }
                """)