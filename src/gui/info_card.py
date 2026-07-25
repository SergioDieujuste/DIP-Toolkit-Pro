from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)
from PySide6.QtCore import Qt


class InfoCard(QFrame):

    def __init__(self, titre, valeur):
        super().__init__()

        # Le style est maintenant géré dans dip.qss
        self.setObjectName("InfoCard")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title = QLabel(titre)
        self.title.setObjectName("InfoCardTitle")
        self.title.setAlignment(Qt.AlignCenter)

        self.value = QLabel(valeur)
        self.value.setObjectName("InfoCardValue")
        self.value.setAlignment(Qt.AlignCenter)
        self.value.setWordWrap(True)

        layout.addWidget(self.title)
        layout.addWidget(self.value)

        self.setLayout(layout)