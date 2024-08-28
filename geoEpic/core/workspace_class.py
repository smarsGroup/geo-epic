import csv
import os
import warnings
import pandas as pd
from functools import wraps
from geoEpic.io import DLY, CSVWriter
from geoEpic.misc import ConfigParser, parallel_executor
from .model_class import EPICModel
from .site_class import Site
import geopandas as gpd
from shapely.geometry import shape
from pyproj import Proj, transform
from glob import glob
from geoEpic.misc.utils import filter_dataframe

class DataLogger:
    def __init__(self, output_folder, delete_after_use=True):
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
        self.dataframes = {}
        self.delete_after_use = delete_after_use

    def get(self, func_name):
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
        if not isinstance(result, dict):
            raise ValueError(f"{func_name} output must be a dictionary.")
        filename = os.path.join(self.output_folder, f"{func_name}.csv")
        with CSVWriter(filename) as writer:
            writer.write_row(**result)


class Workspace:
    def __init__(self, config_path):
        config = ConfigParser(config_path)
        self.config = config.config_data
        self.base_dir = config.dir
        self.routines = {}
        self.fitness_function = None
        self.dataframes = {}
        self.delete_after_use = True
        self.model = EPICModel.from_config(config_path)
        self.process_run_info(self.config['run_info'])
        self.data_logger = DataLogger(os.path.join(self.base_dir, f"__cache__"))

        if self.config["num_of_workers"] > os.cpu_count():
            warning_msg = (f"Workers greater than number of CPU cores ({os.cpu_count()}).")
            warnings.warn(warning_msg, RuntimeWarning)
    
    def process_run_info(self, file_path):
        # Check the file type
        if file_path.lower().endswith('.csv'):
            data = pd.read_csv(file_path)
            required_columns_csv = {'siteid', 'soil', 'opc', 'dly', 'lat', 'lon'}
            if not required_columns_csv.issubset(set(data.columns.str.lower())):
                raise ValueError("CSV file missing one or more required columns: 'SiteID', 'soil', 'opc', 'dly', 'lat', 'lon'")
        elif file_path.lower().endswith('.shp'):
            data = gpd.read_file(file_path)
            data = data.to_crs(epsg=4326)  # Convert to latitude and longitude projection
            data['lat'] = data.geometry.centroid.y
            data['lon'] = data.geometry.centroid.x
            required_columns_shp = {'siteid', 'soil', 'opc', 'dly'}
            if not required_columns_shp.issubset(set(data.columns.str.lower())):
                raise ValueError("Shapefile missing one or more required attributes: 'SiteID', 'soil', 'opc', 'dly'")
            data.drop(columns=['geometry'], inplace=True)
        else:
            raise ValueError("Unsupported file format. Please provide a '.csv' or '.shp' file.")
        
        #check for opc files.
        opc_files = glob(f'{self.config["opc_dir"]}/*.OPC')
        present = [os.path.basename(f).split('.')[0] for f in opc_files]

        # Filter data to include only rows where 'opc' value has a corresponding .OPC file
        initial_count = len(data)
        data = data.loc[data['opc'].astype(str).isin(present)]
        final_count = len(data)

        # Check if the count of valid opc files is less than the initial count of data entries
        if final_count < initial_count:
            missing_count = initial_count - final_count
            warning_msg = f"Warning: {missing_count} sites will not run due to missing .OPC files."
            warnings.warn(warning_msg, RuntimeWarning)
        self.run_info = data
    
    def select(self, select_str = None):
        if select_str is None: 
            select_str = self.config["select"]
        info = filter_dataframe(self.run_info, select_str)
        info_ls = info.to_dict('records')
        return info_ls

    def post_process(self, func):
        @wraps(func)
        def wrapper(site):
            result = func(site)
            if not isinstance(result, dict):
                raise ValueError(f"{func.__name__} must return a dictionary.")
            self.data_logger.log_dict(func.__name__, {'SiteID': site.site_id, **result})
            return result

        self.routines[func.__name__] = wrapper
        return wrapper

    def fitness(self, func):
        @wraps(func)
        def wrapper(): return func()
        self.fitness_function = wrapper
        return wrapper
    
    def get_data(self, func):
        return self.data_logger.get(func)

    def run_function(self, site_info):
        site = Site.from_config(self.config, site_info)
        self.model.run(site)
        for func in self.routines.values():
            func(site)
        if len(self.routines) > 0 and self.delete_after_use:
            for outs in site.outputs.values():
                os.remove(outs)

    def run(self):
        info_ls = self.select()
        parallel_executor(self.run_function, info_ls, method='Process', 
                          max_workers = self.config["num_of_workers"], timeout = self.config["timeout"])
        if self.fitness_function is not None:
            return self.fitness_function()
        else: 
            return None




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

