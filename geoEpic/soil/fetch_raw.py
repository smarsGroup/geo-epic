import os
import argparse
from geoEpic.utils import parallel_executor
import geopandas as gpd
import pandas as pd
from sda import SoilDataAccess

def fetch_data(field):
    data_dict = SoilDataAccess.fetch_value(field['WKT'],field['table'],field['value'])
    return data_dict

def fetch_raw(input_data):
    """
    Fetches soil data based on the input type which could be coordinates, a CSV file, or a shapefile.

    Args:
        input_data (str): Could be latitude and longitude as a string, path to a CSV file, or path to a shapefile.
        output_dir (str): Directory or file path where the output should be saved.
        raw (bool): Whether to save the results as raw CSV or .SOL file.
    """
    if input_data.endswith('.csv'):
        locations = pd.read_csv(input_data)
        locations['WKT'] = shapefile['geometry'].apply(lambda geom: geom.wkt)
        point_strings = [f"point({row.latitude} {row.longitude})" for _, row in locations.iterrows()]
        parallel_executor(fetch_data, point_strings,return_value=True)
    elif input_data.endswith('.shp'):
        shapefile = gpd.read_file(input_data)
        shapefile['WKT'] = shapefile['geometry'].apply(lambda geom: geom.wkt)
        parallel_executor(fetch_data, shapefile, output_dir, raw)
        
def validate_request(intput_file, out_file):
    if not out_file.endswith('.csv') and not out_file.endswith('.shp'):
        print('Only shape and csv files are supported')
        return False
    if not out_file.endswith('.csv'):
        print('The ouput file should be of csv type')
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Fetch and output data from USDA SSURGO")
    parser.add_argument('--input', metavar='INPUT', nargs='+', help='Latitude and longitude as two floats, or a file path')
    parser.add_argument('--table', metavar='INPUT', nargs='+', help='Latitude and longitude as two floats, or a file path')
    parser.add_argument('--value', metavar='INPUT', nargs='+', help='Latitude and longitude as two floats, or a file path')
    parser.add_argument('--out', default='./', dest='output_path', help='Output directory or file path for the fetched data')

    args = parser.parse_args()
    
    fetch_raw(args.fetch[0], args.output_path, args.raw)

if __name__ == '__main__':
    main()