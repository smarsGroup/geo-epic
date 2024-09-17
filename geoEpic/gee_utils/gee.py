import argparse
import os
import sys
from core import *

def fetch_data(config_file, location, output_path):
    collection = CompositeCollection(config_file)
    df = collection.extract([location])
    df.to_csv(f'{output_path}', index = False)

def main():
    parser = argparse.ArgumentParser(description="Fetch and output data from GEE")
    parser.add_argument('config_file', help='Path to the configuration file')
    parser.add_argument('--fetch', metavar='INPUT', nargs='+', help='Latitude and longitude as two floats, or a file path')
    parser.add_argument('--out', default='./', dest='output_path', help='Output directory or file path for the fetched data')
    
    args = parser.parse_args()
    
    try:
        if len(args.fetch) == 2:
            latitude, longitude = map(float, args.fetch)
            fetch_data(args.config_file, [latitude, longitude], args.output_path)
            print(f'Data saved in {args.output_path}')
            
        else:
            fetch_list(args.config_file, args.fetch[0], args.output_path)
    except:
        parser.print_help()


if __name__ == '__main__':
    main()