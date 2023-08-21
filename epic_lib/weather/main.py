import os
EPICLib = os.environ.get('EPICLib')
from .daymet import *
from misc.utils import LatLonLookup
from epic_io.inputs import DLY
import pandas as pd
import subprocess

def download_nldas(start_date="1981-01", end_date="2023-06", lat_min=39.8, lat_max=43.0, lon_min=-104, lon_max=-95.3, out_dir=None):
    if not out_dir:
        raise ValueError("Working directory must be provided!")
    
    command = f'python3 {EPICLib}/weather/nldas_ws.py -s {start_date} -e {end_date} \
                -lat_min {lat_min} -lat_max {lat_max} -lon_min {lon_min} -lon_max {lon_max} -w {out_dir}'
    message = subprocess.Popen(command, shell=True)
    
class DailyWeather:
    def __init__(self, path, start_date, end_date):
        self.path = path
        self.start_date = start_date
        self.end_date = end_date
        self.lookup = LatLonLookup(path + '/nldas_grid.tif')

    def get(self, lat, lon):
        nldas_id = self.lookup.get(lat, lon)
        data = get_daymet_data(lat, lon, self.start_date, self.end_date)
        ws = pd.read_csv(self.path + f'/NLDAS_csv/{nldas_id}.csv')
        ws.columns = ['date', 'vals']
        ws['date'] = pd.to_datetime(ws['date'])
        end_date = pd.to_datetime(self.end_date)
        ws = ws[ws['date'] <= end_date]
        data['ws'] = ws['vals']
        return DLY(data)