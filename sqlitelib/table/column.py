from enum import Enum

from sqlitelib.table.column_enum import ID


class Column:
    def __init__(self, *column_attributes):
        self.attributes = column_attributes

    
class DataType(Enum):
    TEXT = 'TEXT'
    NUMERIC = 'NUMERIC'
    INTEGER = 'INTEGER'
    REAL = 'REAL'
    BLOB = 'BLOB'
    JSON = 'JSON'
    DATETIME = 'DATETIME'

class Constraint(Enum):
    PRIMARY_KEY = 'PRIMARY KEY'
    NOT_NULL = 'NOT NULL'
    UNIQUE = 'UNIQUE'
    AUTOINCREMENT = 'AUTOINCREMENT'

class ForeignKey:
    def __init__(self, model, column_name = None):
        self.model = model
        self.column_name = column_name or ID

class Index:
    def __init__(self, index_name):
        self.index_name = index_name

class Default:
    def __init__(self, value):
        self.value = value