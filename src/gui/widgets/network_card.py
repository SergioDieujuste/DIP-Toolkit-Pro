from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
)


class NetworkCard(QFrame):

    def __init__(self, infos):
        super().__init__()

        self.setObjectName("InfoCard")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("🌐 Informations réseau")
        title.setObjectName("InfoCardTitle")

        layout.addWidget(title)

        champs = [

            ("Nom du PC", infos["hostname"]),
            ("Adresse IPv4", infos["ip"]),
            ("Carte réseau", infos["interface"]),
            ("Adresse MAC", infos["mac"]),

        ]

        for nom, valeur in champs:

            label = QLabel(f"<b>{nom}</b> : {valeur}")
            label.setObjectName("InfoLabel")

            layout.addWidget(label)

        layout.addStretch()

        self.setLayout(layout)