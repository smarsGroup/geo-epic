import csv
import os
import warnings
import pandas as pd
from functools import wraps
from geoEpic.io import DLY, CSVWriter
from geoEpic.misc import ConfigParser, parallel_executor
from geoEpic.model_class import EPICModel

class Workspace:
    def __init__(self, config_path):
        self.config = ConfigParser(config_path)
        self.base_dir = self.config.dir
        self.functions = []
        self.fitness_function = None
        self.dataframes = {}
        self.delete_after_use = True
        self.model = EPICModel.from_config(config_path)

        if self.config["num_of_workers"] > os.cpu_count():
            warning_msg = (f"Workers greater than number of CPU cores ({os.cpu_count()}).")
            warnings.warn(warning_msg, RuntimeWarning)

    def post_process(self, func):
        @wraps(func)
        def wrapper(run_id):
            result = func(run_id)
            self._save_to_csv(func.__name__, run_id, result)
            return result

        self.functions.append(wrapper)
        return wrapper

    def fitness(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.fitness_defined = True
            return func(*args, **kwargs)

        self.fitness_function = wrapper
        return wrapper

    def get_data(self, func_name):
        if func_name not in self.dataframes:
            filename = f"{func_name}.csv"
            if os.path.isfile(filename):
                self.dataframes[func_name] = pd.read_csv(filename)
            else:
                raise FileNotFoundError(f"No data found for function: {func_name}")
        
        df = self.dataframes[func_name]

        if self.delete_after_use:
            del self.dataframes[func_name]
            os.remove(f"{func_name}.csv")

        return df

    def _save_to_csv(self, func_name, run_id, result):
        filename = f"{func_name}.csv"
        file_exists = os.path.isfile(filename)

        if not isinstance(result, dict):
            raise ValueError(f"Function {func_name} must return a dictionary.")

        with CSVWriter(filename) as writer:
            if not file_exists:
                writer.write_row('run_id', *result.keys())
            writer.write_row(run_id, *result.values())

    def run_function(self, run_id):
        for func in self.functions:
            func(run_id)

    def run(self):
        # Run all the post-process functions in parallel
        parallel_executor(self.run_function, range(101), method='Process', 
                          max_workers = self.max_workers, timeout = self.timeout)
        if self.fitness_function is not None:
            return self.fitness_function()




# # Example usage:
# workspace = Workspace()

# @workspace.post_process
# def example_function(run_id):
#     return {
#         'variable_a': run_id * 2,
#         'variable_b': run_id + 10
#     }

# @workspace.fitness
# def example_fitness():
#     df = workspace.get_data('example_function')
#     print(df)
#     mean_a = df['variable_a'].mean()
#     return mean_a

# workspace.run(delete_after_use=True, max_workers=4, timeout=5)
import ee

# Initialize the Earth Engine module.
ee.Initialize()

def get_elevation_slope(lat, lon):
    # Define the point of interest.
    point = ee.Geometry.Point(lon, lat)
    
    # Load the SRTM dataset.
    srtm = ee.Image("USGS/SRTMGL1_003")
    
    # Get the elevation at the point.
    elevation = srtm.select('elevation').reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=point,
        scale=30  # Set scale to 30 meters for more precise elevation data
    ).get('elevation').getInfo()
    
    # Calculate the slope.
    slope = ee.Terrain.slope(srtm).select('slope').reduceRegion(
        reducer=ee.Reducer.first(),
        geometry=point,
        scale=30  # Matching scale for slope calculation
    ).get('slope').getInfo()
    
    return elevation, slope

# Example usage: Get elevation and slope for a specific location
latitude, longitude = 34.052, -118.2437  # Coordinates for Los Angeles, CA
elevation, slope = get_elevation_slope(latitude, longitude)
print("Elevation (m):", elevation)
print("Slope (degrees):", slope)
