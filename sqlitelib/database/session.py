import sqlite3

from sqlitelib.database.base import AbstractDB
from sqlitelib.database.connection import get_sqlite_connection


class Session(AbstractDB):
    def begin(self):
        self.connection = get_sqlite_connection(self.database_path)

    def execute_select_query(self, select_query_string, parameters = ()):
        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()
        cursor.execute(select_query_string, parameters)
        return [dict(row) for row in cursor.fetchall()]
        
    def execute_query(self, query, parameters = ()):
        cursor = self.connection.cursor()
        cursor.execute(query, parameters)
        
    def execute_batch_modify_query(self, modify_query, parameters):
        cursor = self.connection.cursor()
        cursor.executemany(modify_query, parameters)

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()