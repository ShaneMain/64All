from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

class ColorManager:
    def __init__(self):
        self.light_color_map = {
            "0": QColor("black"),
            "32": QColor("darkgreen"),
            "31": QColor("darkred"),
            "33": QColor("darkorange"),
            "34": QColor("darkblue"),
            "35": QColor("darkmagenta"),
            "36": QColor("darkcyan"),
            "37": QColor("darkgray"),
        }

        self.dark_color_map = {
            "0": QColor("white"),
            "32": QColor("lightgreen"),
            "31": QColor("lightcoral"),
            "33": QColor("yellow"),
            "34": QColor("lightskyblue"),
            "35": QColor("violet"),
            "36": QColor("cyan"),
            "37": QColor("lightgray"),
        }

        self.update_color_map()

    def update_color_map(self):
        app = QApplication.instance()
        is_dark_theme = app.palette().color(QPalette.ColorRole.Window).lightness() < 128
        self.color_map = self.dark_color_map if is_dark_theme else self.light_color_map