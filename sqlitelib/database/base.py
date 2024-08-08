from abc import ABC, abstractmethod
import os

from sqlitelib.database.connection import sqlite_connection


class AbstractDB(ABC):
    def __init__(self, database_path, database_name):
        if database_path is None:
            raise ValueError('Database path cannot be None')
        
        if database_name is None:
            raise ValueError('Database name cannot be None')
        
        if not os.path.exists(database_path):
            os.makedirs(database_path)
        
        self.database_path = os.path.join(database_path, database_name + '.db')
    
    @abstractmethod
    def execute_select_query(self, select_query_string, parameters = ()):
        pass

    @abstractmethod
    def execute_query(self, query, parameters = ()):
        pass

    @abstractmethod
    def execute_batch_modify_query(self, modify_query, parameters):
        pass

    def is_table_existed(self, table_name):
        with sqlite_connection(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            result = cursor.fetchone()
            return True if result else False