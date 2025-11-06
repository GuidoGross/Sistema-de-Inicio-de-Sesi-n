import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gui_utilities import gui_utilities
from Utilities import Utilities
from PyQt6.QtCore import Qt, QTimer, QEvent, QObject
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidgetItem, QDialog
import json
from datetime import datetime
from Core.User import User
from Core.Account import Account
from Core.Role import Role
from Core.Action import Action
from DB.Users import Users
from DB.Accounts import Accounts
from DB.Roles import Roles
from DB.Actions import Actions

class Main(QObject):

    def __init__(self):
        super().__init__()
        self.central_widget = None

    def run(self):
        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Log", "log.json")
        if not os.path.exists(log_file_path):
            with open(log_file_path, "w") as log: json.dump([], log)
        Actions.import_log("Log/log.json")
        app = QApplication(sys.argv)
        app.aboutToQuit.connect(self.on_exit)
        self.window = gui_utilities.create_window(title = "Sistema de Inicio de Sesión")
        self.last_activity = datetime.now()
        self.inactivity_timer = QTimer(self.window)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.start(1000)
        app.installEventFilter(self)
        gui_utilities.switch_instance(self, self.login_menu)
        self.window.showMaximized()
        app.exec()
    
    def check_inactivity(self):
        if hasattr(self, "current_user") and self.current_user and (datetime.now() - self.last_activity).total_seconds() > 600:
            gui_utilities.create_information_message_box("Se ha cerrado la sesión por inactividad.").exec()
            self.go_back_to_login_menu()

    def eventFilter(self, obj, event):
        if event.type() in [QEvent.Type.MouseMove, QEvent.Type.KeyPress]: self.last_activity = datetime.now()
        return super().eventFilter(obj, event)
    
    def on_exit(self):
        if hasattr(self, "current_user") and self.current_user:
            Actions.add(
                Action(
                    "loged_out",
                    self.current_user,
                    gui_utilities.format_date(datetime.now()),
                    datetime.now().strftime("%H:%M:%S")
                )
            )


    def go_back_to_login_menu(self):
        self.inactivity_timer.stop()
        Actions.add(
            Action(
                "loged_out",
                self.current_user,
                gui_utilities.format_date(datetime.now()),
                datetime.now().strftime("%H:%M:%S")
            )
        )
        self.current_user = None
        gui_utilities.switch_instance(self, self.login_menu)
    
    def login_menu(self):
        width = gui_utilities.get_responsive_width(window = self.window)
        main_layout = gui_utilities.create_header(title = "Inicio de sesión")
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(10)
        fields_container = QWidget()
        main_layout.addWidget(fields_container, alignment = Qt.AlignmentFlag.AlignCenter)
        fields_container.setLayout(fields_layout)
        fields_container.setFixedWidth(width)
        username_text_box = gui_utilities.create_text_box(placeholder_text = "Nombre de usuario")
        fields_layout.addWidget(username_text_box)
        password_text_box = gui_utilities.create_text_box(placeholder_text = "Contraseña", hide_text = True)
        fields_layout.addWidget(password_text_box)
        main_layout.addStretch()
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(10)
        buttons_container = QWidget()
        main_layout.addWidget(buttons_container, alignment = Qt.AlignmentFlag.AlignCenter)
        buttons_container.setLayout(buttons_grid)
        buttons_container.setFixedWidth(width)
        login_button = gui_utilities.create_button(text = "Iniciar sesión")
        buttons_grid.addWidget(login_button, 0, 0)
        login_button.clicked.connect(lambda: self.log_in(username_text_box.text(), password_text_box.text()))
        recover_password_button = gui_utilities.create_button(text = "Recuperar contraseña")
        buttons_grid.addWidget(recover_password_button, 0, 1)
        recover_password_button.clicked.connect(self.password_recovery_menu)
        exit_button = gui_utilities.create_button(text = "Salir")
        buttons_grid.addWidget(exit_button, 1, 0, 1, 2)
        exit_button.clicked.connect(lambda: gui_utilities.confirm_exit(self.window))
        return main_layout
    
    def log_in(self, username, password):
        validations = [
            (username, "El nombre de usuario"),
            (password, "La contraseña")
        ]
        for value, field in validations:
            error = gui_utilities.validate_string(value, field)
            if error:
                gui_utilities.create_information_message_box(error).exec()
                return
        result = Accounts.log_in(username, password)
        if isinstance(result, Account):
            self.current_user = result.username
            self.last_activity = datetime.now()
            self.inactivity_timer.start(1000)
            Actions.add(
                Action(
                    "loged_in",
                    self.current_user,
                    gui_utilities.format_date(datetime.now()),
                    datetime.now().strftime("%H:%M:%S")
                )
            )
            user_role = result.user.role
            self.permissions = user_role.permissions
            gui_utilities.switch_instance(self, lambda: self.main_menu(self.permissions))
        elif result == 0: gui_utilities.create_information_message_box("La contraseña es incorrecta.").exec()
        elif result == 1: gui_utilities.create_information_message_box("El nombre de usuario es incorrecto.").exec()

    def main_menu(self, permissions):
        buttons = [
            {
                "text": "Leer",
                "font_size": 16,
                "callback": lambda: (
                    gui_utilities.create_information_message_box("Ha leído.").exec(),
                    Actions.add(
                        Action(
                            "readed",
                            self.current_user,
                            gui_utilities.format_date(datetime.now()),
                            datetime.now().strftime("%H:%M:%S")
                        )
                    )
                )
            },
            {
                "text": "Atrás",
                "font_size": 16,
                "callback": self.go_back_to_login_menu
            },
            {
                "text": "Salir",
                "font_size": 16,
                "callback": lambda: gui_utilities.confirm_exit(self.window)
            }
        ]
        if "Edición" in permissions or "Gestión total" in permissions:
            buttons.append(
                {
                    "text": "Editar",
                    "font_size": 16,
                    "callback": lambda: (
                        gui_utilities.create_information_message_box("Ha editado.").exec(),
                        Actions.add(
                            Action(
                                "edited",
                                self.current_user,
                                gui_utilities.format_date(datetime.now()),
                                datetime.now().strftime("%H:%M:%S")
                            )
                        )
                    )
                }
            )
        if "Aprobación" in permissions or "Gestión total" in permissions:
            buttons.append(
                {
                    "text": "Aprobar",
                    "font_size": 16,
                    "callback": lambda: (
                        gui_utilities.create_information_message_box("Ha aprobado.").exec(),
                        Actions.add(
                            Action(
                                "approved",
                                self.current_user,
                                gui_utilities.format_date(datetime.now()),
                                datetime.now().strftime("%H:%M:%S")
                            )
                        )
                    )
                }
            )
        if "Decisión" in permissions or "Gestión total" in permissions:
            buttons.append(
                {
                    "text": "Decidir",
                    "font_size": 16,
                    "callback": lambda: (
                        gui_utilities.create_information_message_box("Ha decidido.").exec(),
                        Actions.add(
                            Action(
                                "decided",
                                self.current_user,
                                gui_utilities.format_date(datetime.now()),
                                datetime.now().strftime("%H:%M:%S")
                            )
                        )
                    )
                }
            )
        if "Control" in permissions or "Gestión total" in permissions:
            buttons.append(
                {
                    "text": "Administrar usuarios",
                    "font_size": 16,
                    "callback": lambda: gui_utilities.switch_instance(self, self.mannage_users)
                }
            )
        if "Control" in permissions or "Gestión total" in permissions:
            buttons.append(
                {
                    "text": "Administrar roles",
                    "font_size": 16,
                    "callback": lambda: gui_utilities.switch_instance(self, self.mannage_roles)
                }
            )
        return gui_utilities.create_form(ui_instance = self, buttons = buttons, title = "Administración")
    
    def mannage_roles(self):
        buttons = [
            {
                "text": "Añadir rol",
                "font_size": 16,
                "callback": self.add_role_form
            },
            {
                "text": "Eliminar rol",
                "font_size": 16,
                "callback": self.delete_role_form
            },
            {
                "text": "Editar rol",
                "font_size": 16,
                "callback": self.edit_role_form
            },
            {
                "text": "Atrás",
                "font_size": 16,
                "callback": lambda: gui_utilities.switch_instance(self, lambda: self.main_menu(self.permissions))
            },
            {
                "text": "Salir",
                "font_size": 16,
                "callback": lambda: gui_utilities.confirm_exit(self.window)
            }
        ]
        return gui_utilities.create_form(ui_instance = self, buttons = buttons, title = "Administración de roles")

    def mannage_users(self):
        buttons = [
            {
                "text": "Añadir usuario",
                "font_size": 16,
                "callback": self.add_user_form
            },
            {
                "text": "Eliminar usuario",
                "font_size": 16,
                "callback": self.delete_user_form
            },
            {
                "text": "Editar usuario",
                "font_size": 16,
                "callback": self.edit_user_form
            },
            {
                "text": "Atrás",
                "font_size": 16,
                "callback": lambda: gui_utilities.switch_instance(self, lambda: self.main_menu(self.permissions))
            },
            {
                "text": "Salir",
                "font_size": 16,
                "callback": lambda: gui_utilities.confirm_exit(self.window)
            }
        ]
        return gui_utilities.create_form(ui_instance = self, buttons = buttons, title = "Administración de usuarios")
    
    def add_user_form(self):
        fields = [
            {"type": "text_box", "placeholder": "Nombre"},
            {"type": "text_box", "placeholder": "Nombre de usuario"},
            {"type": "text_box", "placeholder": "D.N.I."},
            {"type": "text_box", "placeholder": "Edad"},
            {"type": "text_box", "placeholder": "Número de teléfono"},
            {"type": "text_box", "placeholder": "Correo electrónico"},
            {"type": "text_box", "placeholder": "Domicilio"},
            {"type": "text_box", "placeholder": "Contraseña", "hide_text": True},
            {"type": "combo_box", "placeholder": "Rol", "items": [role.name for role in Roles.roles]}
        ]

        def on_confirm(inputs):
            name = inputs[0].text()
            username = inputs[1].text()
            id_number = inputs[2].text()
            age = inputs[3].text()
            phone_number = inputs[4].text()
            email = inputs[5].text()
            domicile = inputs[6].text()
            password = inputs[7].text()
            role = inputs[8].currentText()
            self.add_user(name, username, id_number, age, phone_number, email, domicile, password, role)

        return Utilities.create_add_form(
            title = "Añadir usuario",
            confirm_button_callback = on_confirm,
            cancel_button_callback = lambda: gui_utilities.switch_instance(self, self.mannage_users),
            content_widget = self.content_widget,
            grid_fields = fields,
            width_fraction = 1.5
        )
    
    def add_user(self, name, username, id_number, age, phone_number, email, domicile, password, role):
        validations = {
            gui_utilities.validate_string: [
                (name, "El", "nombre"),
                (username, "El", "nombre de usuario"),
                (domicile, "El", "domicilio"),
                (password, "La", "contraseña"),
                (role, "El", "rol")
            ],
            gui_utilities.validate_id: [(id_number,)],
            gui_utilities.validate_integer: [(age, "La", "edad")],
            gui_utilities.validate_cellphone_number: [(phone_number,)],
            gui_utilities.validate_email: [(email,)]
        }
        for validation, fields in validations.items():
            for field in fields:
                error = validation(*field)
                if error:
                    gui_utilities.create_information_message_box(error).exec()
                    return
        id_number = gui_utilities.format_id(id_number)
        if Users.get_user_by_id_number(id_number):
            gui_utilities.create_information_message_box("El D.N.I. que intenta registrar ya existe.").exec()
            return
        phone_number = gui_utilities.format_cellphone_number(phone_number)
        account = Account(username, password)
        role = Roles.get_role_by_name(role)
        user = User(name, id_number, age, phone_number, email, domicile, role, account)
        account.user = user
        if not Accounts.add(account):
            gui_utilities.create_information_message_box("El nombre de usuario que intenta registrar ya existe.").exec()
            return
        Users.add(user)
        Actions.add(
            Action(
                "user_added",
                self.current_user,
                gui_utilities.format_date(datetime.now()),
                datetime.now().strftime("%H:%M:%S")
            ),
            user_manipulated = user.account.username
        )
        gui_utilities.create_information_message_box(f"El usuario {username} ha sido agregado con éxito.").exec()
        self.add_user_form()

    def delete_user_form(self):
        column_headers = ["Nombre", "Nombre de usuario", "D.N.I.", "Edad", "Número telefónico", "Correo electrónico", "Domicilio", "Rol"]
        column_proportions = [0.12, 0.15, 0.09, 0.05, 0.15, 0.19, 0.15, 0.1]

        def populate(user):
            return [
                QTableWidgetItem(user.name),
                QTableWidgetItem(user.account.username),
                QTableWidgetItem(user.id_number),
                QTableWidgetItem(str(user.age)),
                QTableWidgetItem(user.phone_number),
                QTableWidgetItem(user.email),
                QTableWidgetItem(user.domicile),
                QTableWidgetItem(user.role.name)
            ]

        Utilities.create_delete_and_edit_form(
            window = self,
            title = "Eliminar Usuario",
            items_data = Users.users[::-1],
            column_headers = column_headers,
            column_proportions = column_proportions,
            row_populator_function = populate,
            action_button_text = "Eliminar",
            action_function = self.delete_user
        )
    
    def delete_user(self, users_table):
        selected_row = users_table.currentRow()
        if selected_row == -1:
            gui_utilities.create_information_message_box("Por favor, seleccione un usuario para eliminar.").exec()
            return
        user_username_item = users_table.item(selected_row, 1)
        user_username = user_username_item.text()
        user_to_delete = Users.get_user_by_username(user_username)
        if not user_to_delete:
            gui_utilities.create_information_message_box(f"No se encontró el usuario \"{user_to_delete.name}\".").exec()
            return
        result = gui_utilities.create_confirmation_message_box(f"¿Está seguro de que desea eliminar el usuario \"{user_to_delete.name}\"?").exec()
        if result == QDialog.DialogCode.Accepted:
            Actions.add(
                Action(
                    "user_deleted",
                    self.current_user,
                    gui_utilities.format_date(datetime.now()),
                    datetime.now().strftime("%H:%M:%S")
                ),
                user_manipulated = user_to_delete.account.username
            )
            Users.delete(user_to_delete)
            Accounts.delete(user_to_delete.account)
            users_table.removeRow(selected_row)

    def edit_user_form(self):
        column_headers = ["Nombre", "Nombre de usuario", "D.N.I.", "Edad", "Número telefónico", "Correo electrónico", "Domicilio", "Rol"]
        column_proportions = [0.12, 0.15, 0.09, 0.05, 0.15, 0.19, 0.15, 0.1]

        def populate(user):
            return [
                QTableWidgetItem(user.name),
                QTableWidgetItem(user.account.username),
                QTableWidgetItem(user.id_number),
                QTableWidgetItem(user.age),
                QTableWidgetItem(user.phone_number),
                QTableWidgetItem(user.email),
                QTableWidgetItem(user.domicile),
                QTableWidgetItem(user.role.name)
            ]
        
        Utilities.create_delete_and_edit_form(
            self,
            title = "Editar usuario",
            items_data = Users.users[::-1],
            column_headers = column_headers,
            column_proportions = column_proportions,
            row_populator_function = populate,
            action_button_text = "Editar",
            action_function = self.edit_user
        )

    def edit_user(self, users_table):
        selected_row = users_table.currentRow()
        if selected_row == -1:
            gui_utilities.create_information_message_box("Por favor, seleccione un usuario para editar.").exec()
            return
        user_username_item = users_table.item(selected_row, 1)
        user_username = user_username_item.text()
        user_to_edit = Users.get_user_by_username(user_username)
        if user_to_edit: self.edit_user_fields_form(user_to_edit)

    def edit_user_fields_form(self, user):
        main_layout = gui_utilities.switch_content_widget(self.content_widget)
        main_layout.addLayout(gui_utilities.create_title(text = f"Editar usuario: {user.name}", font_size = 24, background_color = "#333333"))
        main_layout.addStretch()
        fields_container = QWidget()
        main_layout.addWidget(fields_container, alignment = Qt.AlignmentFlag.AlignCenter)
        fields_container.setFixedWidth(gui_utilities.get_responsive_width(window = self.content_widget, fraction = 1.5))
        fields_grid = QGridLayout(fields_container)
        fields_grid.setSpacing(10)
        name_text_box = gui_utilities.create_text_box(placeholder_text = "Nombre")
        name_text_box.setText(user.name)
        fields_grid.addWidget(name_text_box, 0, 0)
        username_text_box = gui_utilities.create_text_box(placeholder_text = "Nombre de usuario")
        username_text_box.setText(user.account.username)
        fields_grid.addWidget(username_text_box, 0, 1)
        id_and_age_layout = QHBoxLayout()
        id_and_age_layout.setSpacing(10)
        id_number_text_box = gui_utilities.create_text_box(placeholder_text = "D.N.I.")
        id_number_text_box.setText(user.id_number)
        id_and_age_layout.addWidget(id_number_text_box, 3)
        age_text_box = gui_utilities.create_text_box(placeholder_text = "Edad")
        age_text_box.setText(user.age)
        id_and_age_layout.addWidget(age_text_box, 1)
        fields_grid.addLayout(id_and_age_layout, 1, 0)
        phone_number_text_box = gui_utilities.create_text_box(placeholder_text = "Número de teléfono")
        phone_number_text_box.setText(user.phone_number)
        fields_grid.addWidget(phone_number_text_box, 1, 1)
        email_text_box = gui_utilities.create_text_box(placeholder_text = "Correo electrónico")
        email_text_box.setText(user.email)
        fields_grid.addWidget(email_text_box, 2, 0)
        domicile_text_box = gui_utilities.create_text_box(placeholder_text = "Domicilio")
        domicile_text_box.setText(user.domicile)
        fields_grid.addWidget(domicile_text_box, 2, 1)
        password_text_box = gui_utilities.create_text_box(placeholder_text = "Contraseña", hide_text = True)
        password_text_box.setText(user.account.password)
        fields_grid.addWidget(password_text_box, 3, 0)
        role_combo_box = gui_utilities.create_combo_box(placeholder_text = "Rol", items = [role.name for role in Roles.roles])
        role_combo_box.setCurrentText(user.role.name)
        fields_grid.addWidget(role_combo_box, 3, 1)
        main_layout.addStretch()
        buttons_container = QWidget()
        main_layout.addWidget(buttons_container, alignment = Qt.AlignmentFlag.AlignCenter)
        buttons_container.setFixedWidth(gui_utilities.get_responsive_width(window = self.content_widget, fraction = 1.5))
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setSpacing(10)
        confirm_button = gui_utilities.create_button(text = "Confirmar")
        buttons_layout.addWidget(confirm_button)
        confirm_button.clicked.connect(
            lambda: self.update_user(
                user,
                name_text_box.text(),
                username_text_box.text(),
                id_number_text_box.text(),
                age_text_box.text(),
                phone_number_text_box.text(),
                email_text_box.text(),
                domicile_text_box.text(),
                password_text_box.text(),
                role_combo_box.currentText()
            )
        )
        cancel_button = gui_utilities.create_button(text = "Cancelar")
        buttons_layout.addWidget(cancel_button)
        cancel_button.clicked.connect(lambda: gui_utilities.switch_instance(self, self.mannage_users))
        return main_layout

    def update_user(self, user, new_name, new_username, new_id_number, new_age, new_phone_number, new_email, new_domicile, new_password, new_role):
        validations = {
            gui_utilities.validate_string: [
                (new_name, "El", "nombre"),
                (new_username, "El", "nombre de usuario"),
                (new_domicile, "El", "domicilio"),
                (new_password, "La", "contraseña"),
                (new_role, "El", "rol")
            ],
            gui_utilities.validate_id: [(new_id_number,)],
            gui_utilities.validate_integer: [(new_age, "La", "edad")],
            gui_utilities.validate_cellphone_number: [(new_phone_number,)],
            gui_utilities.validate_email: [(new_email,)]
        }
        for validation, fields in validations.items():
            for field in fields:
                error = validation(*field)
                if error:
                    gui_utilities.create_information_message_box(error).exec()
                    return
        new_id_number = gui_utilities.format_id(new_id_number)
        new_phone_number = gui_utilities.format_cellphone_number(new_phone_number)
        if new_id_number != user.id_number:
            if Users.get_user_by_id_number(new_id_number):
                gui_utilities.create_information_message_box("El D.N.I. que intenta registrar ya existe.").exec()
                return
        if new_username != user.account.username:
            if Users.get_user_by_username(new_username):
                gui_utilities.create_information_message_box("El nombre de usuario que intenta registrar ya existe.").exec()
                return
        user.name = new_name
        user.account.username = new_username
        user.account.password = new_password
        user.id_number = new_id_number
        user.age = new_age
        user.phone_number = new_phone_number
        user.email = new_email
        user.domicile = new_domicile
        user.role = Roles.get_role_by_name(new_role)
        Actions.add(
            Action(
                "user_edited",
                self.current_user,
                gui_utilities.format_date(datetime.now()),
                datetime.now().strftime("%H:%M:%S")
            ),
            user_manipulated = user.account.username
        )
        gui_utilities.create_information_message_box(f"El usuario \"{new_name}\" ha sido modificado con éxito.").exec()
        self.edit_user_form()
    
    def add_role_form(self):
        normal_fields = [
            {"type": "text_box", "placeholder": "Nombre"},
            {"type": "label", "text": "Permisos:", "font_weight": "bold"}
        ]
        grid_fields = [
            {"type": "check_box", "text": "Lectura"},
            {"type": "check_box", "text": "Edición"},
            {"type": "check_box", "text": "Aprobación"},
            {"type": "check_box", "text": "Desición"},
            {"type": "check_box", "text": "Control"},
            {"type": "check_box", "text": "Gestión total"}
        ]

        def on_confirm(inputs):
            name = inputs[0].text()
            permissions = [input.isChecked() for input in inputs[1:]]
            self.add_role(name, *permissions)

        _, inputs = Utilities.create_add_form(
            title = "Añadir rol",
            confirm_button_callback = on_confirm,
            cancel_button_callback = lambda: gui_utilities.switch_instance(self, self.mannage_roles),
            normal_fields = normal_fields,
            grid_fields = grid_fields,
            content_widget = self.content_widget
        )
        total_management_checkbox = inputs[-1]
        other_permissions_checkboxes = inputs[1:-1]

        def on_total_management_toggled(checked):
            for checkbox in other_permissions_checkboxes:
                checkbox.setChecked(checked)
                checkbox.setEnabled(not checked)

        total_management_checkbox.toggled.connect(on_total_management_toggled)
    
    def add_role(self, name, *permissions):
        error = gui_utilities.validate_string(name, "El", "nombre")
        if error:
            gui_utilities.create_information_message_box(error).exec()
            return
        if Roles.get_role_by_name(name):
            gui_utilities.create_information_message_box("El nombre de rol que intenta registrar ya existe.").exec()
            return
        permission_names = ["Lectura", "Edición", "Aprobación", "Desición", "Control", "Gestión total"]
        selected_permissions = [permission_names[i] for i, permission in enumerate(permissions) if permission]
        role = Role(name, selected_permissions)
        Roles.add(role)
        Actions.add(
            Action(
                "role_added",
                self.current_user,
                gui_utilities.format_date(datetime.now()),
                datetime.now().strftime("%H:%M:%S")
            ),
            role_manipulated = role.name
        )
        gui_utilities.create_information_message_box(f"El rol \"{name}\" ha sido agregado con éxito.").exec()
        self.add_role_form()

    def delete_role_form(self):
        permissions = ["Lectura", "Edición", "Aprobación", "Desición", "Control", "Gestión total"]
        column_headers = ["Rol"] + permissions
        column_proportions = [0.25] + [0.75 / len(permissions)] * len(permissions)

        def populate(role):
            items = [QTableWidgetItem(role.name)]
            has_total_management = "Gestión total" in role.permissions
            for permission in permissions:
                is_checked = has_total_management or permission in role.permissions
                items.append(QTableWidgetItem("✓" if is_checked else ""))
            return items

        Utilities.create_delete_and_edit_form(
            self,
            title = "Eliminar Rol",
            items_data = Roles.roles[::-1],
            column_headers = column_headers,
            column_proportions = column_proportions,
            row_populator_function = populate,
            action_button_text = "Eliminar",
            action_function = self.delete_role
        )
    
    def delete_role(self, roles_table):
        selected_row = roles_table.currentRow()
        if selected_row == -1:
            gui_utilities.create_information_message_box("Por favor, seleccione un rol para eliminar.").exec()
            return
        role_name_item = roles_table.item(selected_row, 0)
        role_name = role_name_item.text()
        role_to_delete = Roles.get_role_by_name(role_name)
        if not role_to_delete:
            gui_utilities.create_information_message_box(f"No se encontró el rol \"{role_name}\".").exec()
            return
        result = gui_utilities.create_confirmation_message_box(f"¿Está seguro de que desea eliminar el rol \"{role_name}\"?").exec()
        if result == QDialog.DialogCode.Accepted:
            Actions.add(
                Action(
                    "role_deleted",
                    self.current_user,
                    gui_utilities.format_date(datetime.now()),
                    datetime.now().strftime("%H:%M:%S")
                ),
                role_manipulated = role_to_delete.name
            )
            Roles.delete(role_to_delete)
            roles_table.removeRow(selected_row)

    def edit_role_form(self):
        permissions = ["Lectura", "Edición", "Aprobación", "Desición", "Control", "Gestión total"]
        column_headers = ["Rol"] + permissions
        column_proportions = [0.25] + [0.75 / len(permissions)] * len(permissions)

        def populate(role):
            items = [QTableWidgetItem(role.name)]
            has_total_management = "Gestión total" in role.permissions
            for permission in permissions:
                is_checked = has_total_management or permission in role.permissions
                items.append(QTableWidgetItem("✓" if is_checked else ""))
            return items
        
        Utilities.create_delete_and_edit_form(
            window = self,
            title = "Editar rol",
            items_data = Roles.roles[::-1],
            column_headers = column_headers,
            column_proportions = column_proportions,
            row_populator_function = populate,
            action_button_text = "Editar",
            action_function = self.edit_role
        )
    
    def edit_role(self, roles_table):
        selected_row = roles_table.currentRow()
        if selected_row == -1:
            gui_utilities.create_information_message_box("Por favor, seleccione un rol para editar.").exec()
            return
        role_name_item = roles_table.item(selected_row, 0)
        role_name = role_name_item.text()
        role_to_edit = Roles.get_role_by_name(role_name)
        if role_to_edit: self.edit_role_fields_form(role_to_edit)
    
    def edit_role_fields_form(self, role):
        main_layout = gui_utilities.switch_content_widget(self.content_widget)
        main_layout.addLayout(gui_utilities.create_title(text = f"Editar rol: {role.name}", font_size = 24, background_color = "#333333"))
        main_layout.addStretch()
        fields_container = QWidget()
        main_layout.addWidget(fields_container, alignment = Qt.AlignmentFlag.AlignCenter)
        fields_container.setFixedWidth(gui_utilities.get_responsive_width(window = self.content_widget))
        fields_layout = QVBoxLayout(fields_container)
        main_layout.addLayout(fields_layout)
        fields_layout.setSpacing(10)
        name_text_box = gui_utilities.create_text_box(placeholder_text = "Nombre")
        name_text_box.setText(role.name)
        fields_layout.addWidget(name_text_box)
        permissions_label = gui_utilities.create_label(text = "Permisos:", font_weight = "bold", background_color = "#333333")
        fields_layout.addWidget(permissions_label)
        permissions_grid = QGridLayout()
        fields_layout.addLayout(permissions_grid)
        permissions_grid.setSpacing(0)
        permissions_grid.setContentsMargins(15, 0, 0, 0)
        read_permission_check_box = gui_utilities.create_checkbox(text = "Lectura", background_color = "#333333")
        read_permission_check_box.setChecked("Lectura" in role.permissions)
        permissions_grid.addWidget(read_permission_check_box, 0, 0)
        edit_permission_check_box = gui_utilities.create_checkbox(text = "Edición", background_color = "#333333")
        edit_permission_check_box.setChecked("Edición" in role.permissions)
        permissions_grid.addWidget(edit_permission_check_box, 0, 1)
        approval_permission_check_box = gui_utilities.create_checkbox(text = "Aprobación", background_color = "#333333")
        approval_permission_check_box.setChecked("Aprobación" in role.permissions)
        permissions_grid.addWidget(approval_permission_check_box, 1, 0)
        decision_permission_check_box = gui_utilities.create_checkbox(text = "Desición", background_color = "#333333")
        decision_permission_check_box.setChecked("Desición" in role.permissions)
        permissions_grid.addWidget(decision_permission_check_box, 1, 1)
        control_permission_check_box = gui_utilities.create_checkbox(text = "Control", background_color = "#333333")
        control_permission_check_box.setChecked("Control" in role.permissions)
        permissions_grid.addWidget(control_permission_check_box, 2, 0)
        total_mannagement_permission_check_box = gui_utilities.create_checkbox(text = "Gestión total", background_color = "#333333")
        total_mannagement_permission_check_box.setChecked("Gestión total" in role.permissions)
        permissions_grid.addWidget(total_mannagement_permission_check_box, 2, 1)
        other_permissions = [
            read_permission_check_box,
            edit_permission_check_box,
            approval_permission_check_box,
            decision_permission_check_box,
            control_permission_check_box
        ]

        def on_total_management_toggled(checked):
            for check_box in other_permissions:
                check_box.setChecked(checked)
                check_box.setEnabled(not checked)

        total_mannagement_permission_check_box.toggled.connect(on_total_management_toggled)
        if total_mannagement_permission_check_box.isChecked():
            for check_box in other_permissions:
                check_box.setChecked(True)
                check_box.setEnabled(False)
        main_layout.addStretch()
        buttons_container = QWidget()
        main_layout.addWidget(buttons_container, alignment = Qt.AlignmentFlag.AlignCenter)
        buttons_container.setFixedWidth(gui_utilities.get_responsive_width(window = self.content_widget))
        buttons_layout = QHBoxLayout()
        buttons_container.setLayout(buttons_layout)
        buttons_layout.setSpacing(10)
        confirm_button = gui_utilities.create_button(text = "Confirmar")
        buttons_layout.addWidget(confirm_button)
        confirm_button.clicked.connect(
            lambda: self.update_role(
                role,
                name_text_box.text(),
                read_permission_check_box.isChecked(),
                edit_permission_check_box.isChecked(),
                approval_permission_check_box.isChecked(),
                decision_permission_check_box.isChecked(),
                control_permission_check_box.isChecked(),
                total_mannagement_permission_check_box.isChecked()
            )
        )
        cancel_button = gui_utilities.create_button(text = "Cancelar")
        buttons_layout.addWidget(cancel_button)
        cancel_button.clicked.connect(lambda: gui_utilities.switch_instance(self, self.mannage_roles))
        return main_layout

    def update_role(self, original_role, new_name, read, edit, approval, decision, control, total_management):
        error = gui_utilities.validate_string(new_name, "El", "nombre")
        if error:
            gui_utilities.create_information_message_box(error).exec()
            return
        if new_name != original_role.name and Roles.get_role_by_name(new_name):
            gui_utilities.create_information_message_box("El nombre de rol que intenta registrar ya existe.").exec()
            return
        permissions = []
        if read: permissions.append("Lectura")
        if edit: permissions.append("Edición")
        if approval: permissions.append("Aprobación")
        if decision: permissions.append("Desición")
        if control: permissions.append("Control")
        if total_management: permissions.append("Gestión total")
        original_role.name = new_name
        original_role.permissions = permissions
        Actions.add(
            Action(
                "role_edited",
                self.current_user,
                gui_utilities.format_date(datetime.now()),
                datetime.now().strftime("%H:%M:%S")
            ),
            role_manipulated = original_role.name
        )
        gui_utilities.create_information_message_box(f"El rol \"{new_name}\" ha sido modificado con éxito.").exec()
        self.edit_role_form()

    def password_recovery_menu(self):
        width = gui_utilities.get_responsive_width(window = self.window)
        main_layout = gui_utilities.create_header(title = "Recuperar contraseña")
        fields_layout = QVBoxLayout()
        fields_layout.setSpacing(10)
        fields_container = QWidget()
        main_layout.addWidget(fields_container, alignment = Qt.AlignmentFlag.AlignCenter)
        fields_container.setLayout(fields_layout)
        fields_container.setFixedWidth(width)
        username_text_box = gui_utilities.create_text_box(placeholder_text = "Nombre de usuario")
        fields_layout.addWidget(username_text_box)
        main_layout.addStretch()
        buttons_grid = QGridLayout()
        buttons_grid.setSpacing(10)
        buttons_container = QWidget()
        main_layout.addWidget(buttons_container, alignment = Qt.AlignmentFlag.AlignCenter)
        buttons_container.setLayout(buttons_grid)
        buttons_container.setFixedWidth(width)
        recover_button = gui_utilities.create_button(text = "Recuperar")
        buttons_grid.addWidget(recover_button, 0, 0, 1, 2)
        recover_button.clicked.connect(lambda: self.recover_password(username_text_box.text()))
        back_button = gui_utilities.create_button(text = "Atrás")
        buttons_grid.addWidget(back_button, 1, 0)
        back_button.clicked.connect(lambda: gui_utilities.switch_instance(self, self.login_menu))
        exit_button = gui_utilities.create_button(text = "Salir")
        buttons_grid.addWidget(exit_button, 1, 1)
        exit_button.clicked.connect(lambda: gui_utilities.confirm_exit(self.window))
        gui_utilities.switch_instance(self, lambda: main_layout)

    def recover_password(self, username):
        error = gui_utilities.validate_string(username, "El", "nombre de usuario")
        if error:
            gui_utilities.create_information_message_box(error).exec()
            return
        user = Users.get_user_by_username(username)
        if not user:
            gui_utilities.create_information_message_box("El nombre de usuario es incorrecto.").exec()
            return
        gui_utilities.create_information_message_box(f"Se ha enviado un correo de recuperación a {user.email}.").exec()

if __name__ == "__main__": Main().run()