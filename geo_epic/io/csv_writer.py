import fcntl
import os

class CSVWriter:
    def __init__(self, file_path, mode='a'):
        """Initialize the CSV class with a file path and file mode.
        
        Args:
            file_path (str): The full path to the CSV file.
            mode (str): The mode to open the file ('w' for writing, 'a' for appending).
        """
        self.file_path = file_path
        self.mode = mode
        self.file_handle = None

    def open(self, mode=None):
        """Open the CSV file in the specified mode and lock it for exclusive access.
        
        Args:
            mode (str): Optionally specify a mode ('w' for writing, 'a' for appending) at opening.
        """
        if mode:
            self.mode = mode
        self.file_handle = open(self.file_path, self.mode)
        fcntl.flock(self.file_handle, fcntl.LOCK_EX)  # Lock the file

    def write_row(self, *args):
        """Write a row to the CSV file with arbitrary number of columns.
        
        Args:
            *args: Variable length argument list representing the columns of the row.
        """
        if self.file_handle is not None:
            self.file_handle.write(', '.join(str(arg) for arg in args) + '\n')
        else:
            raise Exception("File is not open. Please call the 'open' method first.")

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


# # Example usage:
# file_path = '/path/to/yourfile.csv'
# with CSV(file_path, 'w') as csv_writer:
#     csv_writer.write_row('Column1', 'Column2', 'Column3')
#     csv_writer.write_row('Data1', 'Data2', 'Data3')
