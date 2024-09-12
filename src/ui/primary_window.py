import os
import sys

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QProgressBar,
    QTextEdit,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QLabel,
    QComboBox,
    QCheckBox,
)

from core.buildlogic import copy_file_to_dir, run_make
from core.gitlogic import CloneWorker
from src.core.romfinder import N64RomValidator
from src.ui.build_option_utils import (
    add_options_to_layout,
    dump_user_selections,
)
from src.ui.git_utils import load_repos, on_repo_selection, start_cloning


class Mario64All(QMainWindow):
    def __init__(self):
        super().__init__()
        self.workspace = os.path.abspath("./.workspace")

        self.branch_collection = None
        self.directory_collection = None
        self.fork_collection = None
        self.repo_url = None
        self.setWindowTitle("Mario Sixty For All")
        self.setFixedSize(700, 600)

        self.main_widget = QWidget()
        self.main_layout = QVBoxLayout(self.main_widget)  # Use QVBoxLayout
        self.main_layout.setSpacing(5)  # Set the spacing between elements
        self.main_layout.setContentsMargins(
            10, 10, 10, 10
        )  # Set margins around the layout
        self.setCentralWidget(self.main_widget)

        self.repo_url_combobox = QComboBox(self)
        self.clone_dir_entry = QLineEdit(self)
        self.branch_menu = QComboBox(self)
        self.output_text = QTextEdit(self)
        self.progress_bar = QProgressBar(self)
        self.advanced_checkbox = QCheckBox("Show advanced options")

        self.REPOS = []
        self.repo_options = {}
        self.user_selections = {}
        self.clone_worker = CloneWorker()
        self.worker_thread = QThread()

        self.browse_button = QPushButton("Browse...", self)
        self.clone_button = QPushButton("Clone", self)

        self.options_widget = QWidget()
        self.options_layout = QGridLayout(self.options_widget)
        self.options_layout.setSpacing(
            5
        )  # Set the spacing between elements in options layout
        self.options_widget.setLayout(self.options_layout)
        self.setup_ui()
        self.update_advanced_options()
        self.rom_region, self.rom_dir = N64RomValidator().find_or_select_file()

    def populate_repo_urls(self):
        self.repo_url_combobox.clear()
        for repo in self.REPOS:
            self.repo_url_combobox.addItem(repo["name"])

    def setup_ui(self):
        load_repos(self)
        self.connect_signals()

        self.output_text.setFixedHeight(200)

        # Fork Label and ComboBox
        self.fork_collection = self.add_horizontal_widgets(
            (
                QLabel("Fork:"),
                (QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed),
            ),
            (
                self.repo_url_combobox,
                (QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed),
            ),
            (
                self.clone_button,
                (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
            ),
        )

        # Base Directory Label, Entry, and Browse Button
        self.directory_collection = self.add_horizontal_widgets(
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

        # Branch Label, Branch Menu, and Clone Button
        self.branch_collection = self.add_horizontal_widgets(
            (
                QLabel("Branch:"),
                (QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed),
            ),
            (
                self.branch_menu,
                (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed),
            ),
        )

        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.output_text)

        # Advanced Options Layout
        advanced_options_layout = QHBoxLayout()
        advanced_options_layout.addWidget(
            QLabel("Options:", self), alignment=Qt.AlignmentFlag.AlignLeft
        )
        advanced_options_layout.addWidget(
            self.advanced_checkbox, alignment=Qt.AlignmentFlag.AlignRight
        )

        # Add the advanced options layout to the main layout
        self.main_layout.addLayout(advanced_options_layout)
        self.main_layout.addWidget(
            self.options_widget, alignment=Qt.AlignmentFlag.AlignTop
        )

        on_repo_selection(self)

    def add_horizontal_widgets(self, *widgets_with_policies):
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)  # Remove horizontal margins

        for widget_with_policy in widgets_with_policies:
            widget, policy = widget_with_policy[:2]
            alignment = widget_with_policy[2] if len(widget_with_policy) > 2 else None

            # Set the specific size policy provided
            widget.setSizePolicy(policy[0], policy[1])

            if alignment:
                horizontal_layout.addWidget(widget, 0, alignment)
            else:
                horizontal_layout.addWidget(widget)

        # Add the horizontal layout to the main layout
        self.main_layout.addLayout(horizontal_layout)
        return horizontal_layout

    def start_building(self):
        copy_file_to_dir(
            self.rom_dir,
            self.workspace,
            f"baserom.{self.rom_region}.z64",
        )
        run_make(self.workspace)

    def connect_signals(self):
        self.advanced_checkbox.stateChanged.connect(self.update_advanced_options)
        self.repo_url_combobox.currentIndexChanged.connect(
            lambda _: on_repo_selection(self)
        )
        self.browse_button.clicked.connect(self.browse_directory)
        self.clone_button.clicked.connect(lambda _: start_cloning(self))

    def update_build_options(self, repo_options):
        for i in reversed(range(self.options_layout.count())):
            widget = self.options_layout.itemAt(i).widget()
            if widget:
                self.options_layout.removeWidget(widget)
                widget.setParent(None)

        add_options_to_layout(self, repo_options)

    def create_checkbox_handler(self, opt_name):
        return lambda state: self.user_selections.update(
            {opt_name: state == Qt.CheckState.Checked}
        )

    def create_combobox_handler(self, opt_name):
        return lambda text: self.user_selections.update({opt_name: text})

    def update_advanced_options(self):
        self.update_build_options(self.repo_options)
        # Set visibility of all widgets contained within the fork_collection layout
        visible = self.advanced_checkbox.isChecked()
        for i in range(self.branch_collection.count()):
            item = self.branch_collection.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setVisible(visible)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.clone_dir_entry.setText(directory)

    def update_output_text(self, text):
        self.output_text.append(text)

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def cloning_finished(self, success):
        if not success:
            return
        self.output_text.append("Cloning finished!")
        dump_user_selections(self)
        self.start_building()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Mario64All()
    window.show()
    sys.exit(app.exec())
