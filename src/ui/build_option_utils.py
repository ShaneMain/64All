import os

import yaml
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QLabel, QComboBox

selections = {}


def add_options_to_layout(obj, repo_options):
    dropdowns = []
    checkboxes = []
    obj.repo_options = repo_options

    for opt_name, opt_info in repo_options.items():
        if "values" not in opt_info:
            continue

        if not opt_info.get("advanced") or obj.advanced_checkbox.isChecked():
            tooltip_text = opt_info.get("description", "")
            default_value = opt_info.get("recommended", opt_info.get("default", ""))

            if (
                isinstance(opt_info["values"], list)
                and len(opt_info["values"]) == 2
                and 0 in opt_info["values"]
            ):
                checkbox = QCheckBox(f"{opt_name}:", obj)
                checkbox.setCheckState(
                    Qt.CheckState.Checked if default_value else Qt.CheckState.Unchecked
                )
                checkbox.setToolTip(tooltip_text)
                checkbox.stateChanged.connect(create_checkbox_handler(obj, opt_name))
                checkboxes.append((opt_name, checkbox))
                selections[opt_name] = checkbox.isChecked()
            else:
                combobox_label = QLabel(f"{opt_name}:", obj)
                combobox_label.setToolTip(tooltip_text)
                combobox = QComboBox(obj)
                combobox.addItems([str(value) for value in opt_info["values"]])
                combobox.setCurrentText(str(default_value))
                combobox.setToolTip(tooltip_text)
                combobox.currentTextChanged.connect(
                    create_combobox_handler(obj, opt_name)
                )
                dropdowns.append((combobox_label, combobox))
                selections[opt_name] = combobox.currentText()

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


def dump_user_selections(obj):
    try:
        # Ensure the clone directory exists
        clone_directory = obj.workspace
        os.makedirs(clone_directory, exist_ok=True)

        # Filter selections to only include those that are not default
        non_default_selections = {}
        for opt_name, opt_info in obj.repo_options.items():
            # Ensure we get sensible default values
            recommended_value = opt_info.get("recommended")
            default_value = (
                opt_info.get("default")
                if recommended_value is None
                else recommended_value
            )

            # Get the current selection
            current_value = selections.get(opt_name)

            # Compare current value with the defaults (consider bool/int conversions as well)
            if current_value is not None and str(current_value) != str(default_value):
                non_default_selections[opt_name] = current_value

        # Write to the YAML file
        selections_file = os.path.join(clone_directory, ".user_selections.yaml")
        with open(selections_file, "w") as file:
            yaml.dump(non_default_selections, file)

        obj.output_text.append(f"User selections saved to {selections_file}.")
    except Exception as error:
        obj.output_text.append(f"Error saving selections: {error}")


def create_checkbox_handler(obj, opt_name):
    return lambda state: obj.user_selections.update(
        {opt_name: state == Qt.CheckState.Checked}
    )


def create_combobox_handler(obj, opt_name):
    return lambda text: obj.user_selections.update({opt_name: text})

    return handler
