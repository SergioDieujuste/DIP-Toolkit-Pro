from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar
)
from PySide6.QtCore import Qt


class DiskCard(QFrame):

    def __init__(self, disk_info):
        super().__init__()

        self.setObjectName("DiskCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # ----------------------------------------------------
        # 1. EN-TÊTE DE LA CARTE (LECTEUR + SYSTÈME DE FICHIERS)
        # ----------------------------------------------------
        header_layout = QHBoxLayout()
        
        device_name = disk_info.get("device", "Disque")
        mountpoint = disk_info.get("mountpoint", "")
        title_text = f"💾 {device_name} ({mountpoint})" if mountpoint else f"💾 {device_name}"

        title = QLabel(title_text)
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #00adb5;")

        fstype = QLabel(disk_info.get("fstype", "").upper())
        fstype.setStyleSheet("""
            color: #a0a5b5; 
            background-color: #141721; 
            padding: 2px 6px; 
            border-radius: 4px; 
            font-size: 10px; 
            font-weight: bold;
        """)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(fstype)

        layout.addLayout(header_layout)

        # ----------------------------------------------------
        # 2. BARRE DE PROGRESSION
        # ----------------------------------------------------
        percent = int(disk_info.get("percent", 0))

        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(percent)
        progress.setTextVisible(False)
        progress.setFixedHeight(8)
        
        # Changement de couleur si le disque est presque plein (>85%)
        bar_color = "#e74c3c" if percent > 85 else "#00adb5"
        
        progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: #141721;
                border: 1px solid #2e3440;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {bar_color};
                border-radius: 3px;
            }}
        """)

        layout.addWidget(progress)

        # ----------------------------------------------------
        # 3. DÉTAILS D'ESPACE (UTILISÉ / LIBRE / TOTAL)
        # ----------------------------------------------------
        details_layout = QHBoxLayout()
        
        used_str = disk_info.get("used", "0 GB")
        total_str = disk_info.get("total", "0 GB")
        free_str = disk_info.get("free", "0 GB")

        info_label = QLabel(f"Utilisé : <b>{used_str}</b> / {total_str} ({percent}%)")
        info_label.setStyleSheet("color: #ffffff; font-size: 11px;")

        free_label = QLabel(f"Libre : <b>{free_str}</b>")
        free_label.setStyleSheet("color: #a0a5b5; font-size: 11px;")

        details_layout.addWidget(info_label)
        details_layout.addStretch()
        details_layout.addWidget(free_label)

        layout.addLayout(details_layout)

        # ----------------------------------------------------
        # 4. STYLE DE LA CARTE (SOMBRE & TURQUOISE)
        # ----------------------------------------------------
        self.setStyleSheet("""
            QFrame#DiskCard {
                background-color: #1e222d;
                border: 1px solid #2e3440;
                border-radius: 8px;
            }
            QFrame#DiskCard:hover {
                border: 1px solid #00adb5;
            }
        """)