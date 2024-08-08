from collections import defaultdict
from decimal import Decimal
import json
import math
import threading
from typing import List, Union
from sqlitelib.database.common import get_max_variable_number
from sqlitelib.database.session import Session
from sqlitelib.table.column_enum import ID
from sqlitelib.table.model import SqliteDynamicModel, SqliteModel
from sqlitelib.utils.common import split_list_into_batches
from sqlitelib.utils.encoding import CustomEncoder

lock = threading.Lock()

def insert(records:Union[List[SqliteModel],SqliteModel], replace = False):
    t, records = validate_records(records)

    if len(records) == 0:
        return
    
    columns_records_dict = categorize_by_columns(records)

    if any(ID in key for key in columns_records_dict):
        raise Exception(f'{ID} should not be included in insert call.')
    
    with lock:
        s = Session(t.__databasename__)
        s.begin()

        if issubclass(t, SqliteDynamicModel):
            _add_non_existed_columns(s, t, frozenset().union(*columns_records_dict.keys()))

        for k,v in columns_records_dict.items():
            columns = list(k)
            batch_size = math.floor(get_max_variable_number()/len(columns))

            for batch in list(split_list_into_batches(v,batch_size)):
                _insert(s, t.__tablename__, columns, batch, replace)

        last_record_id = s.execute_select_query('SELECT last_insert_rowid()')[0].get('last_insert_rowid()')

        s.commit()
        s.close()

    return last_record_id

def insert_or_replace(records:Union[List[SqliteModel],SqliteModel]):
    return insert(records, True)

def upsert(records:Union[List[SqliteModel],SqliteModel], unique_column = None):
    unique_column = unique_column or ID
    t, records = validate_records(records)

    if len(records) == 0:
        return

    with lock:
        s = Session(t.__databasename__)
        s.begin()

        for r in records:
            r_dict = vars(r)
            columns = list(r_dict.keys())
            if unique_column not in columns:
                raise Exception(f"{unique_column} is not specified in the upsert call")
            
            results = s.execute_select_query(f'SELECT {ID} FROM {t.__tablename__} WHERE {unique_column} = ?', (getattr(r,unique_column),))
            if len(results) > 0:
                r_dict[ID] = results[0].get(ID)
                _update(s, t.__tablename__, columns, r_dict)
            else:
                _insert(s, t.__tablename__, columns, [r])

        s.commit()
        s.close()

def update(record_or_records:Union[List[SqliteModel],SqliteModel]):
    t, records = validate_records(record_or_records)

    if len(records) == 0:
        return

    with lock:
        s = Session(t.__databasename__)
        s.begin()

        if issubclass(t, SqliteDynamicModel):
            _add_non_existed_columns(s, t, {key for r in records for key in vars(r)})

        for r in records:
            r_dict = vars(r)
            fields = r_dict.keys()
            
            _update(s, t.__tablename__, fields, r_dict)
        
        s.commit()
        s.close()

def delete(record_or_records):
    t, records = validate_records(record_or_records)

    if len(records) == 0:
        return

    with lock:
        s = Session(t.__databasename__)
        s.begin()

        for r in records:
            _delete(s, t.__tablename__, r)

        s.commit()
        s.close()

def _insert(session, table_name, columns, records, replace = False):
    dml_query = f'INSERT {"OR REPLACE " if replace else ""}INTO {table_name} ({",".join(columns)}) VALUES {",".join(["(" + ",".join(["?" for _ in range(len(columns))]) + ")"]*len(records))}'
    insert_data = [tuple(get_column_value(r,key) for key in columns) for r in records]
    insert_data_params = [item for sublist in insert_data for item in sublist]
    session.execute_query(dml_query, insert_data_params)

def _update(session:Session, table_name, columns, record_dict):
    set_clause = f"{','.join([key + ' = ?' for key in columns if key != ID])}"
    where_clause = f"{ID} = ?"
    update_query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

    values = [convert_value(record_dict[key]) for key in columns if key != ID]
    values.append(record_dict[ID])

    session.execute_query(update_query, values)

def _delete(session, table_name, record):
    delete_query = f"DELETE FROM {table_name} WHERE {ID} = ?"
    session.execute_query(delete_query, (getattr(record,ID),))

def validate_records(record_or_records):
    ror = record_or_records

    model = None
    records = []

    if isinstance(ror, SqliteModel):
        model = type(ror)
        records = [ror]
    elif isinstance(ror, list) and len(ror) > 0 and isinstance(ror[0], SqliteModel):
        model = type(ror[0])
        if all(isinstance(r, model) for r in ror):
            records = ror
    
    return model, records

def convert_unsupported_values(data):
    for k,v in data.items():
        data[k] = convert_value(v)

def get_not_existed_columns(model, data_attributes):
    exist_columns = set(model.get_db_column_names())
    
    result_set = data_attributes - exist_columns
    if result_set:
         return list(result_set)
    else:
         return []

def convert_value(v):
    if isinstance(v, bool):
        return str(v)
    elif isinstance(v, (list,dict)):
        return json.dumps(v, cls=CustomEncoder)
    elif isinstance(v, int):
        return json.dumps(v, cls=CustomEncoder)
    elif isinstance(v, Decimal):
        return str(v)
    else:
        return v
    
def get_column_value(row, column):
    v = getattr(row,column)
    return convert_value(v)

def _add_non_existed_columns(session, model, columns):
    for nec in get_not_existed_columns(model, set(columns)):
        session.execute_query(f'ALTER TABLE {model.__tablename__} ADD COLUMN {nec} TEXT')

def categorize_by_columns(records):
    column_records_dict = defaultdict(list)
    for r in records:
        keys = frozenset(vars(r).keys())
        column_records_dict[keys].append(r)
    return column_records_dict