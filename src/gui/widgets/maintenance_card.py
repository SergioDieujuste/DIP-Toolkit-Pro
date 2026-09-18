from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QThread, Signal


# Import de la logique backend
try:
    from src.diagnostics.maintenance_info import MaintenanceInfo
except ModuleNotFoundError:
    from diagnostics.maintenance_info import MaintenanceInfo


class MaintenanceWorker(QThread):
    """Thread secondaire pour exécuter une tâche de maintenance sans figer l'IHM."""
    finished = Signal(bool, str)

    def __init__(self, task_id: str):
        super().__init__()
        self.task_id = task_id

    def run(self):
        success, message = MaintenanceInfo.run_task(self.task_id)
        self.finished.emit(success, message)


class MaintenanceCard(QFrame):
    """Widget de carte pour une tâche de maintenance spécifique."""

    def __init__(self, task_data: dict, parent=None):
        super().__init__(parent)
        self.task_data = task_data
        self.task_id = task_data.get("id", "")
        self.setObjectName("maintenance_card")

        self.worker = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        # ----------------------------------------------------
        # 1. En-tête : Titre + Bouton d'action
        # ----------------------------------------------------
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        # Titre de la tâche
        title_label = QLabel(self.task_data.get("title", "Tâche de maintenance"))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        # Bouton d'exécution
        self.action_btn = QPushButton(self.task_data.get("action_name", "Exécuter"))
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.setStyleSheet("""
            QPushButton {
                background-color: #00adb5;
                color: #ffffff;
                border: none;
                padding: 6px 14px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #00888f;
            }
            QPushButton:disabled {
                background-color: #3b4252;
                color: #a0a5b5;
            }
        """)
        self.action_btn.clicked.connect(self._run_maintenance)
        top_layout.addWidget(self.action_btn)

        layout.addLayout(top_layout)

        # ----------------------------------------------------
        # 2. Description
        # ----------------------------------------------------
        desc_label = QLabel(self.task_data.get("description", ""))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #a0a5b5; font-size: 12px;")
        layout.addWidget(desc_label)

        # ----------------------------------------------------
        # 3. Label de résultat (mis à jour après exécution)
        # ----------------------------------------------------
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setVisible(False)
        layout.addWidget(self.result_label)

        # Style de la carte
        self.setStyleSheet("""
            QFrame#maintenance_card {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#maintenance_card:hover {
                border: 1px solid #00adb5;
            }
        """)

    def _run_maintenance(self):
        """Lance l'exécution de la tâche en arrière-plan."""
        self.action_btn.setEnabled(False)
        self.action_btn.setText("En cours...")
        self.result_label.setVisible(False)

        self.worker = MaintenanceWorker(self.task_id)
        self.worker.finished.connect(self._on_task_finished)
        self.worker.start()

    def _on_task_finished(self, success: bool, message: str):
        """Met à jour l'IHM après l'exécution de la tâche."""
        self.action_btn.setEnabled(True)
        self.action_btn.setText(self.task_data.get("action_name", "Exécuter"))

        color = "#2ecc71" if success else "#e74c3c"
        self.result_label.setText(message)
        self.result_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; margin-top: 4px;")
        self.result_label.setVisible(True)