import os
import sys

from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QComboBox,
    QProgressBar,
    QTextEdit,
    QPushButton,
    QCheckBox,
    QLineEdit,
    QFileDialog,
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
from yaml import dump, safe_load

from gitlogic import update_branch_menu, CloneWorker


class Mario64All(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.clone_worker = None

        self.browse_button = QPushButton("Browse...", self)
        self.clone_button = QPushButton("Clone", self)

        self.options_widget = QWidget()
        self.options_layout = QGridLayout(self.options_widget)
        self.options_layout.setSpacing(
            5
        )  # Set the spacing between elements in options layout
        self.options_widget.setLayout(self.options_layout)
        self.setup_ui()
        self.toggle_advanced_options(False)

    def load_repos(self):
        yaml_file = "repos.yaml"
        try:
            with open(yaml_file, "r") as file:
                data = safe_load(file)
                self.REPOS = data.get("repos", [])
                self.populate_repo_urls()
        except Exception as error:
            print(f"Error loading YAML file: {error}")

    def populate_repo_urls(self):
        self.repo_url_combobox.clear()
        for repo in self.REPOS:
            self.repo_url_combobox.addItem(repo["name"])

    def setup_ui(self):
        self.load_repos()
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
            (
                self.clone_button,
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

        self.on_repo_selection()

    def add_horizontal_widgets(self, *widgets_with_policies):
        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)  # Remove horizontal margins

        for widget, policy in widgets_with_policies:
            # Set the specific size policy provided
            widget.setSizePolicy(policy[0], policy[1])
            horizontal_layout.addWidget(widget)

        # Align all widgets to the left
        horizontal_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Add the horizontal layout to the main layout
        self.main_layout.addLayout(horizontal_layout)
        return horizontal_layout

    def connect_signals(self):
        self.advanced_checkbox.stateChanged.connect(self.toggle_advanced_options)
        self.repo_url_combobox.currentIndexChanged.connect(self.on_repo_selection)
        self.browse_button.clicked.connect(self.browse_directory)
        self.clone_button.clicked.connect(self.start_cloning)

    def on_repo_selection(self):
        repo_name = self.repo_url_combobox.currentText()

        self.repo_url = next(
            (repo["url"] for repo in self.REPOS if repo["name"] == repo_name), None
        )

        default_dir = os.path.abspath(f"./{repo_name}")
        self.clone_dir_entry.setText(default_dir)
        repo = next((repo for repo in self.REPOS if repo["name"] == repo_name), None)
        if repo:
            update_branch_menu(repo_name, self.REPOS, self.branch_menu)
            self.repo_options = repo.get("options", {})
            self.update_build_options(self.repo_options)

    def update_build_options(self, repo_options):
        for i in reversed(range(self.options_layout.count())):
            widget = self.options_layout.itemAt(i).widget()
            if widget:
                self.options_layout.removeWidget(widget)
                widget.setParent(None)

        self.add_options_to_layout(repo_options)

    def add_options_to_layout(self, repo_options):
        dropdowns = []
        checkboxes = []

        for opt_name, opt_info in repo_options.items():
            if "values" not in opt_info:
                continue

            if not opt_info.get("advanced") or self.advanced_checkbox.isChecked():
                if (
                    isinstance(opt_info["values"], list)
                    and len(opt_info["values"]) == 2
                    and 0 in opt_info["values"]
                ):
                    checkbox = QCheckBox(f"{opt_name}:", self)
                    checkbox.setCheckState(
                        Qt.CheckState.Checked
                        if opt_info.get("default", 0)
                        else Qt.CheckState.Unchecked
                    )
                    checkbox.stateChanged.connect(
                        self.create_checkbox_handler(opt_name)
                    )
                    checkboxes.append((opt_name, checkbox))
                else:
                    combobox_label = QLabel(f"{opt_name}:", self)
                    combobox = QComboBox(self)
                    combobox.addItems([str(value) for value in opt_info["values"]])
                    combobox.setCurrentText(str(opt_info.get("default", "")))
                    combobox.currentTextChanged.connect(
                        self.create_combobox_handler(opt_name)
                    )
                    dropdowns.append((combobox_label, combobox))

        row, col = 0, 0

        for label, combobox in dropdowns:
            self.options_layout.addWidget(label, row, col, 1, 1)
            self.options_layout.addWidget(combobox, row, col + 1, 1, 1)
            col += 2
            if col >= 6:  # Move to the next row after 3 columns
                row += 1
                col = 0

        for opt_name, checkbox in checkboxes:
            self.options_layout.addWidget(
                checkbox, row, col, 1, 2
            )  # Full span for checkboxes
            col += 2
            if col >= 6:  # Move to the next row after 3 columns
                row += 1
                col = 0

        # Adjust the window height based on the number of rows used
        self.adjust_window_height(row)

    def adjust_window_height(self, num_rows):
        base_height = 600
        row_height = 25  # Reduced height per row
        additional_height = num_rows * row_height
        new_height = base_height + additional_height
        self.setFixedSize(700, new_height)

    def create_checkbox_handler(self, opt_name):
        return lambda state: self.user_selections.update(
            {opt_name: state == Qt.CheckState.Checked}
        )

    def create_combobox_handler(self, opt_name):
        return lambda text: self.user_selections.update({opt_name: text})

    def toggle_advanced_options(self, state):
        self.update_build_options(self.repo_options)
        # Set visibility of all widgets contained within the fork_collection layout
        visible = self.advanced_checkbox.isChecked()
        for i in range(self.fork_collection.count()):
            item = self.fork_collection.itemAt(i)
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

    def cloning_finished(self):
        self.output_text.append("Cloning finished!")
        self.dump_user_selections()

    def start_cloning(self):
        clone_dir = self.clone_dir_entry.text()
        branch = self.branch_menu.currentText()

        self.worker = CloneWorker(self.repo_url, clone_dir, branch)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.worker.progress_signal.connect(self.update_progress_bar)
        self.worker.text_signal.connect(self.update_output_text)
        self.worker.finished_signal.connect(self.cloning_finished)

        self.thread.started.connect(self.worker.run)
        self.worker.finished_signal.connect(self.thread.quit)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        print("Starting cloning process...")
        self.thread.start()

    def dump_user_selections(self):
        try:
            # Ensure the clone directory exists
            clone_directory = self.clone_dir_entry.text()
            os.makedirs(clone_directory, exist_ok=True)

            # Populate the user selections with defaults for missing values
            populated_selections = {}
            for opt_name, opt_info in self.repo_options.items():
                if opt_name in self.user_selections:
                    # Use the user selection
                    populated_selections[opt_name] = self.user_selections[opt_name]
                else:
                    # Use the default value
                    populated_selections[opt_name] = opt_info.get("default", "")

            # Write to the YAML file
            selections_file = os.path.join(clone_directory, ".user_selections.yaml")
            with open(selections_file, "w") as file:
                dump(populated_selections, file)

            self.output_text.append(f"User selections saved to {selections_file}.")
        except Exception as error:
            self.output_text.append(f"Error saving selections: {error}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Mario64All()
    window.show()
    sys.exit(app.exec())
