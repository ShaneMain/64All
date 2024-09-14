from src.ui.git_utils import start_cloning, on_repo_selection, on_fork_selection

def connect_signals(window):
    # UI Setup signals
    window.ui_setup.connect_signals()

    # Repo Manager signals
    window.ui_setup.clone_button.clicked.connect(lambda: start_cloning(window))
    window.ui_setup.repo_url_combobox.currentIndexChanged.connect(
        lambda _: on_repo_selection(window)
    )
    window.ui_setup.fork_combobox.currentIndexChanged.connect(
        lambda _: on_fork_selection(window)
    )

    # Build Manager signals
    # Add any build-related signals here

def cloning_finished(window, success):
    if not success:
        return
    window.ui_setup.update_output_text("Cloning finished!")
    window.build_manager.start_building()