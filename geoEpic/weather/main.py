import os
import pandas as pd
from .daymet import *
from geoEpic.io import DLY
from geoEpic.misc.raster_utils import LatLonLookup
    
class DailyWeather:
    def __init__(self, path, start_date, end_date, offline = False):
        self.path = path
        self.start_date = start_date
        self.end_date = end_date
        self.offline = offline
        if not offline:
            self.lookup = LatLonLookup(path + '/nldas_grid.tif')
        else:
            self.lookup = LatLonLookup(path + '/climate_grid.tif')

    def get(self, lat, lon):
        if not self.offline:
            nldas_id = int(self.lookup.get(lat, lon))
            data = get_daymet_data(lat, lon, self.start_date, self.end_date)
            data['date'] = pd.to_datetime(data[['year', 'month', 'day']])
            ws = pd.read_csv(self.path + f'/NLDAS_csv/{nldas_id}.csv')
            ws.columns = ['date', 'ws']
            ws['date'] = pd.to_datetime(ws['date'])
            data['date'] = pd.to_datetime(data[['year', 'month', 'day']])
            data = pd.merge(data, ws, on='date', how='left', suffixes=('', '_new'))
            data['ws'] = data['ws'].fillna(3.5)
            data.sort_values('date', inplace=True)
            data.drop('date', axis=1, inplace=True)
            return DLY(data)
        else:
            daymet_id = int(self.lookup.get(lat, lon))
            return DLY.load(self.path + f'/Daily/{daymet_id}')
