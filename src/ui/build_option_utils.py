from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QComboBox, QSpinBox, QHBoxLayout, QWidget


def add_options_to_layout(window, repo_options):
    checkbox_options = []
    spinbox_options = []
    dropdown_options = []

    for opt_name, opt_info in repo_options.items():
        is_advanced = opt_info.get("advanced", False)
        should_display = (
            not is_advanced or window.ui_setup.advanced_checkbox.isChecked()
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

    # Clear existing layout
    for i in reversed(range(window.ui_setup.options_layout.count())):
        widget = window.ui_setup.options_layout.itemAt(i).widget()
        if widget:
            window.ui_setup.options_layout.removeWidget(widget)
            widget.setParent(None)

    # Add options to layout
    row = 0
    col = 0
    max_cols = 3  # Adjust this value to change the number of columns

    for opt_name, opt_info in all_options:
        option_widget = QWidget()
        option_layout = QHBoxLayout(option_widget)
        option_layout.setContentsMargins(0, 0, 0, 0)
        option_layout.setSpacing(5)

        label = QLabel(opt_info.get("label", opt_name))
        label.setProperty("opt_name", opt_name)
        option_layout.addWidget(label)

        if isinstance(opt_info.get("values"), list):
            if len(opt_info["values"]) == 2 and set(opt_info["values"]) == {0, 1}:
                widget = QCheckBox()
                widget.setChecked(
                    bool(
                        window.build_manager.user_selections.get(
                            opt_name,
                            opt_info.get("recommended")
                            or opt_info.get("default")
                            or False,
                        )
                    )
                )
                widget.stateChanged.connect(create_checkbox_handler(window, opt_name))
                option_layout.addStretch(1)  # Add stretch to push checkbox to the right
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
                    create_combobox_handler(window, opt_name)
                )
        elif isinstance(opt_info.get("values"), (int, float)):
            widget = QSpinBox()
            widget.setMinimum(0)
            widget.setMaximum(int(opt_info["values"]))
            current_value = window.build_manager.user_selections.get(
                opt_name, opt_info.get("recommended") or opt_info.get("default") or 0
            )
            widget.setValue(int(current_value))
            widget.valueChanged.connect(create_spinbox_handler(window, opt_name))
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

        window.ui_setup.options_layout.addWidget(option_widget, row, col)

        col += 1
        if col >= max_cols:
            col = 0
            row += 1

    # Add custom BUILD_TARGET dropdown at the end
    build_target_widget = QWidget()
    build_target_layout = QHBoxLayout(build_target_widget)
    build_target_layout.setContentsMargins(0, 0, 0, 0)
    build_target_layout.setSpacing(5)

    build_target_label = QLabel("Build Target")
    build_target_combo = QComboBox()
    build_target_combo.addItems(
        ["Linux", "OSX", "Web", "Windows", "Switch", "Raspberry Pi"]
    )
    build_target_combo.setObjectName("BUILD_TARGET_widget")
    build_target_combo.setProperty("opt_name", "BUILD_TARGET")

    current_target = window.build_manager.get_build_target()
    build_target_combo.setCurrentText(current_target)

    build_target_combo.currentTextChanged.connect(create_build_target_handler(window))

    build_target_layout.addWidget(build_target_label)
    build_target_layout.addWidget(build_target_combo)

    window.ui_setup.options_layout.addWidget(build_target_widget, row, col)

    # Adjust window height based on the number of rows
    adjust_window_height(window, row + 1)


def adjust_window_height(window, num_rows):
    if window.ui_setup.advanced_checkbox.isChecked():
        base_height = 415 + window.ui_setup.branch_menu.height()
    else:
        base_height = 400
    row_height = 30  # Adjusted for single row layout
    additional_height = num_rows * row_height
    new_height = base_height + additional_height
    window.setFixedSize(850, new_height)


def create_checkbox_handler(window, opt_name):
    def handler(state):
        value = 1 if state == Qt.CheckState.Checked else 0
        window.build_manager.update_user_selection(opt_name, value)

    return handler


def create_combobox_handler(window, opt_name):
    def handler(value):
        window.build_manager.update_user_selection(opt_name, value)

    return handler


def create_spinbox_handler(window, opt_name):
    def handler(value):
        window.build_manager.update_user_selection(opt_name, value)

    return handler


def create_build_target_handler(window):
    def handler(value):
        targets = [
            "OSX_BUILD",
            "TARGET_WEB",
            "WINDOWS_BUILD",
            "TARGET_SWITCH",
            "TARGET_RPI",
        ]
        for target in targets:
            window.build_manager.update_user_selection(target, 0)

        if value == "Linux":
            pass  # All targets are already set to 0
        elif value == "OSX":
            window.build_manager.update_user_selection("OSX_BUILD", 1)
        elif value == "Web":
            window.build_manager.update_user_selection("TARGET_WEB", 1)
        elif value == "Windows":
            window.build_manager.update_user_selection("WINDOWS_BUILD", 1)
        elif value == "Switch":
            window.build_manager.update_user_selection("TARGET_SWITCH", 1)
        elif value == "Raspberry Pi":
            window.build_manager.update_user_selection("TARGET_RPI", 1)

        print(f"Updated BUILD_TARGET to {value}")

    return handler
