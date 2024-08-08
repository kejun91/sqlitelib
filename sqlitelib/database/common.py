import sqlite3


def get_max_variable_number():
    return 32766 if sqlite3.sqlite_version > "3.32.0" else 999