import sqlite3


class DatabaseConnection:
    def __init__(self, host):
        self.connection = None
        self.host = host

    def __enter__(self):
        self.connection = sqlite3.connect(self.host)
        cursor = self.connection.cursor()
        return cursor

    def __exit__(self, _, __ ,___):
        self.connection.commit()
        self.connection.close()
