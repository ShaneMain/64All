import html
import os
import re
import sys

from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QColor, QPalette, QTextCursor, QFont, QTextOption, QPixmap
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
    QVBoxLayout,
    QApplication,
    QSplitter,
    QFrame,
    QSpinBox,
)

from ui.build_option_utils import add_options_to_layout
from ui.git_utils import CloningManager
from ui.signal_connections import BASE_PATH


class GitProgress(QObject):
    update_progress = pyqtSignal(str)


class UISetup:
    def __init__(self, parent):
        self.parent = parent
        self.current_repo = None
        self.repo_url_combobox = QComboBox(parent)
        self.repo_url_combobox.currentIndexChanged.connect(self.on_repo_selection)
        self.repo_url_label = QLabel("Repository:")
        self.install_dir_entry = QLineEdit(parent)
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
        self.branch_combobox = QComboBox()
        self.branch_label = QLabel("Branch:")

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

        self.repo_image = QLabel(parent)
        self.repo_trailer = QLabel(parent)
        self.repo_description = QTextEdit(parent)
        self.repo_description.setReadOnly(True)

        self.repo_url_combobox.currentIndexChanged.connect(self.on_repo_selection)

        self.current_repo = None

    def update_color_map(self):
        app = QApplication.instance()
        is_dark_theme = app.palette().color(QPalette.ColorRole.Window).lightness() < 128
        self.color_map = self.dark_color_map if is_dark_theme else self.light_color_map

    def setup(self):
        # Create a main horizontal layout
        main_layout = QHBoxLayout()

        # Create a splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left section (Fork info)
        left_widget = QWidget()
        left_widget.setFixedWidth(300)  # Set a fixed width for the fork info section
        left_layout = QVBoxLayout(left_widget)

        # Create a frame to contain the image
        self.image_frame = QFrame()
        self.image_frame.setFixedWidth(
            left_widget.width() - 20
        )  # Adjust for layout margins
        self.image_frame.setFixedHeight(
            int(self.image_frame.width() * 9 / 16)
        )  # 16:9 aspect ratio
        image_layout = QVBoxLayout(self.image_frame)
        image_layout.setContentsMargins(0, 0, 0, 0)

        self.repo_image.setScaledContents(False)  # Changed to False
        self.repo_image.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the image
        image_layout.addWidget(self.repo_image)

        left_layout.addWidget(self.image_frame)
        left_layout.addWidget(self.repo_trailer)
        left_layout.addWidget(self.repo_description)
        left_layout.addStretch(1)
        splitter.addWidget(left_widget)

        # Right section (Existing content)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.setup_existing_content(right_layout)
        splitter.addWidget(right_widget)

        # Set initial sizes for splitter
        splitter.setSizes([left_widget.width(), 1100])  # Adjust these values as needed

        # Add splitter to main layout
        main_layout.addWidget(splitter)

        # Set the main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.parent.setCentralWidget(main_widget)

        # Call this to set initial state
        self.advanced_checkbox.stateChanged.connect(self.update_advanced_options)
        self.update_advanced_options()

    def resizeEvent(self, event):
        # Update image frame size when the window is resized
        left_widget_width = (
            self.parent.width() * 0.21
        )  # Approximately 21% of window width
        self.image_frame.setFixedWidth(
            left_widget_width - 20
        )  # Adjust for layout margins
        self.image_frame.setFixedHeight(
            int(self.image_frame.width() * 9 / 16)
        )  # 16:9 aspect ratio
        super().resizeEvent(event)

    def setup_existing_content(self, layout):
        grid_layout = QGridLayout()

        # Repository section
        grid_layout.addWidget(self.repo_url_label, 0, 0)
        repo_layout = QHBoxLayout()
        repo_layout.addWidget(self.repo_url_combobox)
        grid_layout.addLayout(repo_layout, 0, 1)

        # Clone directory section
        grid_layout.addWidget(QLabel("Install Directory:"), 1, 0)
        clone_dir_layout = QHBoxLayout()
        clone_dir_layout.addWidget(self.install_dir_entry)
        clone_dir_layout.addWidget(self.browse_button)
        grid_layout.addLayout(clone_dir_layout, 1, 1)

        # Branch section
        grid_layout.addWidget(self.branch_label, 2, 0)
        grid_layout.addWidget(self.branch_menu, 2, 1)

        # Advanced options
        grid_layout.addWidget(self.advanced_checkbox, 3, 0, 1, 2)
        grid_layout.addWidget(self.options_widget, 4, 0, 1, 2)

        # Clone button
        grid_layout.addWidget(self.clone_button, 5, 0, 1, 2)

        # Progress bar
        grid_layout.addWidget(self.progress_bar, 6, 0, 1, 2)

        # Output text
        grid_layout.addWidget(self.output_text, 7, 0, 1, 2)

        layout.addLayout(grid_layout)

    def connect_signals(self):
        self.advanced_checkbox.stateChanged.connect(self.update_advanced_options)
        self.browse_button.clicked.connect(self.parent.repo_manager.browse_directory)

    def on_repo_selection(self):
        repo_name = self.repo_url_combobox.currentText()
        if not repo_name or repo_name == self.current_repo:
            return

        self.current_repo = repo_name
        repo = next(
            (
                repo
                for repo in self.parent.repo_manager.REPOS
                if repo["name"] == repo_name
            ),
            None,
        )
        if repo:
            self.parent.repo_url = repo.get("url")
            default_dir = os.path.expanduser(f"~/{repo_name}")
            self.install_dir_entry.setText(default_dir)

            self.parent.build_dependencies = repo.get("dependencies", [])

            from core.gitlogic import update_branch_menu

            update_branch_menu(
                repo_name, self.parent.repo_manager.REPOS, self.branch_menu
            )

            # Clear existing options
            self.parent.repo_options = {}
            self.parent.build_manager.user_selections = {}

            # Update with new repo options
            self.parent.repo_options = repo.get("options", {})
            self.parent.build_manager.update_build_options(self.parent.repo_options)

            self.branch_combobox.setCurrentText(repo_name)

            self.update_advanced_options()

            # Update image and other info
            self.update_repo_info(repo)

            print(f"Selected repo: {repo_name}, Options: {self.parent.repo_options}")
        else:
            print(f"Repository {repo_name} not found in loaded repos.")

    def update_repo_info(self, repo):
        info = repo.get("info", {})

        # Debug: Print BASE_PATH
        print(f"BASE_PATH: {BASE_PATH}")

        # Update image
        image_name = info.get("image", "")
        print(f"Image name from repo info: {image_name}")

        image_path = os.path.join(BASE_PATH, "config", "images", image_name)
        print(f"Full image path: {image_path}")
        print(f"Image file exists: {os.path.exists(image_path)}")

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            print(f"Pixmap is null: {pixmap.isNull()}")
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    300,
                    200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                print(f"Scaled pixmap is null: {scaled_pixmap.isNull()}")
                self.repo_image.setPixmap(scaled_pixmap)
            else:
                print(f"Failed to load image: {image_path}")
                self.repo_image.clear()
        else:
            print(f"Image file not found: {image_path}")
            self.repo_image.clear()

        # Update description
        description = info.get("description", "No description available.")
        self.repo_description.setPlainText(description)

        # Update trailer
        trailer_link = info.get("trailer", "")
        if trailer_link:
            self.repo_trailer.setText(f'<a href="{trailer_link}">Watch Trailer</a>')
            self.repo_trailer.setOpenExternalLinks(True)
        else:
            self.repo_trailer.clear()

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
        current_selections = self.parent.build_manager.user_selections.copy()

        # Update branch menu visibility
        self.branch_label.setVisible(visible)
        self.branch_menu.setVisible(visible)

        # Refresh the layout with the new visibility settings
        self.parent.build_manager.update_build_options(self.parent.repo_options)

        # Restore user selections
        for opt_name, value in current_selections.items():
            self.parent.build_manager.update_user_selection(opt_name, value)

        # Update UI to reflect restored selections
        self.refresh_options_layout()

        # Ensure BUILD_TARGET dropdown is always visible
        build_target_widget = self.options_layout.findChild(
            QWidget, "BUILD_TARGET_widget"
        )
        if build_target_widget:
            build_target_widget.setVisible(True)

    def set_clone_button_enabled(self, enabled):
        self.clone_button.setEnabled(enabled)

    def update_output_text(self, text):
        # Replace carriage returns with newlines, but only if it's not followed by a newline
        text = re.sub(r"\r(?!\n)", "\n", text)

        # Split the text into lines
        lines = text.split("\n")

        for line in lines:
            # If the new line starts with the same content as the last line,
            # replace the last line instead of adding a new one
            if self.last_line and line.startswith(self.last_line):
                self.text_buffer = (
                    self.text_buffer[: -len(self.last_line)] + line + "\n"
                )
            else:
                self.text_buffer += line + "\n"

            # Update the last line
            self.last_line = line

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

        # Update UI to reflect current selections
        for opt_name, value in self.parent.build_manager.user_selections.items():
            widget = self.options_layout.findChild(QWidget, f"{opt_name}_widget")
            if widget:
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value))

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
