import os
import sys
EPICLib = os.environ.get('EPICLib')
sys.path.insert(0, EPICLib)

import json
import shutil
import subprocess
from weather import DailyWeather
import numpy as np
import pandas as pd
from misc.utils import parallel_executor, writeDATFiles

# Fetch the base directory
base_dir = os.getcwd()
# Load the JSON data from a file
with open('config.json') as config_file:
    config = json.load(config_file)

start_date = config["weather"]["start_date"]
end_date = config["weather"]["end_date"]
weather_dir = config["weather"]["dir"].replace('./', base_dir + '/')
model = config['EPICModel'].replace('./', base_dir + '/')
output_dir = config['output_dir'].replace('./', base_dir + '/')
log_dir = config["log_dir"].replace('./', base_dir + '/')
model_dir = '/'.join(model.split('/')[:-1])
model = model.split('/')[-1]

daily_weather = DailyWeather(weather_dir, start_date, end_date)

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
    
    dly = daily_weather.get(row['y'], row['x'])
    dly.save(fid)
    dly.to_monthly(fid)
    writeDATFiles(new_dir, base_dir, fid, row)
    
    # Run the model and collect outputs
    command = f'nohup ./{model} &> {os.path.join(log_dir, f"{fid}.out")}'
    subprocess.Popen(command, shell=True).wait()
    
    for out_type in config['output_types']:
        out_file_loc = os.path.join(new_dir, f'{fid}.{out_type}')
        if os.path.exists(out_file_loc) and os.path.getsize(out_file_loc) > 0:
            shutil.move(out_file_loc, os.path.join(output_dir, f'{fid}.{out_type}'))
        else:
            raise Exception("Simulation Failed")
    else: os.remove(os.path.join(log_dir, f"{fid}.out"))

    # Return to the root directory and delete the simulation directory
    os.chdir(base_dir)
    shutil.rmtree(new_dir)

info = pd.read_csv('info.csv')
info_ls = info.to_dict('records')
parallel_executor(process_model, info_ls, max_workers = 80)
