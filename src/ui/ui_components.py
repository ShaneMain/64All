import html
import re

from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QTextCursor, QFont, QTextOption
from PyQt6.QtWidgets import (
    QLabel,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QProgressBar,
    QCheckBox,
    QPushButton,
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QSizePolicy,
    QApplication,
)

from src.ui.uiutils import add_horizontal_widgets
from ui.build_option_utils import add_options_to_layout
from ui.git_utils import CloningManager


class GitProgress(QObject):
    update_progress = pyqtSignal(str)


class UISetup:
    def __init__(self, parent):
        self.parent = parent
        self.repo_url_combobox = QComboBox()
        self.repo_url_label = QLabel("Repository:")
        self.clone_dir_entry = QLineEdit(parent)
        self.branch_menu = QComboBox(parent)
        self.output_text = QTextEdit(parent)
        self.output_text.setReadOnly(True)
        self.output_text.setAcceptRichText(True)
        self.output_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.output_text.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)

        # Set monospace font
        font = QFont("Courier")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(9)  # Adjust this value as needed
        self.output_text.setFont(font)

        # Set custom stylesheet to control spacing and wrapping
        self.output_text.setStyleSheet(
            """
            QTextEdit {
                padding: 0px;
            }
            .line {
                margin: 0;
                padding: 0;
                line-height: 1.2;
                font-family: Courier, monospace;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
        """
        )

        self.progress_bar = QProgressBar(parent)
        self.advanced_checkbox = QCheckBox("Show advanced options")
        self.browse_button = QPushButton("Browse...", parent)
        self.clone_button = QPushButton("Clone", parent)
        self.options_widget = QWidget()
        self.options_layout = QGridLayout(self.options_widget)
        self.fork_combobox = QComboBox()
        self.fork_label = QLabel("Fork:")

        # Initialize color maps
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

        # Compile regex pattern
        self.color_pattern = re.compile(r"\[(\d+)m")

        # Set initial color map based on theme
        self.update_color_map()

        self.text_buffer = ""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.flush_text_buffer)
        self.update_timer.start(100)  # Update every 100ms

        self.cloning_manager = CloningManager()
        self.cloning_manager.progress_signal.connect(self.update_progress_bar)
        self.cloning_manager.text_signal.connect(self.update_output_text)
        self.cloning_manager.finished_signal.connect(self.cloning_finished)

        self.last_line = ""

    def update_color_map(self):
        app = QApplication.instance()
        is_dark_theme = app.palette().color(QPalette.ColorRole.Window).lightness() < 128
        self.color_map = self.dark_color_map if is_dark_theme else self.light_color_map

    def setup(self):
        self.parent.output_text = self.output_text
        self.output_text.setFixedHeight(100)

        self.setup_fork_section()
        self.setup_directory_section()
        self.setup_branch_section()

        self.parent.main_layout.addWidget(self.progress_bar)
        self.parent.main_layout.addWidget(self.output_text)

        self.setup_advanced_options()

    def setup_fork_section(self):
        self.parent.fork_collection = add_horizontal_widgets(
            self.parent.main_layout,
            (QLabel("Fork:"), (QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)),
            (
                self.fork_combobox,
                (QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed),
            ),
            (self.clone_button, (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)),
        )

    def setup_directory_section(self):
        self.parent.directory_collection = add_horizontal_widgets(
            self.parent.main_layout,
            (
                QLabel("Base Directory:"),
                (QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed),
            ),
            (
                self.clone_dir_entry,
                (QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed),
            ),
            (
                self.browse_button,
                (QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed),
            ),
        )

    def setup_branch_section(self):
        self.parent.branch_collection = add_horizontal_widgets(
            self.parent.main_layout,
            (
                QLabel("Branch:"),
                (QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed),
            ),
            (self.branch_menu, (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)),
        )

    def setup_advanced_options(self):
        advanced_options_layout = QHBoxLayout()
        advanced_options_layout.addWidget(
            QLabel("Options:", self.parent), alignment=Qt.AlignmentFlag.AlignLeft
        )
        advanced_options_layout.addWidget(
            self.advanced_checkbox, alignment=Qt.AlignmentFlag.AlignRight
        )

        self.parent.main_layout.addLayout(advanced_options_layout)
        self.parent.main_layout.addWidget(
            self.options_widget, alignment=Qt.AlignmentFlag.AlignTop
        )

    def connect_signals(self):
        self.advanced_checkbox.stateChanged.connect(self.update_advanced_options)
        self.browse_button.clicked.connect(self.parent.repo_manager.browse_directory)

    def update_build_options(self, repo_options):
        for i in reversed(range(self.parent.ui_setup.options_layout.count())):
            widget = self.parent.ui_setup.options_layout.itemAt(i).widget()
            if widget:
                self.parent.ui_setup.options_layout.removeWidget(widget)
                widget.setParent(None)

        add_options_to_layout(self.parent, repo_options)

        # Set initial values for options
        for opt_name, opt_info in repo_options.items():
            recommended_value = opt_info.get("recommended")
            default_value = opt_info.get("default")
            if recommended_value is not None:
                self.update_user_selection(opt_name, recommended_value)
            elif default_value is not None:
                self.update_user_selection(opt_name, default_value)

    def update_advanced_options(self):
        visible = self.advanced_checkbox.isChecked()

        for i in range(self.options_layout.count()):
            item = self.options_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                # Check if this is an advanced option
                opt_name = widget.property("opt_name")
                if opt_name:
                    opt_info = self.parent.repo_options.get(opt_name, {})
                    is_advanced = opt_info.get("advanced", False)
                    widget.setVisible(not is_advanced or visible)

        # Refresh the layout
        self.parent.build_manager.update_build_options(self.parent.repo_options)

    def update_output_text(self, text):
        # Replace carriage returns with newlines, but only if it's not followed by a newline
        text = re.sub(r"\r(?!\n)", "\n", text)

        # If the new text starts with the same content as the last line,
        # replace the last line instead of adding a new one
        if self.last_line and text.startswith(self.last_line):
            self.text_buffer = self.text_buffer[: -len(self.last_line)] + text
        else:
            self.text_buffer += text

        # Update the last line
        self.last_line = text.split("\n")[-1]

        # If the buffer is getting too large, force an update
        if len(self.text_buffer) > 4096:
            self.flush_text_buffer()

    def flush_text_buffer(self):
        if not self.text_buffer:
            return

        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Split the text by color codes, preserving newlines
        parts = self.color_pattern.split(self.text_buffer)

        html_text = ""
        current_color = self.color_map["0"]  # Start with default color

        for i, part in enumerate(parts):
            if i % 2 == 1:  # This is a color code
                current_color = self.color_map.get(part, self.color_map["0"])
            else:  # This is text content
                # Escape special HTML characters and replace newlines with <br>
                escaped_part = html.escape(part).replace("\n", "<br>")
                html_text += (
                    f'<span style="color:{current_color.name()};">{escaped_part}</span>'
                )

        cursor.insertHtml(html_text)
        self.output_text.setTextCursor(cursor)
        self.output_text.ensureCursorVisible()
        self.text_buffer = ""

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def refresh_options_layout(self):
        # Clear the existing layout
        for i in reversed(range(self.options_layout.count())):
            widget = self.options_layout.itemAt(i).widget()
            if widget:
                self.options_layout.removeWidget(widget)
                widget.setParent(None)

        # Rebuild the layout
        self.parent.build_manager.update_build_options(self.parent.repo_options)

    def cloning_finished(self, success):
        if success:
            self.ui_setup.update_output_text("[32mCloning finished successfully![0m\n")
            self.ui_setup.update_output_text("[32mStarting build process...[0m\n")
            QTimer.singleShot(0, self.build_manager.start_building)
        else:
            self.ui_setup.update_output_text(
                "[31mCloning failed. Check the output for errors.[0m\n"
            )
            self.ui_setup.update_output_text(
                "[33mYou may need to try cloning again.[0m\n"
            )

    def cleanup(self):
        self.update_timer.stop()

    def start_cloning(self, repo_url, clone_dir, branch):
        self.cloning_manager.start_cloning(repo_url, clone_dir, branch)
