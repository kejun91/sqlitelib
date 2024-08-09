# sqlitelib

`sqlitelib` is a Python library that provides an easy-to-use interface for common SQLite database operations. It simplifies database interactions, making it easier to perform tasks like creating tables, inserting records, querying data, and more.

## Features

- Connect to SQLite databases
- Create tables
- Insert, update, and delete records
- Query data with flexible options
- Simple and intuitive API

## Installation

You can install `sqlitelib` using pip:

```bash
pip install sqlitelib
```

## Usage
```python
from sqlitelib import SqliteModel, Column, Constraint, DataType

class ExportJob(SqliteModel):
    __databasepath__ = 'path/to/db.db'
    __tablename__ = 'export_job'

    job_type = Column(DataType.TEXT, Constraint.NOT_NULL)
    status = Column(DataType.TEXT, Constraint.NOT_NULL)
    completed_date = Column(DataType.INTEGER)
    export_parameters_json = Column(DataType.TEXT)
    description = Column(DataType.TEXT)
    directory_path = Column(DataType.TEXT)
```
