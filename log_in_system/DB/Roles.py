from Core.Role import Role

class Roles:
    
    roles = [
        Role("Personal", ["Lectura"]),
        Role("Jefe de área", ["Lectura", "Edición"]),
        Role("Gerente", ["Lectura", "Edición", "Aprobación"]),
        Role("Director", ["Lectura", "Edición", "Aprobación", "Desición"]),
        Role("Supervisor", ["Lectura", "Control"]),
        Role("Administrador", ["Gestión total"])
    ]

    @classmethod
    def add(cls, role):
        cls.roles.append(role)
    
    @classmethod
    def delete(cls, role):
        cls.roles.remove(role)
    
    @classmethod
    def get_role_by_name(cls, name):
        for role in cls.roles:
            if role.name == name: return role
        return None