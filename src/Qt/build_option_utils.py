from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QComboBox


def add_options_to_layout(obj, repo_options):
    dropdowns = []
    checkboxes = []

    for opt_name, opt_info in repo_options.items():
        if "values" not in opt_info:
            continue

        if not opt_info.get("advanced") or obj.advanced_checkbox.isChecked():
            tooltip_text = opt_info.get("description", "")

            if (
                    isinstance(opt_info["values"], list)
                    and len(opt_info["values"]) == 2
                    and 0 in opt_info["values"]
            ):
                checkbox = QCheckBox(f"{opt_name}:", obj)
                checkbox.setCheckState(
                    Qt.CheckState.Checked
                    if opt_info.get("default", 0)
                    else Qt.CheckState.Unchecked
                )
                checkbox.stateChanged.connect(
                    obj.create_checkbox_handler(opt_name)
                )
                checkbox.setToolTip(tooltip_text)
                checkboxes.append((opt_name, checkbox))
            else:
                combobox_label = QLabel(f"{opt_name}:", obj)
                combobox_label.setToolTip(tooltip_text)
                combobox = QComboBox(obj)
                combobox.addItems([str(value) for value in opt_info["values"]])
                combobox.setCurrentText(str(opt_info.get("default", "")))
                combobox.currentTextChanged.connect(
                    obj.create_combobox_handler(opt_name)
                )
                combobox.setToolTip(tooltip_text)
                dropdowns.append((combobox_label, combobox))

    row, col = 0, 0

    for label, combobox in dropdowns:
        obj.options_layout.addWidget(label, row, col, 1, 1)
        obj.options_layout.addWidget(combobox, row, col + 1, 1, 1)
        col += 2
        if col >= 6:  # Move to the next row after 3 columns
            row += 1
            col = 0

    for opt_name, checkbox in checkboxes:
        obj.options_layout.addWidget(
            checkbox, row, col, 1, 2
        )  # Full span for checkboxes
        col += 2
        if col >= 6:  # Move to the next row after 3 columns
            row += 1
            col = 0

    # Adjust the window height based on the number of rows used
    adjust_window_height(obj, row)


def adjust_window_height(obj, num_rows):
    if obj.advanced_checkbox.isChecked():
        base_height = 415 + obj.branch_menu.height()
    else:
        base_height = 400
    row_height = 25
    additional_height = num_rows * row_height
    new_height = base_height + additional_height
    obj.setFixedSize(675, new_height)


