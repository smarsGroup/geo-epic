import os
import shutil
import subprocess
from glob import glob
from epic_lib.weather import DailyWeather
import numpy as np
import pandas as pd
from epic_lib.misc import ConfigParser
from epic_lib.misc.utils import *

daily_weather = DailyWeather(weather["dir"], weather["start_date"], weather["end_date"], weather['offline'])

class EPICModel:
    def __init__(self, config):
        self.model = config['EPICModel']
        self.output_dir = config['output_dir']
        self.log_dir = config['log_dir']
        self.model_dir = os.path.dirname(self.model)
        self.config = config
        self.base_dir = os.getcwd()  # Assuming base_dir is the current working directory

        # Ensure output and log directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        # Make the model executable
        subprocess.Popen(f'chmod +x {self.model}', shell=True).wait()

    def run(self, row):
        # Assumes 'row' is a dictionary containing FieldID, x, y, and other needed keys
        fid = row['FieldID']
        new_dir = os.path.join(self.base_dir, 'sims', str(fid))

        # Delete the new directory if it exists and create a fresh one
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        shutil.copytree(self.model_dir, new_dir)
        os.chdir(new_dir)

        # Process weather data if needed
        # Assumes functions like `daily_weather.get` and `writeDATFiles` are defined
        if not row.get('weather', {}).get('offline', True):
            dly = daily_weather.get(row['y'], row['x'])
            dly.save(fid)
            dly.to_monthly(fid)
        
        writeDATFiles(new_dir, self.config, fid, row)

        # Run the model and handle outputs
        model_executable = os.path.basename(self.model)
        command = f'nohup ./{model_executable} > {os.path.join(self.log_dir, f"{fid}.out")} 2>&1'
        subprocess.Popen(command, shell=True).wait()

        # Check and move output files
        self._handle_outputs(fid, new_dir)

        # Cleanup
        os.chdir(self.base_dir)
        shutil.rmtree(new_dir)

    def _handle_outputs(self, fid, new_dir):
        for out_type in self.config['output_types']:
            out_file_loc = os.path.join(new_dir, f'{fid}.{out_type}')
            if not (os.path.exists(out_file_loc) and os.path.getsize(out_file_loc) > 0):
                raise Exception("Output files not found")
            shutil.move(out_file_loc, os.path.join(self.output_dir, f'{fid}.{out_type}'))

        # Optional: Delete log file after moving outputs
        os.remove(os.path.join(self.log_dir, f"{fid}.out"))

# Example usage
config = {
    'EPICModel': '/path/to/model',
    'output_dir': '/path/to/output',
    'log_dir': '/path/to/log',
    'output_types': ['yield', 'biomass']
}

model = EPICModel(config)
data_row = {
    'FieldID': '001',
    'x': 100,
    'y': 200,
    'weather': {'offline': False}
}
model.run(data_row)
