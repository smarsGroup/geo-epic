import argparse
import os
import sys
from core import *

# def fetch_list(config_file, location, output_path):
#     """
#     Fetches weather data based on the input type which could be coordinates, a CSV file, or a shapefile.

#     Args:
#         config_file (str): Path to the configuration YAML file.
#         input_data (str): Could be latitude and longitude as a string, path to a CSV file, or path to a shapefile.
#         output_path (str): Directory or file path where the output should be saved.
#     """
#     if input_data.endswith('.csv'):
#         # Handle fetching based on CSV file
#         print(f"Fetching weather data for locations in CSV file: {input_data}")
#         # Implementation would go here
#     elif input_data.endswith('.shp'):
#         # Handle fetching based on shapefile
#         print(f"Fetching weather data for area in shape file: {input_data}")
#         # Implementation would go here
#     else:
#         # Assuming the input is lat lon coordinates
#         latitude, longitude = map(float, input_data.split())
#         print(f"Fetching weather data for coordinates: Latitude {latitude}, Longitude {longitude}")
#         # Implementation would go here
    
#     # Example print to simulate output file path
#     print(f"Data will be saved to: {output_path}")

from time import time
def fetch_data(config_file, location, output_path):
    start = time()

    collection = CompositeCollection(config_file)
    print(len(collection.args))
    df = collection.extract([location])
    df.to_csv(f'{output_path}', index = False)

    end = time()
    print(end - start)
    
def fetch_list(config_file, input_data, output_dir, raw):
    """
    Fetches soil data based on the input type which could be coordinates, a CSV file, or a shapefile.

    Args:
        input_data (str): Could be latitude and longitude as a string, path to a CSV file, or path to a shapefile.
        output_dir (str): Directory or file path where the output should be saved.
        raw (bool): Whether to save the results as raw CSV or .SOL file.
    """
    def fetch_data_wrapper(location):
        collection = CompositeCollection(config_file)
        df = collection.extract([location])
        df.to_csv(f'{output_path}', index = False)
        
    if input_data.endswith('.csv'):
        locations = pd.read_csv(input_data)
        parallel_executor(fetch_data, locations['location'], output_dir, raw)
    elif input_data.endswith('.shp'):
        shapefile = gpd.read_file(input_data)
        shapefile['centroid'] = shapefile.geometry.centroid
        locations = shapefile['centroid'].apply(lambda x: f'point({x.x} {x.y})')
        parallel_executor(fetch_data, locations, output_dir, raw)
        
def main():
    parser = argparse.ArgumentParser(description="Fetch and output data from GEE")
    parser.add_argument('config_file', help='Path to the configuration file')
    parser.add_argument('--fetch', metavar='INPUT', nargs='+', help='Latitude and longitude as two floats, or a file path')
    parser.add_argument('--out', default='./', dest='output_path', help='Output directory or file path for the fetched data')
    
    args = parser.parse_args()
    
    # try:
    if len(args.fetch) == 2:
        latitude, longitude = map(float, args.fetch)
        fetch_data(args.config_file, [latitude, longitude], args.output_path)
        print(f'Data saved in {args.output_path}')
        
    else:
        fetch_list(args.config_file, args.fetch[0], args.output_path)
    # except:
    #     parser.print_help()


if __name__ == '__main__':
    main()