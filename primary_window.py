import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QComboBox, QProgressBar, QTextEdit
from PyQt6.QtWidgets import QPushButton, QCheckBox, QLineEdit, QFileDialog, QWidget, QGridLayout, QVBoxLayout, \
    QScrollArea, QMessageBox
from yaml import dump, safe_load
from gitlogic import update_branch_menu, CloneWorker
from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QMainWindow, QComboBox, QVBoxLayout, QTextEdit, QPushButton, QLineEdit, QProgressBar, QLabel


class Mario64All(QMainWindow):
    def __init__(self):
        super().__init__()
        self.repo_url = None
        self.setWindowTitle("Mario Sixty For All")
        self.setFixedSize(700, 600)

        self.main_widget = QWidget()
        self.main_layout = QGridLayout(self.main_widget)
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
        self.options_layout = QVBoxLayout(self.options_widget)
        self.options_widget.setLayout(self.options_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.options_widget)

        self.setup_ui()

    def load_repos(self):
        yaml_file = 'repos.yaml'
        try:
            with open(yaml_file, 'r') as file:
                data = safe_load(file)
                self.REPOS = data.get('repos', [])
                self.populate_repo_urls()
        except Exception as error:
            print(f"Error loading YAML file: {error}")

    def populate_repo_urls(self):
        self.repo_url_combobox.clear()
        for repo in self.REPOS:
            self.repo_url_combobox.addItem(repo['name'])

    def setup_ui(self):
        self.load_repos()
        self.connect_signals()

        self.output_text.setFixedHeight(200)
        self.main_layout.addWidget(QLabel("Repository URL:"), 0, 0)
        self.main_layout.addWidget(self.repo_url_combobox, 0, 1, 1, 3)
        self.main_layout.addWidget(QLabel("Base Directory:"), 1, 0)
        self.main_layout.addWidget(self.clone_dir_entry, 1, 1, 1, 2)
        self.main_layout.addWidget(self.browse_button, 1, 3)
        self.main_layout.addWidget(QLabel("Branch:"), 2, 0)
        self.main_layout.addWidget(self.branch_menu, 2, 1, 1, 3)
        self.main_layout.addWidget(self.clone_button, 3, 0, 1, 4)
        self.main_layout.addWidget(self.progress_bar, 4, 0, 1, 4)
        self.main_layout.addWidget(self.output_text, 5, 0, 1, 4)
        self.main_layout.addWidget(self.advanced_checkbox, 6, 0, 1, 4)
        self.main_layout.addWidget(QLabel("Options:"), 7, 0, 1, 4)
        self.main_layout.addWidget(self.scroll_area, 8, 0, 1, 4)

    def connect_signals(self):
        self.advanced_checkbox.stateChanged.connect(self.toggle_advanced_options)
        self.repo_url_combobox.currentIndexChanged.connect(self.on_repo_selection)
        self.browse_button.clicked.connect(self.browse_directory)
        self.clone_button.clicked.connect(self.start_cloning)

    def on_repo_selection(self):
        repo_name = self.repo_url_combobox.currentText()

        self.repo_url = next((repo['url'] for repo in self.REPOS if repo['name'] == repo_name), None)

        default_dir = os.path.abspath(f"./{repo_name}")
        self.clone_dir_entry.setText(default_dir)
        repo = next((repo for repo in self.REPOS if repo['name'] == repo_name), None)
        if repo:
            update_branch_menu(repo_name, self.REPOS, self.branch_menu)
            self.repo_options = repo.get('options', {})
            self.update_build_options(self.repo_options)

    def update_build_options(self, repo_options):
        for i in reversed(range(self.options_layout.count())):
            widget = self.options_layout.itemAt(i).widget()
            if widget:
                self.options_layout.removeWidget(widget)
                widget.setParent(None)

        basic_options = {k: v for k, v in repo_options.items() if not v.get('advanced')}
        advanced_options = {k: v for k, v in repo_options.items() if v.get('advanced')}

        self.add_options_to_layout(basic_options)

        if self.advanced_checkbox.isChecked():
            self.add_options_to_layout(advanced_options)

    def add_options_to_layout(self, options):
        for opt_name, opt_info in options.items():
            if 'values' not in opt_info:
                continue

            label = QLabel(f"{opt_name}:")
            self.options_layout.addWidget(label)

            if isinstance(opt_info['values'], list) and len(opt_info['values']) == 2 and 0 in opt_info['values']:
                checkbox = QCheckBox(self)
                checkbox.setCheckState(Qt.CheckState.Checked if opt_info.get('default', 0) else Qt.CheckState.Unchecked)
                checkbox.stateChanged.connect(self.create_checkbox_handler(opt_name))
                self.options_layout.addWidget(checkbox)
            else:
                combobox = QComboBox(self)
                combobox.addItems([str(value) for value in opt_info['values']])
                combobox.setCurrentText(str(opt_info.get('default', '')))
                combobox.currentTextChanged.connect(self.create_combobox_handler(opt_name))
                self.options_layout.addWidget(combobox)

    def create_checkbox_handler(self, opt_name):
        return lambda state: self.user_selections.update({opt_name: state == Qt.CheckState.Checked})

    def create_combobox_handler(self, opt_name):
        return lambda text: self.user_selections.update({opt_name: text})

    def toggle_advanced_options(self, state):
        self.update_build_options(self.repo_options)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.clone_dir_entry.setText(directory)

    def update_output_text(self, text):
        self.output_text.append(text)

    def cloning_finished(self):
        self.output_text.append("Cloning finished!")

    def start_cloning(self):
        clone_dir = self.clone_dir_entry.text()
        branch = self.branch_menu.currentText()


        self.worker = CloneWorker(self.repo_url, clone_dir, branch)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.worker.progress_signal.connect(self.update_output_text)
        self.worker.finished_signal.connect(self.cloning_finished)

        self.thread.started.connect(self.worker.run)
        self.worker.finished_signal.connect(self.thread.quit)
        self.worker.finished_signal.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def on_clone_finished(self):
        self.dump_user_selections()

    def dump_user_selections(self):
        try:
            clone_directory = self.clone_dir_entry.text()
            os.makedirs(clone_directory, exist_ok=True)

            selections_file = os.path.join(clone_directory, 'user_selections.yaml')
            with open(selections_file, 'w') as file:
                dump(self.user_selections, file)
            self.output_text.append(f"User selections saved to {selections_file}.")
        except Exception as error:
            self.output_text.append(f"Error saving selections: {error}")

    def closeEvent(self, event):
        if self.clone_worker and self.clone_worker.isRunning():
            self.clone_worker.quit()
            self.clone_worker.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Mario64All()
    window.show()
    sys.exit(app.exec())
