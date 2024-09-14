from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QComboBox, QSpinBox

selections = {}


def add_options_to_layout(window, repo_options):
    num_rows = 0

    for opt_name, opt_info in repo_options.items():
        is_advanced = opt_info.get("advanced", False)
        should_display = not is_advanced or window.ui_setup.advanced_checkbox.isChecked()

        if should_display:
            label = QLabel(opt_info.get("label", opt_name))
            label.setProperty("opt_name", opt_name)
            
            if isinstance(opt_info.get("values"), list):
                if len(opt_info["values"]) == 2 and set(opt_info["values"]) == {0, 1}:
                    # Binary option (0 and 1)
                    checkbox = QCheckBox()
                    checkbox.setProperty("opt_name", opt_name)
                    default_value = opt_info.get("default", opt_info["values"][0])
                    checkbox.setChecked(default_value == 1)
                    window.ui_setup.options_layout.addWidget(label, num_rows, 0)
                    window.ui_setup.options_layout.addWidget(checkbox, num_rows, 1)
                    setattr(window, f"{opt_name}_checkbox", checkbox)
                    checkbox.stateChanged.connect(create_checkbox_handler(window, opt_name))
                else:
                    # Multiple choice option
                    combobox = QComboBox()
                    combobox.setProperty("opt_name", opt_name)
                    combobox.addItems([str(value) for value in opt_info["values"]])
                    default_value = opt_info.get("default")
                    if default_value is not None:
                        combobox.setCurrentText(str(default_value))
                    
                    window.ui_setup.options_layout.addWidget(label, num_rows, 0)
                    window.ui_setup.options_layout.addWidget(combobox, num_rows, 1)
                    setattr(window, f"{opt_name}_combobox", combobox)
                    combobox.currentTextChanged.connect(create_combobox_handler(window, opt_name))
            elif isinstance(opt_info.get("values"), (int, float)):
                # Numeric option with a single value (assumed to be the maximum)
                spinbox = QSpinBox()
                spinbox.setProperty("opt_name", opt_name)
                spinbox.setMinimum(0)
                spinbox.setMaximum(int(opt_info["values"]))
                default_value = opt_info.get("default", 0)
                spinbox.setValue(int(default_value))
                
                window.ui_setup.options_layout.addWidget(label, num_rows, 0)
                window.ui_setup.options_layout.addWidget(spinbox, num_rows, 1)
                setattr(window, f"{opt_name}_spinbox", spinbox)
                spinbox.valueChanged.connect(create_spinbox_handler(window, opt_name))
            else:
                # Fallback to combobox for unknown types
                combobox = QComboBox()
                combobox.setProperty("opt_name", opt_name)
                combobox.addItems([str(value) for value in opt_info.get("values", [])])
                default_value = opt_info.get("default")
                if default_value is not None:
                    combobox.setCurrentText(str(default_value))
                
                window.ui_setup.options_layout.addWidget(label, num_rows, 0)
                window.ui_setup.options_layout.addWidget(combobox, num_rows, 1)
                setattr(window, f"{opt_name}_combobox", combobox)
                combobox.currentTextChanged.connect(create_combobox_handler(window, opt_name))

            num_rows += 1

    adjust_window_height(window, num_rows)


def adjust_window_height(window, num_rows):
    if window.ui_setup.advanced_checkbox.isChecked():
        base_height = 415 + window.ui_setup.branch_menu.height()
    else:
        base_height = 400
    row_height = 25
    additional_height = num_rows * row_height
    new_height = base_height + additional_height
    window.setFixedSize(675, new_height)

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
