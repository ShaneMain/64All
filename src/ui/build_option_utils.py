from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QComboBox, QSpinBox, QHBoxLayout, QWidget

selections = {}


def add_options_to_layout(window, repo_options):
    checkbox_options = []
    other_options = []

    for opt_name, opt_info in repo_options.items():
        is_advanced = opt_info.get("advanced", False)
        should_display = not is_advanced or window.ui_setup.advanced_checkbox.isChecked()

        if should_display:
            if isinstance(opt_info.get("values"), list) and len(opt_info["values"]) == 2 and set(opt_info["values"]) == {0, 1}:
                checkbox_options.append((opt_name, opt_info))
            else:
                other_options.append((opt_name, opt_info))

    # Sort options
    checkbox_options.sort(key=lambda x: x[0])
    other_options.sort(key=lambda x: x[0])

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

    # Add checkbox options
    for opt_name, opt_info in checkbox_options:
        checkbox = QCheckBox(opt_info.get("label", opt_name))
        checkbox.setObjectName(f"{opt_name}_widget")
        checkbox.setProperty("opt_name", opt_name)
        checkbox.setChecked(opt_info.get("recommended") or opt_info.get("default") or False)
        
        # Add tooltip using the description
        tooltip = opt_info.get("description", "")
        if tooltip:
            checkbox.setToolTip(tooltip)
            checkbox.setToolTipDuration(5000)  # Show tooltip for 5 seconds

        window.ui_setup.options_layout.addWidget(checkbox, row, col)
        checkbox.stateChanged.connect(create_checkbox_handler(window, opt_name))

        col += 1
        if col >= max_cols:
            col = 0
            row += 1

    # Add other options
    for opt_name, opt_info in other_options:
        option_widget = QWidget()
        option_layout = QHBoxLayout(option_widget)
        option_layout.setContentsMargins(0, 0, 0, 0)
        option_layout.setSpacing(5)

        label = QLabel(opt_info.get("label", opt_name))
        label.setProperty("opt_name", opt_name)
        option_layout.addWidget(label)

        if isinstance(opt_info.get("values"), list):
            widget = QComboBox()
            widget.addItems([str(value) for value in opt_info["values"]])
            if opt_info.get("recommended") is not None:
                widget.setCurrentText(str(opt_info["recommended"]))
            elif opt_info.get("default") is not None:
                widget.setCurrentText(str(opt_info["default"]))
            widget.currentTextChanged.connect(create_combobox_handler(window, opt_name))
        elif isinstance(opt_info.get("values"), (int, float)):
            widget = QSpinBox()
            widget.setMinimum(0)
            widget.setMaximum(int(opt_info["values"]))
            widget.setValue(opt_info.get("recommended") or opt_info.get("default") or 0)
            widget.valueChanged.connect(create_spinbox_handler(window, opt_name))
        else:
            widget = QComboBox()
            widget.addItems([str(value) for value in opt_info.get("values", [])])
            widget.currentTextChanged.connect(create_combobox_handler(window, opt_name))

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

    adjust_window_height(window, row + 1)


def adjust_window_height(window, num_rows):
    if window.ui_setup.advanced_checkbox.isChecked():
        base_height = 415 + window.ui_setup.branch_menu.height()
    else:
        base_height = 400
    row_height = 30  # Adjusted for single row layout
    additional_height = num_rows * row_height
    new_height = base_height + additional_height
    window.resize(1400, new_height)


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
