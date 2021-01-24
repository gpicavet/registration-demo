from datetime import datetime
from main.database import DatabaseConnection


class UserRepository():

    def __init__(self):
        pass

    def account_get(self, email):
        cursor = DatabaseConnection.get().cursor()
        cursor.execute(
            "select id,email,password,status,activation_key,registred_date from account where email=%s", (email,))
        return cursor.fetchone()

    def account_activate(self, email):
        cursor = DatabaseConnection.get().cursor()
        cursor.execute(
            "update account set status='A' where email=%s", (email,))

    def account_add(self, email, password, status, activation_key):
        cursor = DatabaseConnection.get().cursor()
        cursor.execute("insert into account(email,password,status,activation_key,registred_date) values(%s, %s, %s, %s, %s)",
                       (email, password, status, activation_key, datetime.now(),))

    def account_set_activation_key(self, email, activation_key):
        cursor = DatabaseConnection.get().cursor()
        cursor.execute("update account set activation_key=%s ,registred_date =now() where email=%s",
                       (activation_key, email,))
