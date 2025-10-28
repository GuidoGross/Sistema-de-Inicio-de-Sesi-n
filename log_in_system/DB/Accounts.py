class Accounts():
    accounts = []

    @classmethod
    def add(cls, account):
        if not account.username in [account.username for account in cls.accounts]:
            cls.accounts.append(account)
            return True
        else: return False
    
    @classmethod
    def delete(cls, account):
        cls.accounts.remove(account)
    
    @classmethod
    def log_in(cls, username, password):
        for account in cls.accounts:
            if account.username == username:
                if account.password == password: return account
                else: return 0
        return 1