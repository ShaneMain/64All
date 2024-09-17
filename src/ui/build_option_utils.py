from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QComboBox, QSpinBox, QHBoxLayout, QWidget

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

def adjust_window_height(window, num_rows):
    if window.ui_setup.advanced_checkbox.isChecked():
        base_height = 415 + window.ui_setup.branch_menu.height()
    else:
        base_height = 400
    row_height = 30  # Adjusted for single row layout
    additional_height = num_rows * row_height
    new_height = base_height + additional_height
    window.setFixedSize(850, new_height)