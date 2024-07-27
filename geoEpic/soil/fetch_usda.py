from utils import write_soil_file
import pandas as pd
from sda import SoilDataAccess


mukey = 642029
soil_properties_df = SoilDataAccess.fetch_properties(mukey)
print(soil_properties_df)
soil_properties_df.to_csv('soil.csv', index = False)

write_soil_file(soil_properties_df, './')

import requests
import json
import pandas as pd
import argparse
import numpy as np
import geopandas as gpd
from tqdm import tqdm
import os
import rasterio
import xarray as xr
import rioxarray as rio
# from ..misc.utils import parallel_executor
# from ..misc.raster_utils import raster_to_dataframe

# def save_data_as_csv(data, lat, lon, output_dir='./data'):
#     if data:
#         df = data
#         file_name = f"ssurgo_data_lat_{lat}_lon_{lon}.csv"
#         file_path = f"{output_dir}/{file_name}"
#         os.makedirs(output_dir, exist_ok=True)
#         df.to_csv(file_path, index=False)

# def process_row(row):
#     ssurgo_data, lat, lon = download_ssurgo_data(row)
#     save_data_as_csv(ssurgo_data, lat, lon)

import argparse
import os
import sys

def fetch_data(input_data, output_path):
    """
    Fetches weather data based on the input type which could be coordinates, a CSV file, or a shapefile.

    Args:
        config_file (str): Path to the configuration YAML file.
        input_data (str): Could be latitude and longitude as a string, path to a CSV file, or path to a shapefile.
        output_path (str): Directory or file path where the output should be saved.
    """
    if input_data.endswith('.csv'):
        # Handle fetching based on CSV file
        print(f"Fetching weather data for locations in CSV file: {input_data}")
        # Implementation would go here
    elif input_data.endswith('.shp'):
        # Handle fetching based on shapefile
        print(f"Fetching weather data for area in shape file: {input_data}")
    
    # Example print to simulate output file path
    print(f"Data will be saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Fetch and output data from USDA SSURGO")
    parser.add_argument('--fetch', metavar='INPUT', nargs='+', help='Latitude and longitude as two floats, or a file path')
    parser.add_argument('--out', default='./', dest='output_path', help='Output directory or file path for the fetched data')

    args = parser.parse_args()

    if len(args.fetch) == 2:
        latitude, longitude = map(float, args.fetch)
        wkt = f'point({latitude}, {longitude})'
        df = SoilDataAccess.fetch_properties(wkt)
    else:
        fetch_data(args.fetch[0], args.output_path)


if __name__ == '__main__':
    main()
