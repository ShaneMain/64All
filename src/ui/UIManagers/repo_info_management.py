import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from ui.signal_connections import BASE_PATH

class RepoInfoManager:
    def __init__(self, ui_setup):
        self.ui_setup = ui_setup

    def on_repo_selection(self):
        repo_name = self.ui_setup.repo_url_combobox.currentText()
        if not repo_name or repo_name == self.ui_setup.current_repo:
            return

        self.ui_setup.current_repo = repo_name
        repo = next((repo for repo in self.ui_setup.parent.repo_manager.REPOS if repo["name"] == repo_name), None)
        if repo:
            self.update_repo_info(repo)
            self.update_build_options(repo)
            print(f"Selected repo: {repo_name}, Options: {self.ui_setup.parent.repo_options}")
        else:
            print(f"Repository {repo_name} not found in loaded repos.")

    def update_repo_info(self, repo):
        info = repo.get("info", {})

        self.update_repo_image(info)
        self.update_repo_description(info)
        self.update_repo_trailer(info)

    def update_repo_image(self, info):
        image_name = info.get("image", "")
        image_path = os.path.join(BASE_PATH, "config", "images", image_name)

        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    300, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.ui_setup.repo_image.setPixmap(scaled_pixmap)
            else:
                print(f"Failed to load image: {image_path}")
                self.ui_setup.repo_image.clear()
        else:
            print(f"Image file not found: {image_path}")
            self.ui_setup.repo_image.clear()

    def update_repo_description(self, info):
        description = info.get("description", "No description available.")
        self.ui_setup.repo_description.setPlainText(description)

    def update_repo_trailer(self, info):
        trailer_link = info.get("trailer", "")
        if trailer_link:
            self.ui_setup.repo_trailer.setText(f'<a href="{trailer_link}">Watch Trailer</a>')
            self.ui_setup.repo_trailer.setOpenExternalLinks(True)
        else:
            self.ui_setup.repo_trailer.clear()

    def update_build_options(self, repo):
        self.ui_setup.parent.repo_url = repo.get("url")
        default_dir = os.path.expanduser(f"~/{repo['name']}")
        self.ui_setup.install_dir_entry.setText(default_dir)

        self.ui_setup.parent.build_dependencies = repo.get("dependencies", [])

        from core.gitlogic import update_branch_menu
        update_branch_menu(repo["name"], self.ui_setup.parent.repo_manager.REPOS, self.ui_setup.branch_menu)

        self.ui_setup.parent.repo_options = {}
        self.ui_setup.parent.build_manager.user_selections = {}

        self.ui_setup.parent.repo_options = repo.get("options", {})
        self.ui_setup.parent.build_manager.update_build_options(self.ui_setup.parent.repo_options)

        self.ui_setup.branch_combobox.setCurrentText(repo["name"])

        self.ui_setup.update_advanced_options()