class User():
    def __init__(self, name, id_number, age, phone_number, email, domicile, role = None, account = None):
        self.name = name
        self.id_number = id_number
        self.age = age
        self.phone_number = phone_number
        self.email = email
        self.domicile = domicile
        self.role = role
        self.account = account