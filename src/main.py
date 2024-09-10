import sys

from PyQt6.QtWidgets import QApplication

from src.Qt.primary_window import Mario64All
from src.logic.check_dependencies import check_and_install

if __name__ == "__main__":
    check_and_install()
    app = QApplication(sys.argv)
    window = Mario64All()
    window.show()
    sys.exit(app.exec())
