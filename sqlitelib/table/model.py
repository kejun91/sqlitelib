from abc import ABC, ABCMeta
import json
import random
import string

from sqlitelib.database.db import DB
from sqlitelib.sql.pragma import table_info
from sqlitelib.table.column import Column, Constraint, DataType, Default, ForeignKey, Index
from sqlitelib.table.column_enum import ID, LAST_MODIFIED_DATE, SystemColumn

class SqliteModelMeta(ABCMeta):
    def __init__(cls, name, bases, dct):
        if cls.__databasename__ is not None and cls.__tablename__ is not None:
            if not cls.is_table_existed():
                cls.initialize_table()
            else:
                cls.add_new_columns()

    def __str__(cls):
        return cls.__tablename__

class SqliteModel(ABC, metaclass=SqliteModelMeta):
    __databasename__ = 'default'
    __tablename__ = None

    sqlitelib__id = Column(DataType.INTEGER, Constraint.PRIMARY_KEY, Constraint.AUTOINCREMENT)
    sqlitelib__created_date = Column(DataType.INTEGER, Default('CURRENT_TIMESTAMP'))
    sqlitelib__last_modified_date = Column(DataType.INTEGER, Default('CURRENT_TIMESTAMP'))

    def __init__(self, attribute_dict = {}):
        for key, value in attribute_dict.items():
            setattr(self, key, value)

    @classmethod
    def select_all(cls):
        query = f"SELECT * FROM {cls.__tablename__}"
        return DB(cls.__databasename__).execute_select_query(query)
    
    @classmethod
    def select_by_id(cls,id):
        query = f"SELECT * FROM {cls.__tablename__} WHERE {ID} = ?"
        return DB(cls.__databasename__).execute_select_query(query, (id,))[0]
    
    @classmethod
    def select_from_query(cls, query, parameters = ()):
        result = DB(cls.__databasename__).execute_select_query(query, parameters)

        for r in result:
            for k,v in r.items():
                column_attributes = getattr(cls,k,Column()).attributes
                if column_attributes and DataType.JSON in column_attributes and v is not None and isinstance(v, str):
                    r[k] = json.loads(v)
        
        return result
    
    @classmethod
    def execute_from_query(cls, query, parameters = ()):
        return DB(cls.__databasename__).execute_query(query, parameters)
    
    @classmethod
    def get_db_column_names(cls) -> list:
        return [column[1] for column in DB(cls.__databasename__).execute_and_fetchall(f'PRAGMA table_info({cls.__tablename__})')]
    
    @classmethod
    def get_model_columns(cls, custom = False) -> dict:
        columns = {}
        for m in list(reversed(cls.mro())):
            for k,v in vars(m).items():
                if type(v) == Column:
                    if custom:
                        if k not in SystemColumn.list():
                            columns.update({k:v})
                    else:
                        columns.update({k:v})
        
        return columns

    @classmethod
    def get_model_custom_column_names(cls) -> list:
        return list(cls.get_model_columns(True).keys())
    
    @classmethod
    def is_table_existed(cls) -> bool:
        result = DB(cls.__databasename__).execute_select_query(f'SELECT name From sqlite_master where type = "table" and name = "{cls.__tablename__}"')
        return len(result) > 0
    
    @classmethod
    def add_new_columns(cls):
        new_columns = {k:v for k,v in cls.get_model_columns().items() if k not in [tc.get('name') for tc in table_info(cls)]}
        if len(new_columns) == 0:
            return

        column_defs = []
        foreign_keys_defs = []
        index_queries = []
        
        for nc in new_columns:
            cd, fkd, iq = get_column_def_info(cls.__tablename__, nc, new_columns.get(nc))
            column_defs.extend(cd)
            foreign_keys_defs.extend(fkd)
            index_queries.extend(iq)

        add_column_queries = [f"ALTER TABLE {cls.__tablename__} ADD COLUMN {cd}" for cd in column_defs]
        add_constraint_queries = [f"ALTER TABLE {cls.__tablename__} ADD CONSTRAINT {cls.__tablename__ + '_' + ''.join(random.choices(string.ascii_lowercase) for _ in range(3))} {fkd}" for fkd in foreign_keys_defs]
        for q in (add_column_queries + add_constraint_queries + index_queries):
            DB(cls.__databasename__).execute_query(q)

    @classmethod
    def initialize_table(cls):
        database_name = cls.__databasename__
        table_name = cls.__tablename__

        column_defs = []
        foreign_keys_defs = []
        index_queries = []

        columns = cls.get_model_columns()

        for k in columns:
            cd, fkd, iq = get_column_def_info(table_name, k, columns.get(k))
            column_defs.extend(cd)
            foreign_keys_defs.extend(fkd)
            index_queries.extend(iq)

        create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({','.join(column_defs + foreign_keys_defs)})"

        last_modified_date_fill_trigger = f'''
        CREATE TRIGGER IF NOT EXISTS set_last_modified_date
        AFTER UPDATE ON {table_name} FOR EACH ROW
        BEGIN
            UPDATE {table_name}
                SET {LAST_MODIFIED_DATE} = CURRENT_TIMESTAMP
                WHERE {ID} = OLD.{ID};
        END;
        '''

        for q in ([create_table_query] + index_queries + [last_modified_date_fill_trigger]):
            DB(database_name).execute_query(q)

class SqliteDynamicModel(SqliteModel):
    pass

def get_column_def_info(table_name:str, column_name:str, c:Column):
    foreign_keys_defs = []
    index_queries = []
    column_defs = []
    data_type = None
    constraints = []
    for a in c.attributes:
        if type(a) == DataType:
            if a == DataType.JSON:
                data_type = DataType.TEXT.value
            else:
                data_type = a.value
        elif type(a) == Constraint:
            constraints.append(a.value)
        elif type(a) == ForeignKey:
            foreign_keys_defs.append(f"FOREIGN KEY ({column_name}) REFERENCES {a.model.__tablename__}({a.column_name}) ON DELETE SET NULL")
        elif type(a) == Index:
            index_queries.append(f"CREATE INDEX IF NOT EXISTS {a.index_name} ON {table_name}({column_name})")
        elif type(a) == Default:
            constraints.append(f"DEFAULT {a.value}")
            
    column_defs.append(f"{column_name} {data_type} {' '.join(constraints)}")
    return column_defs, foreign_keys_defs, index_queries

def create_model_class(base_class:SqliteModel, database_name):
    return type(base_class.__name__, (base_class,), {"__databasename__":database_name})