from Core.User import User
from Core.Account import Account
from DB.Roles import Roles
from DB.Accounts import Accounts

class Users:
    users = [
        User(
            name = "Administrador",
            id_number = "46.301.436",
            age = "20",
            phone_number = "3754-439480",
            email = "grossguidoivan@gmail.com",
            domicile = "Sede central",
            role = Roles.get_role_by_name("Administrador"),
            account = Account(username = "Administrador", password = "Administrador")
        )
    ]
    users[0].account.user = users[0]
    Accounts.accounts.append(users[0].account)

    @classmethod
    def add(cls, user):
        cls.users.append(user)

    @classmethod
    def delete(cls, user):
        cls.users.remove(user)

    @classmethod
    def get_user_by_id_number(cls, id_number):
        for user in cls.users:
            if user.id_number == id_number:
                return user
        return None