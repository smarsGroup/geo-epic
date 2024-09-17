import argparse
import os
import sys
from core import *

from time import time
def download_data(config_file, location):
    start = time()

    collection = CompositeCollection(config_file)
    collection.download([location])

    end = time()
    print(f'time taken : {end - start}')
    
def download_list(config_file, input_data):
    """
    Fetches soil data based on the input type which could be coordinates, a CSV file, or a shapefile.

    Args:
        input_data (str): Could be latitude and longitude as a string, path to a CSV file, or path to a shapefile.
        output_dir (str): Directory or file path where the output should be saved.
        raw (bool): Whether to save the results as raw CSV or .SOL file.
    """
    def download_data_wrapper(location):
        collection = CompositeCollection(config_file)
        df = collection.extract([location])
        df.to_csv(f'{output_path}', index = False)
        
    if input_data.endswith('.csv'):
        locations = pd.read_csv(input_data)
        parallel_executor(download_data, locations['location'])
    elif input_data.endswith('.shp'):
        shapefile = gpd.read_file(input_data)
        shapefile['centroid'] = shapefile.geometry.centroid
        locations = shapefile['centroid'].apply(lambda x: f'point({x.x} {x.y})')
        parallel_executor(download_data, locations, output_dir, raw)
        
def main():
    parser = argparse.ArgumentParser(description="Fetch and output data from GEE")
    parser.add_argument('config_file', help='Path to the configuration file')
    parser.add_argument('--fetch', metavar='INPUT', nargs='+', help='Latitude and longitude as two floats, or a file path')
    
    args = parser.parse_args()
    
    # try:
    if len(args.fetch) == 2:
        latitude, longitude = map(float, args.fetch)
        download_data(args.config_file, [latitude, longitude], args.output_path)
        print(f'Data saved in {args.output_path}')
        
    else:
        download_data(args.config_file, args.fetch[0], args.output_path)


if __name__ == '__main__':
    main()