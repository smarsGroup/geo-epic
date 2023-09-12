import os
import yaml
import argparse
import pandas as pd
import subprocess
import geopandas as gpd
from misc import ConfigParser
from misc.utils import calc_centroids#, find_column
from ssurgo import get_soil_ids

parser = argparse.ArgumentParser(description="ConfigParser CLI")
parser.add_argument("-c", "--config", required=True, help="Path to the configuration file")
args = parser.parse_args()

curr_dir = os.getcwd()

config = ConfigParser(curr_dir, args.config)

env = os.environ.copy()
root_path = os.path.dirname(os.path.dirname(__file__))
env["PYTHONPATH"] = root_path + ":" + env.get("PYTHONPATH", "")

print("\nPreparing data for", config["EXPName"])

print("\nProcessing fields of interest")
info_df = gpd.read_file(config["Fields_of_Interest"])

columns = set(info_df.columns)
ID_names = set(['OBJECTID', 'FieldID', 'FIELDID', 'OBID', 'RUNID', 'RunID'])
IDs = ID_names & columns
ID = next(iter(IDs), None)
if ID is None:
    raise Exception("FieldID column not Found")
info_df['FieldID'] = info_df[ID]
info_df.drop(list(IDs), axis=1, inplace=True)

rot_names = set(['RotID', 'rotID'])
rots = rot_names & columns
rot = next(iter(rots), None)
if rot is None:
    raise Exception("RotID column not Found")
info_df['opc'] = info_df[rot].apply(lambda x: f'{config["opc_prefix"]}_{int(x)}')

info_df = info_df.to_crs(epsg = 4326)
lon_min, lat_min, lon_max, lat_max = info_df.total_bounds

# Read from config file
soil = config["soil"]
weather = config["weather"]
region_code = config["code"]

# Download Nldas data 
if not os.path.exists(weather["dir"] + '/NLDAS_csv'):
    start_date = weather["start_date"]
    end_date = weather["end_date"]
    command = f'python3 {root_path}/weather/nldas_ws.py -s {start_date} -e {end_date} \
                  -w {weather["dir"]} -b {lat_min} {lat_max} {lon_min} {lon_max}'
    message = subprocess.Popen(command, shell=True, env=env)

# create soil files 
if soil['files_dir'] is None:
    command = f'python3 {root_path}/ssurgo/processing.py -r {region_code} -gdb {soil["gdb_path"]}'
    message = subprocess.Popen(command, shell=True, env=env).wait()

#Prepare Info for Run
info_df = calc_centroids(info_df)
info_df.drop(['geometry', 'centroid'], axis=1, inplace=True)

coords = info_df[['x', 'y']].values
soil_dir = os.path.dirname(soil["gdb_path"])
invalid = soil_dir + '/invalid_mukeys.csv'
site = config["site"]
ssurgo_map = site["ssurgo_map"]
info_df['ssu'] = get_soil_ids(coords, ssurgo_map, invalid) 
info_df.to_csv(curr_dir + '/info.csv', index = False)

# create site files
command = f'python3 {root_path}/sit/generate.py -o {site["dir"]} -i {curr_dir + "/info.csv"}\
    -ele {site["elevation"]} -slope {site["slope_us"]} -sl {site["slope_len"]}'
message = subprocess.Popen(command, shell=True, env=env).wait()

config.update_config({
    'soil': {
        'files_dir': f'{soil_dir}/files'
    },
    'Processed_Info': f'{curr_dir}/info.csv'
})