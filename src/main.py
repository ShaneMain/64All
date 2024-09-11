import sys

from PyQt6.QtWidgets import QApplication

from src.ui.primary_window import Mario64All

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Mario64All()
    window.show()
    sys.exit(app.exec())
