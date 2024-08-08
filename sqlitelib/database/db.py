import sqlite3

from sqlitelib.database.base import AbstractDB
from sqlitelib.database.connection import sqlite_connection


class DB(AbstractDB):
    def execute_and_fetchall(self, query, parameters = ()):
        with sqlite_connection(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            return cursor.fetchall()
        
    def execute_select_query(self, select_query_string, parameters = ()):
        return [dict(row) for row in self.execute_and_fetchall(select_query_string, parameters)]
        
    def execute_query(self, query, parameters = ()):
        with sqlite_connection(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, parameters)
            conn.commit()
        
    def execute_batch_modify_query(self, modify_query, parameters):
        with sqlite_connection(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.executemany(modify_query, parameters)
            conn.commit()