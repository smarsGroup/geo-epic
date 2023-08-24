import os
import pandas as pd
from .daymet import *
from epic_io import DLY
from misc.raster_utils import LatLonLookup
    
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