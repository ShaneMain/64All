from PyQt6.QtWidgets import QFileDialog


class RepoManager:
    def __init__(self, parent):
        self.parent = parent
        self.REPOS = []

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self.parent, "Select Directory")
        if directory:
            self.parent.ui_setup.clone_dir_entry.setText(directory)

    def populate_repo_urls(self):
        self.parent.ui_setup.repo_url_combobox.clear()
        self.parent.ui_setup.branch_combobox.clear()
        for repo in self.REPOS:
            self.parent.ui_setup.repo_url_combobox.addItem(repo["name"])
            self.parent.ui_setup.branch_combobox.addItem(repo["name"])

        # Set the current index to 0 for both comboboxes
        self.parent.ui_setup.repo_url_combobox.setCurrentIndex(0)
        self.parent.ui_setup.branch_combobox.setCurrentIndex(0)
