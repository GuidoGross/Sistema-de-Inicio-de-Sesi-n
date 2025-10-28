from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QAbstractItemView
from PyQt6.QtCore import Qt
from gui_utilities import gui_utilities

class Utilities:

    @staticmethod
    def create_add_form(title, confirm_button_callback, cancel_button_callback, content_widget, normal_fields = [], grid_fields = [], width_fraction = 3.0):
        main_layout = gui_utilities.switch_content_widget(content_widget)
        main_layout.addLayout(gui_utilities.create_title(text = title, font_size = 24, background_color = "#333333"))
        main_layout.addStretch()
        fields_container = QWidget()
        main_layout.addWidget(fields_container, alignment = Qt.AlignmentFlag.AlignCenter)
        fields_container.setFixedWidth(gui_utilities.get_responsive_width(window = content_widget, fraction = width_fraction))
        fields_layout = QVBoxLayout(fields_container)
        fields_layout.setSpacing(10)
        inputs = []
        for field in normal_fields:
            widget = None
            if field["type"] == "label":
                widget = gui_utilities.create_label(text = field.get("text", ""), background_color = "#333333")
                fields_layout.addWidget(widget, alignment = Qt.AlignmentFlag.AlignLeft)
            elif field["type"] == "text_box":
                widget = gui_utilities.create_text_box(placeholder_text = field.get("placeholder", ""), hide_text = field.get("hide_text", False))
                fields_layout.addWidget(widget)
                inputs.append(widget)
            elif field["type"] == "combo_box":
                widget = gui_utilities.create_combo_box(placeholder_text = field.get("placeholder", ""), items = field.get("items", []))
                fields_layout.addWidget(widget)
                inputs.append(widget)
            elif field["type"] == "check_box":
                widget = gui_utilities.create_checkbox(text = field.get("text", ""), background_color = "#333333")
                fields_layout.addWidget(widget)
                inputs.append(widget)
        if grid_fields:
            grid_layout = QGridLayout()
            grid_layout.setSpacing(10)
            row = 0
            column = 0
            skip_next = False
            for i, field in enumerate(grid_fields):
                if skip_next:
                    skip_next = False
                    continue
                widget = None
                if field.get("placeholder") == "D.N.I." and i + 1 < len(grid_fields) and grid_fields[i + 1].get("placeholder") == "Edad":
                    id_number_widget = gui_utilities.create_text_box(placeholder_text = "D.N.I.")
                    age_widget = gui_utilities.create_text_box(placeholder_text = "Edad")
                    id_number_and_age_layout = QHBoxLayout()
                    id_number_and_age_layout.setSpacing(10)
                    id_number_and_age_layout.addWidget(id_number_widget, 3)
                    id_number_and_age_layout.addWidget(age_widget, 1)
                    grid_layout.addLayout(id_number_and_age_layout, row, 0, 1, 1)
                    inputs.extend([id_number_widget, age_widget])
                    column += 1
                    skip_next = True
                    continue
                if field["type"] == "text_box":
                    widget = gui_utilities.create_text_box(placeholder_text = field.get("placeholder", ""), hide_text = field.get("hide_text", False))
                elif field["type"] == "combo_box":
                    widget = gui_utilities.create_combo_box(placeholder_text = field.get("placeholder", ""), items = field.get("items", []))
                elif field["type"] == "check_box": widget = gui_utilities.create_checkbox(text = field.get("text", ""), background_color = "#333333")
                if widget:
                    grid_layout.addWidget(widget, row, column)
                    inputs.append(widget)
                    column += 1
                    if column > 1:
                        column = 0
                        row += 1
            fields_layout.addLayout(grid_layout)
        main_layout.addStretch()
        buttons_container = QWidget()
        main_layout.addWidget(buttons_container, alignment = Qt.AlignmentFlag.AlignCenter)
        buttons_container.setFixedWidth(gui_utilities.get_responsive_width(window = content_widget, fraction = width_fraction))
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(10)
        confirm_button = gui_utilities.create_button(text = "Confirmar")
        buttons_layout.addWidget(confirm_button)
        confirm_button.clicked.connect(lambda: confirm_button_callback(inputs))
        cancel_button = gui_utilities.create_button(text = "Cancelar")
        buttons_layout.addWidget(cancel_button)
        cancel_button.clicked.connect(cancel_button_callback)
        return main_layout
    
    @staticmethod
    def create_delete_and_edit_form(
            window,
            title,
            items_data,
            column_headers,
            column_proportions,
            row_populator_function,
            action_button_text,
            action_function,
            filter_enabled = True
    ):
        main_layout = gui_utilities.switch_content_widget(window.content_widget)
        main_layout.addLayout(gui_utilities.create_title(text = title, font_size = 24, background_color = "#333333"))
        if filter_enabled:
            search_bar = gui_utilities.create_text_box("Buscar...")
            main_layout.addWidget(search_bar)
        table = gui_utilities.create_list_table(
            items_data = items_data,
            column_headers = column_headers,
            column_proportions = column_proportions,
            row_populator_function = row_populator_function
        )
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        main_layout.addWidget(table)
        if filter_enabled:
        
            def filter_table():
                search_text = search_bar.text().lower()
                for i in range(table.rowCount()):
                    item = table.item(i, 0)
                    if item: table.setRowHidden(i, search_text not in item.text().lower())
            
            search_bar.textChanged.connect(filter_table)
        buttons_layout = QHBoxLayout()
        main_layout.addLayout(buttons_layout)
        buttons_layout.setSpacing(10)
        confirm_button = gui_utilities.create_button(text = action_button_text)
        confirm_button.clicked.connect(lambda: action_function(table))
        buttons_layout.addWidget(confirm_button)
        cancel_button = gui_utilities.create_button(text = "Cancelar")
        buttons_layout.addWidget(cancel_button)
        cancel_button.clicked.connect(lambda: gui_utilities.switch_instance(window, window.mannage_users))
        return main_layout