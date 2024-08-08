from contextlib import contextmanager
import re
import sqlite3

def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None

def get_sqlite_connection(database_path):
    conn = sqlite3.connect(database_path)
    conn.create_function("REGEXP", 2, regexp)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    return conn

@contextmanager
def sqlite_connection(database_path):
    connection = get_sqlite_connection(database_path)
    try:
        yield connection
    finally:
        connection.close()