import os
import argparse
import shutil
import subprocess
from epic_lib.weather import DailyWeather
import numpy as np
import pandas as pd
from epic_lib.misc import ConfigParser
from epic_lib.misc.utils import parallel_executor, writeDATFiles

# Fetch the base directory
parser = argparse.ArgumentParser(description="EPIC workspace")
parser.add_argument("-c", "--config", default= "./config.yml", help="Path to the configuration file")
args = parser.parse_args()

curr_dir = os.getcwd()

config = ConfigParser(curr_dir, args.config)

base_dir = curr_dir

weather = config["weather"]
model = config['EPICModel']
output_dir = config['output_dir']
log_dir = config["log_dir"]
model_dir = os.path.dirname(model)

os.makedirs(output_dir, exist_ok = True)
os.makedirs(log_dir, exist_ok = True)

daily_weather = DailyWeather(weather["dir"], weather["start_date"], weather["end_date"])

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
    
    dly = daily_weather.get(row['y'], row['x'])
    dly.save(fid)
    dly.to_monthly(fid)
    writeDATFiles(new_dir, config, fid, row)
    
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

total = len(info_ls)
min_ind, max_ind = config["Range"]
min_ind, max_ind = int(min_ind*total), int(max_ind*total)
parallel_executor(process_model, info_ls[min_ind: max_ind], max_workers = config["num_of_workers"])
#shutil.rmtree(os.path.join(base_dir, 'sims'))
