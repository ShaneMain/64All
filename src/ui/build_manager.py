from src.core.buildlogic import symlink_file_to_dir, run_make
from src.ui.build_option_utils import add_options_to_layout


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
        self.build_process = run_make(
            self.parent.workspace,
            build_dependencies=self.parent.build_dependencies,
            ui_setup=self.parent.ui_setup,
            user_selections=self.user_selections,
        )
        self.build_process.finished.connect(self.build_finished)

    def build_finished(self, success):
        if success:
            self.parent.ui_setup.update_output_text(
                "[32m Build completed successfully! [0m"
            )
        else:
            self.parent.ui_setup.update_output_text(
                "[31m Build failed. Check the output for errors. [0m"
            )

    def update_build_options(self, repo_options):
        # Store current selections
        current_selections = self.user_selections.copy()

        # Clear the layout
        for i in reversed(range(self.parent.ui_setup.options_layout.count())):
            widget = self.parent.ui_setup.options_layout.itemAt(i).widget()
            if widget:
                self.parent.ui_setup.options_layout.removeWidget(widget)
                widget.setParent(None)

        # Rebuild the layout
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

    def update_user_selection(self, opt_name, value):
        if isinstance(value, str):
            # Try to convert string values to int or float if possible
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
        self.user_selections[opt_name] = value
        print(f"Updated {opt_name} to {value}")
