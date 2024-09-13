from PyQt6.QtWidgets import QHBoxLayout


def add_horizontal_widgets(window, *widgets_with_policies):
    horizontal_layout = QHBoxLayout()
    horizontal_layout.setContentsMargins(0, 0, 0, 0)  # Remove horizontal margins

    for widget_with_policy in widgets_with_policies:
        widget, policy = widget_with_policy[:2]
        alignment = widget_with_policy[2] if len(widget_with_policy) > 2 else None

        # Set the specific size policy provided
        widget.setSizePolicy(policy[0], policy[1])

        if alignment:
            horizontal_layout.addWidget(widget, 0, alignment)
        else:
            horizontal_layout.addWidget(widget)

    # Add the horizontal layout to the main layout
    window.addLayout(horizontal_layout)
    return horizontal_layout
