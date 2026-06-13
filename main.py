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
    
    # Try to set an app icon if available
    # app.setWindowIcon(QIcon("icon.png"))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
