import os
import argparse
import shutil
import subprocess
from geoEpic.weather import DailyWeather
import numpy as np
import pandas as pd
from geoEpic.misc import ConfigParser, parallel_executor
from geoEpic.misc.sys_utils import *
from glob import glob
# import importlib.util
# import sys

# Fetch the base directory
parser = argparse.ArgumentParser(description="EPIC workspace")
parser.add_argument("-c", "--config", default= "./config.yml", help="Path to the configuration file")
parser.add_argument("-b", "--progress_bar", default = 'True', help = "Display Progress Bar")
args = parser.parse_args()

# print(args.progress_bar)

curr_dir = os.getcwd()

config = ConfigParser(args.config)

base_dir = curr_dir

weather = config["weather"]
model = config['EPICModel']
output_dir = config['output_dir']
log_dir = config["log_dir"]
model_dir = os.path.dirname(model)


process_outputs = import_function(config["process_outputs"])

# print(config["process_outputs"], process_outputs)

os.makedirs(output_dir, exist_ok = True)
os.makedirs(log_dir, exist_ok = True)


# def check_system_resources(folder_path):
if config["num_of_workers"] > os.cpu_count():
    print('Warning!')
    print(f"Workers greater than number of CPU cores ({os.cpu_count()})")

daily_weather = DailyWeather(weather["dir"], weather["start_date"], weather["end_date"], weather['offline'])

subprocess.Popen(f'chmod +x {model}', shell=True).wait()
model = model.split('/')[-1]
def process_model(row):
    fid = row['FieldID']
    # Define paths using the config and base_dir
    new_dir = os.path.join(base_dir, 'sims', str(fid))

    # Delete the new directory if it exists
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
        
    # Copy EPICModel to a new directory named as id
    shutil.copytree(model_dir, new_dir)
    os.chdir(new_dir)
    
    # if not weather['offline']:
    dly = daily_weather.get(row['y'], row['x'])
    dly.save(fid)
    dly.to_monthly(fid)
    writeDATFiles(new_dir, config, fid, row)
    
    # Run the model and collect outputs
    command = f'nohup ./{model} > {os.path.join(log_dir, f"{fid}.out")} 2>&1'
    subprocess.Popen(command, shell=True).wait()
    
    for out_type in config['output_types']:
        out_file_loc = f'{fid}.{out_type}'
        glob('./*')
        if os.path.exists(out_file_loc) and os.path.getsize(out_file_loc) > 0:
            pass
        else:
            raise Exception("Output files not Found")
    else: 
        if process_outputs is not None:
            process_outputs(fid, base_dir)
        if output_dir is not None:
            for out_type in config['output_types']:
                out_file_loc = f'{fid}.{out_type}'
                shutil.move(out_file_loc, os.path.join(output_dir, f'{fid}.{out_type}'))
        os.remove(os.path.join(log_dir, f"{fid}.out"))

    # Return to the root directory and delete the simulation directory
    os.chdir(base_dir)
    shutil.rmtree(new_dir)

info = pd.read_csv('info.csv')

opc_files = glob(f'{config["opc_dir"]}/*.OPC')
present = [(os.path.basename(f).split('.'))[0] for f in opc_files]
info = info.loc[(info['opc'].astype(str)).isin(present)]

if args.progress_bar == 'True':
    print('Selection:', [i.strip() for i in config["select"].split('+')])

info = filter_dataframe(info, config["select"])
info_ls = info.to_dict('records')

total = len(info_ls)

# Check the available disk space for a given folder
est = int(len(config['output_types'])*total/200)
if not process_outputs: check_disk_space(output_dir, est)

if args.progress_bar == 'True':
    print('Total Field Sites:', total)

process_model(info_ls[0])
parallel_executor(process_model, info_ls, max_workers = config["num_of_workers"], timeout = config["timeout"], bar = (args.progress_bar == 'True'))
#shutil.rmtree(os.path.join(base_dir, 'sims'))


plot = import_function(config['visualize'])
if plot is not None: 
    import geopandas as gpd    
    file_path = config["Fields_of_Interest"]
    exp_name = config["EXPName"]
    file_extension = (file_path.split('.'))[-1]
    if file_extension == 'shp':
        shp = gpd.read_file(file_path)
        shp['FieldID'] = shp['FieldID'].astype('int')
        plot(shp, exp_name)
    else:
        print('AOI has to be a shape file')

        
