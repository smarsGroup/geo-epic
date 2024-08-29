import os
import pandas as pd
from .csv_writer import CSVWriter


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
        filename = os.path.join(self.output_folder, f"{func_name}.csv")
        if func_name not in self.dataframes:
            if os.path.isfile(filename):
                self.dataframes[func_name] = pd.read_csv(filename)
            else:
                raise FileNotFoundError(f"No data found for name: {func_name}")
        df = self.dataframes[func_name]
        if self.delete_after_use:
            del self.dataframes[func_name]
            os.remove(filename)
        return df

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
        filename = os.path.join(self.output_folder, f"{func_name}.csv")
        with CSVWriter(filename) as writer:
            writer.write_row(**result)
