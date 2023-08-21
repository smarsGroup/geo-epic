import os
import sys
EPICLib = os.environ.get('EPICLib')
sys.path.insert(0, EPICLib)

import json
import pandas as pd
import geopandas as gpd
from weather import download_nldas
from misc.utils import calc_centroids
from ssurgo import get_soil_ids, process_gdb
from sit import generate_site_files

# Load the JSON data from a file
with open('config.json') as config_file:
    config = json.load(config_file)

curr_dir = os.getcwd()

print("Preparing data for ", config["EXPName"])

print("Processing fields of interest")
info_df = gpd.read_file(config["Fields_of_Interest"])
info_df = info_df.to_crs(epsg = 4326)
lon_min, lat_min, lon_max, lat_max = info_df.total_bounds

# Use values from the config dictionary
weather_dir = config["weather"]["dir"]

# Download Nldas data 
if not os.path.exists(weather_dir + '/NLDAS_csv'):
    start_date = config["weather"]["start_date"]
    end_date = config["weather"]["end_date"]
    weather_dir = weather_dir.replace('./', curr_dir + '/')
    download_nldas(start_date, end_date, lat_min, lat_max, lon_min, lon_max, weather_dir)

# create soil files 
if config['soil']['files_dir'] is None:
    region_code = config["code"]
    gdb_path = config["soil"]["gdb_path"]
    gdb_path = gdb_path.replace('./', curr_dir + '/')
    process_gdb(region_code, gdb_path)

info_df = calc_centroids(info_df)
info_df.drop(['geometry', 'centroid'], axis=1, inplace=True)

info_df['FieldID'] = info_df['OBJECTID']
info_df['opc'] = info_df['rotID'].apply(lambda x: f'CropRot_{int(x)}')
coords = info_df[['x', 'y']].values
info_df['ssu'] = get_soil_ids(coords) 
info_df.to_csv('info.csv', index=False)

#create site files
site_dir = config["site_dir"].replace('./', curr_dir + '/')
generate_site_files(curr_dir + '/info.csv', site_dir)