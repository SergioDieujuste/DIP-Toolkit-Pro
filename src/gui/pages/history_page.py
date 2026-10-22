from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QMessageBox,
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices

from src.diagnostics import history
from src.diagnostics import report_analysis as ra

STATUS_COLORS = {
    ra.OK: "#2ecc71",
    ra.WARNING: "#f39c12",
    ra.DANGER: "#e74c3c",
    ra.UNKNOWN: "#a0a5b5",
}

COLUMNS = ["Date", "Client", "Poste", "Verdict", "Technicien", "PDF"]

BUTTON_STYLE = """
    QPushButton {
        background-color: #141721;
        color: #00adb5;
        border: 1px solid #00adb5;
        padding: 7px 14px;
        border-radius: 5px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #00adb5; color: #ffffff; }
    QPushButton:disabled { color: #5c6370; border: 1px solid #3b4252; background-color: #141721; }
"""


def format_date(iso_text: str) -> str:
    try:
        return datetime.fromisoformat(iso_text).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return iso_text or ""


class HistoryPage(QWidget):
    """Liste des rapports déjà générés : recherche, ouverture du PDF, retrait."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("history_page")

        self.all_entries = []
        self.visible = []   # entrées affichées, dans l'ordre des lignes du tableau
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.reload()   # la liste est à jour à chaque fois qu'on ouvre la page

    # ------------------------------------------------------------------
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        title = QLabel("Historique des rapports")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #ffffff;")
        subtitle = QLabel("Retrouvez les rapports remis à vos clients")
        subtitle.setStyleSheet("font-size: 12px; color: #a0a5b5;")
        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # ---------------- Recherche ----------------
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher un client, un poste, un technicien, un numéro de série...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #141721;
                color: #ffffff;
                border: 1px solid #2e3440;
                padding: 8px 12px;
                border-radius: 5px;
            }
            QLineEdit:focus { border: 1px solid #00adb5; }
        """)
        self.search_input.textChanged.connect(self._apply_filter)
        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: #a0a5b5; font-size: 12px;")
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.count_label)
        main_layout.addLayout(search_row)

        # ---------------- Tableau ----------------
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setShowGrid(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e222d;
                color: #ffffff;
                border: 1px solid #2e3440;
                border-radius: 8px;
                gridline-color: #2e3440;
            }
            QTableWidget::item { padding: 6px; border-bottom: 1px solid #2e3440; }
            QTableWidget::item:selected { background-color: #00adb5; color: #ffffff; }
            QHeaderView::section {
                background-color: #141721;
                color: #a0a5b5;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.table.itemSelectionChanged.connect(self._update_buttons)
        self.table.itemDoubleClicked.connect(lambda _item: self._open_pdf())
        main_layout.addWidget(self.table, 1)

        self.empty_label = QLabel("")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #a0a5b5; font-size: 13px;")
        main_layout.addWidget(self.empty_label)

        # ---------------- Actions ----------------
        actions = QHBoxLayout()
        self.open_btn = QPushButton("Ouvrir le PDF")
        self.folder_btn = QPushButton("Ouvrir le dossier")
        self.remove_btn = QPushButton("Retirer de l'historique...")
        for btn in (self.open_btn, self.folder_btn, self.remove_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(BUTTON_STYLE)
            actions.addWidget(btn)
        actions.addStretch()
        self.open_btn.clicked.connect(self._open_pdf)
        self.folder_btn.clicked.connect(self._open_folder)
        self.remove_btn.clicked.connect(self._remove)
        main_layout.addLayout(actions)

        self.setStyleSheet("QWidget#history_page { background-color: #0f111a; }")
        self._update_buttons()

    # ------------------------------------------------------------------
    def reload(self):
        self.all_entries = history.load_history()
        self._apply_filter()

    def _apply_filter(self):
        self.visible = history.search(self.all_entries, self.search_input.text())
        self._fill_table()

    def _fill_table(self):
        self.table.setRowCount(len(self.visible))

        for row, entry in enumerate(self.visible):
            pdf = history.resolve_file(entry)
            status = entry.get("overall", ra.UNKNOWN)

            cells = [
                format_date(entry.get("date", "")),
                entry.get("client_name", ""),
                entry.get("hostname", ""),
                ra.STATUS_LABELS.get(status, status),
                entry.get("tech_name", ""),
                "Présent" if pdf else "Introuvable",
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col == 3:
                    item.setForeground(QColor(STATUS_COLORS.get(status, "#a0a5b5")))
                elif col == 5 and not pdf:
                    item.setForeground(QColor("#e74c3c"))
                    item.setToolTip("Le fichier a été déplacé ou supprimé.")
                if col == 2 and entry.get("model"):
                    item.setToolTip(entry["model"])
                self.table.setItem(row, col, item)

        total = len(self.all_entries)
        if total == 0:
            self.empty_label.setText("Aucun rapport pour l'instant. Ils apparaîtront ici dès le premier PDF généré.")
        elif not self.visible:
            self.empty_label.setText("Aucun rapport ne correspond à la recherche.")
        else:
            self.empty_label.setText("")
        self.empty_label.setVisible(bool(self.empty_label.text()))

        clients = len({e.get("client_name", "").lower() for e in self.all_entries})
        self.count_label.setText(f"{total} rapport(s) - {clients} client(s)")
        self._update_buttons()

    # ------------------------------------------------------------------
    def _selected_entry(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.visible):
            return self.visible[row]
        return None

    def _update_buttons(self):
        entry = self._selected_entry()
        has_file = entry is not None and history.resolve_file(entry) is not None
        self.open_btn.setEnabled(has_file)
        self.folder_btn.setEnabled(has_file)
        self.remove_btn.setEnabled(entry is not None)

    def _open_pdf(self):
        entry = self._selected_entry()
        pdf = history.resolve_file(entry) if entry else None
        if pdf:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf)))

    def _open_folder(self):
        entry = self._selected_entry()
        pdf = history.resolve_file(entry) if entry else None
        if pdf:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(pdf.parent)))

    def _remove(self):
        entry = self._selected_entry()
        if entry is None:
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Retirer de l'historique")
        box.setText(f"Retirer le rapport de {entry.get('client_name', '')} "
                    f"du {format_date(entry.get('date', ''))} ?")
        box.setInformativeText("Vous pouvez aussi supprimer le fichier PDF de l'ordinateur.")
        keep_btn = box.addButton("Retirer de la liste seulement", QMessageBox.ButtonRole.AcceptRole)
        delete_btn = box.addButton("Retirer et supprimer le PDF", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Annuler", QMessageBox.ButtonRole.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is keep_btn:
            history.delete_entry(entry["id"], delete_file=False)
        elif clicked is delete_btn:
            history.delete_entry(entry["id"], delete_file=True)
        else:
            return
        self.reload()
