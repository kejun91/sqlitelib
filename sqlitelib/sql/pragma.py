from sqlitelib.database.db import DB


def table_info(s):
    return DB(s.__databasename__).execute_select_query(f'PRAGMA table_info({s.__tablename__})')
