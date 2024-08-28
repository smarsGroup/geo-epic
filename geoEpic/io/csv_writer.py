import fcntl
import os
import csv

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
