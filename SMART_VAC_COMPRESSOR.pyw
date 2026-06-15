import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from gui.main_window import MainWindow

def main():
    # Setup application
    app = QApplication(sys.argv)
    app.setApplicationName("SMART VAC MEDIA COMPRESSOR")
    app.setOrganizationName("VAC")
    app.setQuitOnLastWindowClosed(False)
    
    # Try to set an app icon if available
    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.svg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
