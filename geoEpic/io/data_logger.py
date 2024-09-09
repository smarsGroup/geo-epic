import fcntl
import os
import csv
import pandas as pd
import sqlite3
import time
import random


class CSVWriter:
    def __init__(self, file_path, mode='a+'):
        """Initialize the CSV class with a file path and file mode.
        
        Args:
            file_path (str): The full path to the CSV file.
            mode (str): The mode to open the file ('w' for writing, 'a' for appending).
        """
        self.file_path = file_path
        self.mode = mode
        self.file_handle = None
        self.writer = None
        self.headers_written = False

    def open(self, mode=None):
        """Open the CSV file in the specified mode and lock it for exclusive access.
        
        Args:
            mode (str): Optionally specify a mode ('w' for writing, 'a' for appending) at opening.
        """
        if mode: self.mode = mode
        # if not os.path.exists(self.file_path):
        #     if 'a' in self.mode: open(self.file_path, 'w+').close()
        self.file_handle = open(self.file_path, self.mode)
        self.writer = csv.writer(self.file_handle)
        fcntl.flock(self.file_handle, fcntl.LOCK_EX)  # Lock the file
        # Check if we need to write headers by checking if the file is empty
        if os.stat(self.file_path).st_size == 0:
            self.headers_written = False
        else:
            self._read_header()
    
    def _read_header(self):
        """Read the header from the file if it exists."""
        if self.file_handle:
            self.file_handle.seek(0)  # Go to the start of the file
            first_line = self.file_handle.readline()
            if first_line:
                self.header = first_line.strip().split(',')
                self.headers_written = True

    def write_row(self, *args, **kwargs):
        """Write a row to the CSV file.
        
        Args can be a variable length argument list representing the columns of the row,
        or kwargs can be a dict with column names and values.
        """
        if self.file_handle is None:
            raise Exception("File is not open. Please call the 'open' method first.")

        if kwargs:
            if not self.headers_written:
                # Write the header based on dictionary keys
                self.header = list(kwargs.keys())
                self.writer.writerow(self.header)
                self.headers_written = True
            # Write the row based on dictionary values
            self.writer.writerow([kwargs[key] for key in self.header])
        else:
            # Assume args contains only values in the correct order
            self.writer.writerow(args)

    def close(self):
        """Release the lock and close the CSV file."""
        if self.file_handle is not None:
            fcntl.flock(self.file_handle, fcntl.LOCK_UN)  # Unlock the file
            self.file_handle.close()
            self.file_handle = None

    def __enter__(self):
        """Support context manager 'with' statement by opening the file."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Support context manager 'with' statement by closing the file."""
        self.close()



class SQLTableWriter:

    TYPE_MAPPING = {
        int: "INTEGER",
        float: "REAL",
        str: "TEXT",
        bool: "INTEGER",  # SQLite doesn't have a native boolean type
        bytes: "BLOB",
        None: "NULL"
    }
        
    def __init__(self, table_path, columns=None, max_retries=5, initial_wait=0.05):
        self.db_path = table_path
        self.table_name = os.path.basename(table_path).split('.')[0]
        self.columns = columns
        self.conn = None
        self.cursor = None
        self.initialized = False
        self.max_retries = max_retries
        self.initial_wait = initial_wait

    def open(self):
        self._execute_with_retry(self._open_connection)

    def _open_connection(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        if self.columns:
            columns_stmt = ', '.join([f"{col_name} {col_type}" for col_name, col_type in self.columns.items()])
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} ({columns_stmt})")
            self.conn.commit()
            self.initialized = True
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        self.cursor.execute("PRAGMA synchronous = NORMAL;")
        self.cursor.execute("PRAGMA temp_store = MEMORY;")
        self.cursor.execute("PRAGMA cache_size = -64000;")

    def write_row(self, **kwargs):
        if self.conn is None or self.cursor is None:
            raise Exception("Database is not open. Please call the 'open' method first.")
        
        self._execute_with_retry(self._write_row, kwargs)
    
    def get_sqlite_type(self, value):
        return self.TYPE_MAPPING.get(type(value), "BLOB")

    def _write_row(self, kwargs):
        if not self.initialized:
            # Infer column types from the given arguments
            columns_with_types = [f"{col} {self.get_sqlite_type(value)}" for col, value in kwargs.items()]
            columns_stmt = ', '.join(columns_with_types)
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} ({columns_stmt})")
            self.initialized = True

        columns = ', '.join(kwargs.keys())
        placeholders = ':' + ', :'.join(kwargs.keys())
        self.cursor.execute(f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})", kwargs)
        self.conn.commit()

    def query_rows(self, condition=None, *args, **kwargs):
        return self._execute_with_retry(self._query_rows, condition, *args, **kwargs)

    def _query_rows(self, condition, *args, **kwargs):
        query = f"SELECT * FROM {self.table_name}"
        if condition:
            query += f" WHERE {condition}"
        self.cursor.execute(query, *args, **kwargs)
        rows = self.cursor.fetchall()
        # Get column names from cursor.description
        columns = [description[0] for description in self.cursor.description]
        return pd.DataFrame(rows, columns=columns)

    def delete_table(self):
        if self.conn is None or self.cursor is None:
            raise Exception("Database is not open. Please call the 'open' method first.")
        self._execute_with_retry(self._delete_table)

    def _delete_table(self):
        self.cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _execute_with_retry(self, func, *args, **kwargs):
        retries = 0
        while retries < self.max_retries:
            try:
                return func(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    wait_time = self.initial_wait * (2 ** retries) + random.uniform(0, 0.01)
                    print(f"Database is locked. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    raise
        raise Exception(f"Failed to execute after {self.max_retries} retries due to database lock")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class DataLogger:
    """
    A class to handle logging of data to CSV files. It supports logging dictionaries
    and retrieving logged data.

    Attributes:
        output_folder (str): Directory where CSV files are stored.
        delete_after_use (bool): Whether to delete the file after retrieving it.
        dataframes (dict): Cache for dataframes loaded from CSV files.
    """

    def __init__(self, output_folder, delete_after_use=True):
        """
        Initialize the DataLogger with a specified output folder.

        Args:
            output_folder (str): Directory to store the CSV files.
            delete_after_use (bool): Flag to indicate if the file should be deleted after use.
        """
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        self.dataframes = {}
        self.delete_after_use = delete_after_use

    def get(self, func_name):
        """
        Retrieve a DataFrame from a CSV file.

        Args:
            func_name (str): The name of the function whose data needs to be retrieved.

        Returns:
            pandas.DataFrame: The DataFrame containing the logged data.

        Raises:
            FileNotFoundError: If the corresponding CSV file does not exist.
        """
        filename = os.path.join(self.output_folder, f"{func_name}.db")
        # if func_name not in self.dataframes:
        if os.path.isfile(filename):
            with SQLTableWriter(filename) as writer:
                df = writer.query_rows()
            if self.delete_after_use:
                os.remove(filename)
            return df
        else:
            raise FileNotFoundError(f"No data found for name: {func_name}")
        

    def log_dict(self, func_name, result):
        """
        Log a dictionary of results to a CSV file.

        Args:
            func_name (str): The name of the function to log the data for.
            result (dict): Dictionary of results to log.

        Raises:
            ValueError: If the result is not a dictionary.
        """
        if not isinstance(result, dict):
            raise ValueError(f"{func_name} output must be a dictionary.")
        filename = os.path.join(self.output_folder, f"{func_name}.db")
        with SQLTableWriter(filename) as writer:
            writer.write_row(**result)
