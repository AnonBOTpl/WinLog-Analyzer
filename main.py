import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from ui.main_window import MainWindow
from core.paths import resource_path
from core.i18n import load as i18n_load
from ui.settings_dialog import load_settings


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("WinLog Analyzer")
    app.setOrganizationName("WinLog")
    app.setWindowIcon(QIcon(str(resource_path("ikona.png"))))

    settings = load_settings()
    i18n_load(settings.get("language", "en"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
