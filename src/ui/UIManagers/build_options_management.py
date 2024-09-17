from PyQt6.QtWidgets import QWidget, QCheckBox, QComboBox, QSpinBox, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from ui.build_option_utils import (
    create_checkbox_handler,
    create_combobox_handler,
    create_spinbox_handler,
    adjust_window_height,
)

class BuildOptionsManager:
    def __init__(self, ui_setup):
        self.ui_setup = ui_setup

    def update_advanced_options(self):
        visible = self.ui_setup.advanced_checkbox.isChecked()
        current_selections = self.ui_setup.parent.build_manager.user_selections.copy()

        self.ui_setup.branch_label.setVisible(visible)
        self.ui_setup.branch_menu.setVisible(visible)

        self.ui_setup.parent.build_manager.update_build_options(self.ui_setup.parent.repo_options)

        for opt_name, value in current_selections.items():
            self.ui_setup.parent.build_manager.update_user_selection(opt_name, value)

        self.refresh_options_layout()

        build_target_widget = self.ui_setup.options_layout.findChild(QWidget, "BUILD_TARGET_widget")
        if build_target_widget:
            build_target_widget.setVisible(True)

    def refresh_options_layout(self):
        # Clear existing layout
        for i in reversed(range(self.ui_setup.options_layout.count())):
            widget = self.ui_setup.options_layout.itemAt(i).widget()
            if widget:
                self.ui_setup.options_layout.removeWidget(widget)
                widget.setParent(None)

        # Recreate the layout with updated options
        self.add_options_to_layout(self.ui_setup.parent, self.ui_setup.parent.repo_options)

        # Update widget values based on current user selections
        for opt_name, value in self.ui_setup.parent.build_manager.user_selections.items():
            widget = self.ui_setup.options_layout.findChild(QWidget, f"{opt_name}_widget")
            if widget:
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                    print(f"Updating checkbox {opt_name} to {bool(value)}")  # Debug print
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(value))
                elif isinstance(widget, QSpinBox):
                    widget.setValue(int(value))

    def add_options_to_layout(self, window, repo_options):
        checkbox_options = []
        spinbox_options = []
        dropdown_options = []
        for opt_name, opt_info in repo_options.items():
            is_advanced = opt_info.get("advanced", False)
            should_display = (
                not is_advanced or self.ui_setup.advanced_checkbox.isChecked()
            )
            if should_display:
                if isinstance(opt_info.get("values"), list):
                    if len(opt_info["values"]) == 2 and set(opt_info["values"]) == {0, 1}:
                        checkbox_options.append((opt_name, opt_info))
                    else:
                        dropdown_options.append((opt_name, opt_info))
                elif isinstance(opt_info.get("values"), (int, float)):
                    spinbox_options.append((opt_name, opt_info))

        # Sort options within their groups
        checkbox_options.sort(key=lambda x: x[0])
        spinbox_options.sort(key=lambda x: x[0])
        dropdown_options.sort(key=lambda x: x[0])

        # Combine sorted options
        all_options = checkbox_options + spinbox_options + dropdown_options

        # Add options to layout
        row = 0
        col = 0
        max_cols = 3  # Adjust this value to change the number of columns

        for opt_name, opt_info in all_options:
            option_widget = QWidget()
            option_layout = QHBoxLayout(option_widget)
            option_layout.setContentsMargins(0, 0, 0, 0)
            option_layout.setSpacing(5)

            # Create and add the label
            label = QLabel(opt_name)
            option_layout.addWidget(label)

            if isinstance(opt_info.get("values"), list):
                if len(opt_info["values"]) == 2 and set(opt_info["values"]) == {0, 1}:
                    widget = QCheckBox()
                    current_value = window.build_manager.user_selections.get(
                        opt_name,
                        opt_info.get("recommended")
                        or opt_info.get("default")
                        or False,
                    )
                    widget.setChecked(bool(current_value))
                    widget.stateChanged.connect(
                        lambda state, name=opt_name: self.checkbox_state_changed(name, state)
                    )
                    print(f"Connected checkbox signal for {opt_name}")  # New debug print
                    option_layout.addStretch(1)
                else:
                    widget = QComboBox()
                    widget.addItems([str(value) for value in opt_info["values"]])
                    current_value = str(
                        window.build_manager.user_selections.get(
                            opt_name,
                            opt_info.get("recommended")
                            or opt_info.get("default")
                            or opt_info["values"][0],
                        )
                    )
                    widget.setCurrentText(current_value)
                    widget.currentTextChanged.connect(
                        lambda value, name=opt_name: create_combobox_handler(window, name)(
                            value
                        )
                    )
            elif isinstance(opt_info.get("values"), (int, float)):
                widget = QSpinBox()
                widget.setMinimum(0)
                widget.setMaximum(int(opt_info["values"]))
                current_value = window.build_manager.user_selections.get(
                    opt_name, opt_info.get("recommended") or opt_info.get("default") or 0
                )
                widget.setValue(int(current_value))
                widget.valueChanged.connect(
                    lambda value, name=opt_name: create_spinbox_handler(window, name)(value)
                )
            else:
                widget = QLabel("Invalid option type")

            widget.setObjectName(f"{opt_name}_widget")
            widget.setProperty("opt_name", opt_name)
            option_layout.addWidget(widget)

            # Add tooltip using the description
            tooltip = opt_info.get("description", "")
            if tooltip:
                option_widget.setToolTip(tooltip)
                option_widget.setToolTipDuration(5000)  # Show tooltip for 5 seconds

            self.ui_setup.options_layout.addWidget(option_widget, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Ensure that the BUILD_TARGET option is always visible
        build_target_widget = self.ui_setup.options_layout.findChild(
            QWidget, "BUILD_TARGET_widget"
        )
        if build_target_widget:
            build_target_widget.setVisible(True)

        # Adjust window height
        adjust_window_height(window, row + 1)

    def checkbox_state_changed(self, opt_name, state):
        value = 1 if state == Qt.CheckState.Checked.value else 0
        self.ui_setup.parent.build_manager.update_user_selection(opt_name, value)
        print(f"Checkbox {opt_name} changed to {value}")  # Debug print
        print(f"Checkbox state: {state}")  # Additional debug print