import numpy as np
import pandas as pd
from ruamel.yaml import YAML
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import Polygon, MultiPolygon

import ee
from initialize import ee_Initialize

ee_Initialize()


def extract_features(collection, aoi, date_range, resolution):
        
    def map_function(image):
        # Function to reduce image region and extract data
        date = image.date().format()
        reducer = ee.Reducer.mode() if aoi.getInfo()['type'] != "Point" else ee.Reducer.first()
        reduction = image.reduceRegion(reducer=reducer, geometry=aoi, scale=resolution, maxPixels=1e9)
        return ee.Feature(None, reduction).set('Date', date)

    filtered_collection = collection.filterBounds(aoi)
    filtered_collection = filtered_collection.filterDate(*date_range)
    daily_data = filtered_collection.map(map_function)
    df = ee.data.computeFeatures({
            'expression': daily_data,
            'fileFormat': 'PANDAS_DATAFRAME'
        })
    
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    return df

class CompositeCollection:
    """
    A class to handle composite collection of Earth Engine data.

    This class initializes collections of Earth Engine based on a provided
    YAML configuration file, applies specified formulas and selections, and allows
    for the extraction of temporal data for a given Area of Interest (AOI).

    Methods:
        extract(aoi_coords):
            Extracts temporal data for a given AOI and returns it as a pandas DataFrame.
    """

    def __init__(self, yaml_file):
        # Initialize the CompositeCollection object
        self.global_scope = None
        with open(yaml_file, 'r') as file:
            self.config = YAML().load(file)
        self.global_scope = self.config.get('global_scope')
        self.collections_config = self.config.get('collections')
        self.collections = {}
        self.vars = {}
        self.args = []
        self.resolution = self.global_scope['resolution']
        self._initialize_collections()

    def _initialize_collections(self):
        # Initialize collections based on the configuration
        for name, config in self.collections_config.items():
            if 'time_range' in config.keys():
                start, end = config['time_range']
            else:
                start, end = self.global_scope['time_range']

            collection = ee.ImageCollection(config['collection'])
            if 'linkcollection' in config.keys():
                # Handle linked collections if specified in the configuration
                link_settings = config['linkcollection']
                collection2 = ee.ImageCollection(link_settings['collection'])
                collection = collection.linkCollection(collection2, link_settings['bands'])

            collection = collection.filterDate(start, end)
            
            if 'select' in config.keys():
                # Apply selection mask to the collection if specified
                mask_exp = config['select']
                def mask_util(image):
                    mask = image.expression(mask_exp)
                    return image.updateMask(mask)
                collection = collection.map(lambda image: mask_util(image))
                
            variables = config['variables']
            vars = []
            for var, formula in variables.items():
                # Apply formulas to the collection to compute variables
                def apply_formula(image):
                    try:
                        var_image = image.expression(formula).rename(var).set('system:time_start', image.get('system:time_start'))
                        return image.addBands(var_image).toFloat()
                    except Exception as e:
                        print(f"Error processing image {image.id()}: {e}")
                        return image

                collection = collection.map(apply_formula)
                vars.append(var)
            
            self.collections[name] = collection.select(vars)
            self.vars[name] = vars
            self.args.append((name, self.collections[name], (start, end)))
    
    def extract(self, aoi_coords):
        """
        Extracts temporal data for a given Area of Interest (AOI).

        Args:
            aoi_coords (tuple/list): Coordinates representing the AOI, either as a Point or as vertices of a Polygon.

        Returns:
            pd.DataFrame: A pandas DataFrame containing the extracted data.
        """
        # Convert coordinates to AOI geometry
        if isinstance(aoi_coords, (Polygon, MultiPolygon)):
            aoi_coords = aoi_coords.exterior.coords[:]
        if len(aoi_coords) == 1:
            aoi = ee.Geometry.Point(aoi_coords[0])
        else:
            aoi = ee.Geometry.Polygon(aoi_coords)
        
        def extract_features_wrapper(args):
            name, collection, date_range = args
            return extract_features(collection, aoi, date_range, self.resolution)
        # Use ThreadPoolExecutor to parallelize the extraction process
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(extract_features_wrapper, self.args))

        # Merge the results into a single DataFrame
        df_merged = results[0]
        for df in results[1:]:
            df_merged = pd.merge(df_merged, df, on='Date', how='outer')
            columns = df_merged.columns
            # Iterate over columns to find and calculate the mean for columns with suffixes
            for col in set(col.rsplit('_', 1)[0] for col in columns if '_' in col):
                if f"{col}_x" in columns and f"{col}_y" in columns:
                    df_merged[col] = df_merged[[f"{col}_x", f"{col}_y"]].mean(axis=1)
                    df_merged.drop(columns=[f"{col}_x", f"{col}_y"], inplace=True)
        
        df_merged = df_merged.groupby('Date').mean().reset_index()
        df_merged.sort_values(by='Date', inplace=True)

        try:
            # Apply derived variables formulas if specified in the configuration
            derived = self.config.get('derived_variables')
            for var_name, formula in derived.items():
                df_merged[var_name] = self._safe_eval(formula, df_merged)
        except Exception as e:
            print(e)
        
        # Filter and clean the DataFrame based on the global scope variables
        df_merged = df_merged[['Date'] + self.global_scope['variables']].copy()
        df_merged.dropna(inplace=True)
        df_merged = df_merged.reset_index(drop=True)
        numerical_cols = df_merged.select_dtypes(include=['number']).columns
        df_merged[numerical_cols] = df_merged[numerical_cols].astype(float).round(3)

        return df_merged
    

    def _safe_eval(self, expression, df):
        """
        Safely evaluate a mathematical expression using only functions from the math and numpy libraries.

        Args:
            expression (str): The expression to evaluate.
            df (pd.DataFrame): The DataFrame containing the data to evaluate against.

        Returns:
            pd.Series: The result of the evaluated expression.
        """
        safe_dict = np.__dict__
        safe_dict.update(df.to_dict(orient='series'))
        return eval(expression, {"__builtins__": None}, safe_dict)



if __name__ == '__main__':
    # yaml_file = 'weather_config.yml'
    # composite_collection = CompositeCollection(yaml_file)

    # from time import time
    # start = time()

    # parallel_executor(composite_collection.extract, [[[-98.114, 41.855]]]*10, method = 'Thread', return_value=True, max_workers=40)

    # end = time()
    # print(end - start)
    
    col = CompositeCollection('./landsat_lai.yml')
    df = col.extract([[-98.114, 41.855]])
    print(df)