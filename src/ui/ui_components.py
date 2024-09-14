from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel, QComboBox, QLineEdit, QTextEdit, QProgressBar, QCheckBox,
    QPushButton, QWidget, QGridLayout, QHBoxLayout, QSizePolicy
)

from src.ui.uiutils import add_horizontal_widgets


class UISetup:
    def __init__(self, parent):
        self.parent = parent
        self.repo_url_combobox = QComboBox()
        self.repo_url_label = QLabel("Repository:")
        self.clone_dir_entry = QLineEdit(parent)
        self.branch_menu = QComboBox(parent)
        self.output_text = QTextEdit(parent)
        self.progress_bar = QProgressBar(parent)
        self.advanced_checkbox = QCheckBox("Show advanced options")
        self.browse_button = QPushButton("Browse...", parent)
        self.clone_button = QPushButton("Clone", parent)
        self.options_widget = QWidget()
        self.options_layout = QGridLayout(self.options_widget)
        self.fork_combobox = QComboBox()
        self.fork_label = QLabel("Fork:")

    def setup(self):
        self.parent.output_text = self.output_text
        self.output_text.setFixedHeight(200)

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
            (self.fork_combobox, (QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)),
            (self.clone_button, (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)),
        )

    def setup_directory_section(self):
        self.parent.directory_collection = add_horizontal_widgets(
            self.parent.main_layout,
            (QLabel("Base Directory:"), (QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)),
            (self.clone_dir_entry, (QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)),
            (self.browse_button, (QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)),
        )

    def setup_branch_section(self):
        self.parent.branch_collection = add_horizontal_widgets(
            self.parent.main_layout,
            (QLabel("Branch:"), (QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)),
            (self.branch_menu, (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)),
        )

    def setup_advanced_options(self):
        advanced_options_layout = QHBoxLayout()
        advanced_options_layout.addWidget(QLabel("Options:", self.parent), alignment=Qt.AlignmentFlag.AlignLeft)
        advanced_options_layout.addWidget(self.advanced_checkbox, alignment=Qt.AlignmentFlag.AlignRight)

        self.parent.main_layout.addLayout(advanced_options_layout)
        self.parent.main_layout.addWidget(self.options_widget, alignment=Qt.AlignmentFlag.AlignTop)

    def connect_signals(self):
        self.advanced_checkbox.stateChanged.connect(self.update_advanced_options)
        self.browse_button.clicked.connect(self.parent.repo_manager.browse_directory)

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
        self.output_text.append(text)

    def update_progress_bar(self, value):   
        self.progress_bar.setValue(value)
