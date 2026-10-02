import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from src.utils.paths import APP_NAME, resource_path


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    icon_file = resource_path("assets/logo/app.ico")
    if icon_file.exists():
        app.setWindowIcon(QIcon(str(icon_file)))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
