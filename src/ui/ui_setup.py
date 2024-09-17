from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextOption
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
    QSplitter,
    QFrame,
)

from ui.UIManagers.build_options_management import BuildOptionsManager
from ui.UIManagers.cloning_management import CloningFinishHandler
from ui.UIManagers.color_management import ColorManager
from ui.UIManagers.output_text_management import OutputTextManager
from ui.UIManagers.repo_info_management import RepoInfoManager
from ui.git_utils import CloningManager


class UISetup:
    def __init__(self, parent):
        self.parent = parent
        self.current_repo = None
        self.setup_ui_components()
        self.color_manager = ColorManager()
        self.output_text_manager = OutputTextManager(
            self.output_text, self.color_manager
        )
        self.repo_info_manager = RepoInfoManager(self)
        self.build_options_manager = BuildOptionsManager(self)
        self.cloning_finish_handler = CloningFinishHandler(self)
        self.cloning_manager = CloningManager()
        self.setup_signals()

    def setup_ui_components(self):
        # Initialize all UI components here
        self.repo_url_combobox = QComboBox(self.parent)
        self.repo_url_label = QLabel("Repository:")
        self.install_dir_entry = QLineEdit(self.parent)
        self.branch_menu = QComboBox(self.parent)
        self.output_text = QTextEdit(self.parent)
        self.progress_bar = QProgressBar(self.parent)
        self.advanced_checkbox = QCheckBox("Show advanced options")
        self.browse_button = QPushButton("Browse...", self.parent)
        self.clone_button = QPushButton("Build", self.parent)
        self.options_widget = QWidget()
        self.options_layout = QGridLayout(self.options_widget)
        self.branch_combobox = QComboBox()
        self.branch_label = QLabel("Branch:")
        self.repo_image = QLabel(self.parent)
        self.repo_trailer = QLabel(self.parent)
        self.repo_description = QTextEdit(self.parent)

        self.setup_output_text()

    def setup_output_text(self):
        self.output_text.setReadOnly(True)
        self.output_text.setAcceptRichText(True)
        self.output_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.output_text.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)

        font = QFont("Courier")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setPointSize(9)
        self.output_text.setFont(font)

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

    def setup_signals(self):
        self.repo_url_combobox.currentIndexChanged.connect(self.on_repo_selection)
        self.advanced_checkbox.stateChanged.connect(self.update_advanced_options)
        self.cloning_manager.progress_signal.connect(self.update_progress_bar)
        self.cloning_manager.text_signal.connect(
            self.output_text_manager.update_output_text
        )
        self.cloning_manager.finished_signal.connect(
            self.cloning_finish_handler.cloning_finished
        )

    def setup(self):
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = self.setup_left_section()
        right_widget = self.setup_right_section()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([left_widget.width(), 1100])

        main_layout.addWidget(splitter)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.parent.setCentralWidget(main_widget)

        self.update_advanced_options()

    def setup_left_section(self):
        left_widget = QWidget()
        left_widget.setFixedWidth(300)
        left_layout = QVBoxLayout(left_widget)

        self.image_frame = QFrame()
        self.image_frame.setFixedWidth(left_widget.width() - 20)
        self.image_frame.setFixedHeight(int(self.image_frame.width() * 9 / 16))
        image_layout = QVBoxLayout(self.image_frame)
        image_layout.setContentsMargins(0, 0, 0, 0)

        self.repo_image.setScaledContents(False)
        self.repo_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.repo_image)

        left_layout.addWidget(self.image_frame)
        left_layout.addWidget(self.repo_trailer)
        left_layout.addWidget(self.repo_description)
        left_layout.addStretch(1)

        return left_widget

    def setup_right_section(self):
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        self.setup_existing_content(right_layout)
        return right_widget

    def setup_existing_content(self, layout):
        grid_layout = QGridLayout()

        grid_layout.addWidget(self.repo_url_label, 0, 0)
        repo_layout = QHBoxLayout()
        repo_layout.addWidget(self.repo_url_combobox)
        grid_layout.addLayout(repo_layout, 0, 1)

        grid_layout.addWidget(QLabel("Install Directory:"), 1, 0)
        clone_dir_layout = QHBoxLayout()
        clone_dir_layout.addWidget(self.install_dir_entry)
        clone_dir_layout.addWidget(self.browse_button)
        grid_layout.addLayout(clone_dir_layout, 1, 1)

        grid_layout.addWidget(self.branch_label, 2, 0)
        grid_layout.addWidget(self.branch_menu, 2, 1)

        grid_layout.addWidget(self.advanced_checkbox, 3, 0, 1, 2)
        grid_layout.addWidget(self.options_widget, 4, 0, 1, 2)

        grid_layout.addWidget(self.clone_button, 5, 0, 1, 2)

        grid_layout.addWidget(self.progress_bar, 6, 0, 1, 2)

        grid_layout.addWidget(self.output_text, 7, 0, 1, 2)

        layout.addLayout(grid_layout)

    def on_repo_selection(self):
        self.repo_info_manager.on_repo_selection()

    def update_advanced_options(self):
        self.build_options_manager.update_advanced_options()

    def update_progress_bar(self, value):
        self.progress_bar.setValue(value)

    def set_build_button_enabled(self, enabled):
        self.clone_button.setEnabled(enabled)

    def start_cloning(self, repo_url, clone_dir, branch):
        self.cloning_manager.start_cloning(repo_url, clone_dir, branch)

    def cleanup(self):
        self.output_text_manager.cleanup()
