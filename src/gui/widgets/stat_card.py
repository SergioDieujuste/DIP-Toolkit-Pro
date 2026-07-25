from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QProgressBar
)
from PySide6.QtCore import Qt


class StatCard(QFrame):

    def __init__(self, titre):
        super().__init__()

        self.setObjectName("StatCard")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.title = QLabel(titre)
        self.title.setObjectName("CardTitle")
        self.title.setAlignment(Qt.AlignCenter)

        self.value = QLabel("0 %")
        self.value.setObjectName("CardValue")
        self.value.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setObjectName("CardProgress")
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)

        self.status = QLabel("Normal")
        self.status.setObjectName("CardStatus")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setProperty("state", "normal")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)

        self.setLayout(layout)

    def set_value(self, valeur):

        self.progress.setValue(valeur)
        self.value.setText(f"{valeur} %")

        if valeur < 50:
            state = "normal"
            text = "Normal"

        elif valeur < 80:
            state = "warning"
            text = "Élevé"

        else:
            state = "danger"
            text = "Critique"

        self.status.setText(text)
        self.status.setProperty("state", state)

        # Recharge uniquement le style du label
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.status.update()