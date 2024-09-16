import os

import yaml

from core.distrobox import run_ephemeral_command
from src.core.buildlogic import symlink_file_to_dir
from ui.signal_connections import BASE_PATH


class BuildManager:
    def __init__(self, parent):
        self.parent = parent
        self.user_selections = {}
        self.build_process = None

    def start_building(self):
        symlink_file_to_dir(
            self.parent.rom_dir,
            self.parent.workspace,
            f"baserom.{self.parent.rom_region}.z64",
        )
        print(self.parent.build_dependencies)

        command = "make -j$(nproc) " + " ".join(
            [f"{k}={v}" for k, v in self.user_selections.items()]
        )

        run_ephemeral_command(
            command,
            ui_setup=self.parent.ui_setup,
            directory=self.parent.workspace,
            additional_packages=self.parent.build_dependencies,
            on_complete=self.build_finished,
        )

    def build_finished(self, success):
        if success:
            self.parent.ui_setup.update_output_text(
                "[32m Build completed successfully! [0m"
            )
        else:
            self.parent.ui_setup.update_output_text(
                "[31m Build failed. Check the output for errors. [0m"
            )

    def load_repo_configs(self):
        repo_configs = {}
        config_dir = os.path.join(BASE_PATH, "config", "repos")     

        for filename in os.listdir(config_dir):
            if filename.endswith(".yaml"):
                with open(os.path.join(config_dir, filename), "r") as file:
                    config = yaml.safe_load(file)
                    for repo in config:
                        repo_configs[repo["name"]] = repo

        return repo_configs

    def update_build_options(self, repo_options=None):
        current_repo = self.parent.ui_setup.repo_url_combobox.currentText()

        if not current_repo:
            print("No repository selected. Please select a repository first.")
            return

        if repo_options is None:
            repo_options = self.parent.repo_options.get(current_repo, {})

        if not repo_options:
            print(f"No options found for repository: {current_repo}")
            return

        # Store current selections
        current_selections = self.user_selections.copy()

        # Clear the layout
        for i in reversed(range(self.parent.ui_setup.options_layout.count())):
            widget = self.parent.ui_setup.options_layout.itemAt(i).widget()
            if widget:
                self.parent.ui_setup.options_layout.removeWidget(widget)
                widget.setParent(None)

        # Rebuild the layout
        from ui.build_option_utils import add_options_to_layout

        add_options_to_layout(self.parent, repo_options)

        # Restore selections, using recommended or default values for new options
        for opt_name, opt_info in repo_options.items():
            if opt_name in current_selections:
                # Restore previous selection
                self.update_user_selection(opt_name, current_selections[opt_name])
            else:
                # New option: use recommended or default value
                recommended_value = opt_info.get("recommended")
                default_value = opt_info.get("default")
                if recommended_value is not None:
                    self.update_user_selection(opt_name, recommended_value)
                elif default_value is not None:
                    self.update_user_selection(opt_name, default_value)

    def update_user_selection(self, option_name, value):
        self.user_selections[option_name] = value
        # Update the UI to reflect the new selection
        # This part depends on how your UI is structured

    def get_build_target(self):
        if self.user_selections.get("OSX_BUILD", 0) == 1:
            return "OSX"
        elif self.user_selections.get("TARGET_WEB", 0) == 1:
            return "Web"
        elif self.user_selections.get("WINDOWS_BUILD", 0) == 1:
            return "Windows"
        elif self.user_selections.get("TARGET_SWITCH", 0) == 1:
            return "Switch"
        elif self.user_selections.get("TARGET_RPI", 0) == 1:
            return "Raspberry Pi"
        else:
            return "Linux"
