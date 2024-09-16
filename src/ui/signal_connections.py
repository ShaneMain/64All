import os
import sys

from src.ui.git_utils import start_cloning

if getattr(sys, "frozen", False):
    # Running in a PyInstaller bundle
    BASE_PATH = sys._MEIPASS
else:
    # Running in a normal Python environment
    BASE_PATH = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def connect_signals(window):
    # UI Setup signals
    window.ui_setup.connect_signals()

    # Repo Manager signals
    window.ui_setup.clone_button.clicked.connect(lambda: start_cloning(window))
    window.ui_setup.repo_url_combobox.currentIndexChanged.connect(
        lambda _: window.ui_setup.repo_url_combobox.currentIndexChanged.connect(
            window.ui_setup.on_repo_selection
        )
    )
    window.ui_setup.branch_combobox.currentIndexChanged.connect(
        lambda _: window.ui_setup.repo_url_combobox.currentIndexChanged.connect(
            window.ui_setup.on_repo_selection
        )
    )

    # Build Manager signals
    # Add any build-related signals here


def cloning_finished(window, success):
    if not success:
        return
    window.ui_setup.update_output_text("Cloning finished!")
    window.build_manager.start_building()
