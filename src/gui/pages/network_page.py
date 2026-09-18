import subprocess
import socket
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QFileDialog,
)

from .base_page import BasePage
from src.diagnostics.network_info import get_network_info
from src.gui.widgets.network_card import NetworkCard


# Thread pour scanner le réseau sans bloquer l'UI
class NetworkScannerThread(QThread):
    scan_complete = Signal(list)

    def __init__(self, base_ip):
        super().__init__()
        self.base_ip = base_ip  # Ex: "192.168.1"

    def run(self):
        active_hosts = []
        # Scan rapide des premières adresses IP de la plage locale
        for i in range(1, 255):
            ip = f"{self.base_ip}.{i}"
            # Commande ping (1 seul paquet, 200ms de timeout)
            res = subprocess.run(
                ["ping", "-n", "1", "-w", "200", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if res.returncode == 0:
                active_hosts.append(ip)
        self.scan_complete.emit(active_hosts)


class NetworkPage(BasePage):

    def __init__(self):
        super().__init__(
            "🌐 Réseau",
            "Informations sur la connexion réseau et les interfaces de l'ordinateur."
        )

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

        # Carte des informations
        self.card_container = QVBoxLayout()
        self.load_network_card()
        scroll_layout.addLayout(self.card_container)

        # Barre de boutons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)

        btn_style = """
            QPushButton {
                background-color: #1e222d;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 8px 14px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00adb5;
                border-color: #00adb5;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #141721;
                color: #555555;
            }
        """

        self.refresh_button = QPushButton("🔄 Actualiser")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.setStyleSheet(btn_style)
        self.refresh_button.clicked.connect(self.load_network_card)

        self.internet_button = QPushButton("🌐 Tester Internet")
        self.internet_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.internet_button.setStyleSheet(btn_style)
        self.internet_button.clicked.connect(self.test_internet)

        self.scan_button = QPushButton("📡 Scanner le réseau")
        self.scan_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.scan_button.setStyleSheet(btn_style)
        self.scan_button.clicked.connect(self.scan_network)

        self.export_button = QPushButton("📄 Exporter")
        self.export_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_button.setStyleSheet(btn_style)
        self.export_button.clicked.connect(self.export_info)

        actions_layout.addWidget(self.refresh_button)
        actions_layout.addWidget(self.internet_button)
        actions_layout.addWidget(self.scan_button)
        actions_layout.addWidget(self.export_button)
        actions_layout.addStretch()

        scroll_layout.addLayout(actions_layout)
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        self.content_layout.addWidget(scroll_area)

    def load_network_card(self):
        """Recharge ou initialise la carte d'information réseau."""
        # Vide le layout si la carte existe déjà
        while self.card_container.count():
            item = self.card_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.infos = get_network_info()
        self.card = NetworkCard(self.infos)
        self.card_container.addWidget(self.card)

    def test_internet(self):
        """Teste la connexion internet avec un ping rapide."""
        try:
            # Tente d'ouvrir une connexion vers le DNS public Google (8.8.8.8)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            QMessageBox.information(
                self, 
                "Test Internet", 
                "✅ Connexion Internet fonctionnelle !\n(Ping vers 8.8.8.8 réussi)"
            )
        except OSError:
            QMessageBox.critical(
                self, 
                "Test Internet", 
                "❌ Pas de connexion Internet détectée."
            )

    def scan_network(self):
        """Lance un balayage IP rapide en tâche de fond."""
        ip = self.infos.get("ip", "")
        if not ip or ip == "Inconnue" or ip.startswith("127."):
            QMessageBox.warning(self, "Scanner Réseau", "Impossible de déterminer l'adresse IP locale.")
            return

        base_ip = ".".join(ip.split(".")[:3])
        self.scan_button.setEnabled(False)
        self.scan_button.setText("📡 Scan en cours...")

        self.scanner_thread = NetworkScannerThread(base_ip)
        self.scanner_thread.scan_complete.connect(self.on_scan_finished)
        self.scanner_thread.start()

    def on_scan_finished(self, hosts):
        self.scan_button.setEnabled(True)
        self.scan_button.setText("📡 Scanner le réseau")
        
        count = len(hosts)
        hosts_str = "\n".join(hosts[:15])  # Affiche jusqu'à 15 IPs
        if count > 15:
            hosts_str += f"\n... et {count - 15} autres."

        QMessageBox.information(
            self,
            "Résultat du scan",
            f"✅ {count} équipement(s) détecté(s) sur le réseau :\n\n{hosts_str}"
        )

    def export_info(self):
        """Exporte les données réseau dans un fichier texte."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder l'état réseau", "diagnostic_reseau.txt", "Fichiers Texte (*.txt)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("=== INFORMATIONS RÉSEAU ===\n")
                for k, v in self.infos.items():
                    f.write(f"{k} : {v}\n")
            QMessageBox.information(self, "Exportation", "✅ Fichier exporté avec succès !")