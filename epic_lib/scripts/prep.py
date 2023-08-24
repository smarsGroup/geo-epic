import os
import yaml
import pandas as pd
import geopandas as gpd
from misc import ConfigParser
from misc.utils import calc_centroids
from ssurgo import get_soil_ids


config = ConfigParser()
curr_dir = os.getcwd()

print("Preparing data for ", config["EXPName"])
print("\nProcessing fields of interest")
info_df = gpd.read_file(config["Fields_of_Interest"])
info_df = info_df.to_crs(epsg = 4326)
lon_min, lat_min, lon_max, lat_max = info_df.total_bounds

# Use values from the config dictionary
weather_dir = config["weather"]["dir"]

# Download Nldas data 
if not os.path.exists(weather_dir + '/NLDAS_csv'):
    start_date = config["weather"]["start_date"]
    end_date = config["weather"]["end_date"]
    download_nldas(start_date, end_date, lat_min, lat_max, lon_min, lon_max, weather_dir)

# create soil files 
if config['soil']['files_dir'] is None:
    region_code = config["code"]
    gdb_path = config["soil"]["gdb_path"]
    process_gdb(region_code, gdb_path)

info_df = calc_centroids(info_df)
info_df.drop(['geometry', 'centroid'], axis=1, inplace=True)

info_df['FieldID'] = info_df['OBJECTID']
info_df['opc'] = info_df['rotID'].apply(lambda x: f'CropRot_{int(x)}')

coords = info_df[['x', 'y']].values
info_df['ssu'] = get_soil_ids(coords) 
info_df.to_csv('info.csv', index = False)

# #create site files
site_dir = config["site_dir"]
generate_site_files(curr_dir + '/MD_info.csv', site_dir)