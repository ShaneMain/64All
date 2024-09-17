import os

import yaml
from PyQt6.QtWidgets import QFileDialog

from ui.signal_connections import BASE_PATH


class RepoManager:
    def __init__(self, parent):
        self.parent = parent
        self.REPOS = []

    def load_repos(self):
        config_dir = os.path.join(BASE_PATH, "config", "repos")
        if not os.path.exists(config_dir):
            print(
                f"The repos directory was not found at {config_dir}. Please make sure it exists."
            )
            return

        self.REPOS = []
        for filename in os.listdir(config_dir):
            if filename.endswith(".yaml"):
                file_path = os.path.join(config_dir, filename)
                try:
                    with open(file_path, "r") as file:
                        repo_data = yaml.safe_load(file)
                        if isinstance(repo_data, list):
                            self.REPOS.extend(repo_data)
                        elif isinstance(repo_data, dict):
                            self.REPOS.append(repo_data)
                        else:
                            print(f"Invalid data structure in {filename}")
                except Exception as e:
                    print(f"Error loading {filename}: {str(e)}")

        if not self.REPOS:
            print(
                "No valid repository configurations were found in the repos directory."
            )
        else:
            print(f"Total repos loaded: {len(self.REPOS)}")

    def populate_repo_urls(self):
        if not hasattr(self.parent, "ui_setup") or self.parent.ui_setup is None:
            print("UI setup not initialized yet. Skipping repo URL population.")
            return

        self.parent.ui_setup.repo_url_combobox.blockSignals(True)
        self.parent.ui_setup.branch_combobox.blockSignals(True)

        self.parent.ui_setup.repo_url_combobox.clear()
        self.parent.ui_setup.branch_combobox.clear()
        for repo in self.REPOS:
            self.parent.ui_setup.repo_url_combobox.addItem(repo["name"])
            self.parent.ui_setup.branch_combobox.addItem(repo["name"])

        if self.REPOS:
            self.parent.ui_setup.repo_url_combobox.setCurrentIndex(0)
            self.parent.ui_setup.branch_combobox.setCurrentIndex(0)

        self.parent.ui_setup.repo_url_combobox.blockSignals(False)
        self.parent.ui_setup.branch_combobox.blockSignals(False)

        if self.REPOS:
            self.parent.ui_setup.on_repo_selection()

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self.parent, "Select Directory")
        if directory:
            self.parent.ui_setup.install_dir_entry.setText(directory)
