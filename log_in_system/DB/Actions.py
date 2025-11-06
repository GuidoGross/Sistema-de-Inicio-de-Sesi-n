import json
import os

class Actions():

    log = []

    @classmethod
    def add(cls, action, user_manipulated = None, role_manipulated = None):
        action_performed = f"{action.date} - {action.time}: El usuario \"{action.user}\" ha "
        match action.type:
            case "loged_in":
                action_performed += "iniciado sesión."
            case "loged_out":
                action_performed += "cerrado sesión."
            case "readed":
                action_performed += "leído."
            case "edited":
                action_performed += "editado."
            case "approved":
                action_performed += "aprobado."
            case "decided":
                action_performed += "decidido."
            case "user_added":
                action_performed += f"agregado el usuario \"{user_manipulated}\"."
            case "user_deleted":
                action_performed += f"eliminado el usuario \"{user_manipulated}\"."
            case "user_edited":
                action_performed += f"editado el usuario \"{user_manipulated}\"."
            case "role_added":
                action_performed += f"agregado el rol \"{role_manipulated}\"."
            case "role_deleted":
                action_performed += f"eliminado el rol \"{role_manipulated}\"."
            case "role_edited":
                action_performed += f"editado el rol \"{role_manipulated}\"."
        cls.log.append(action_performed)
        cls.export_log("Log/log.json")
    
    @classmethod
    def import_log(cls, file_path):
        if os.path.exists(file_path):
            with open(file_path, "r", encoding = "utf-8") as log:
                try: cls.log = json.load(log)
                except json.JSONDecodeError: cls.log = []
        else: cls.log = []

    @classmethod
    def export_log(cls, file_path):
        with open(file_path, "w", encoding = "utf-8") as log: json.dump(cls.log, log, indent = 4, ensure_ascii = False)