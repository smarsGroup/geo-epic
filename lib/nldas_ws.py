from pydap.cas.urs import setup_session
import numpy as np
import xarray as xr
import pandas as pd
from utils import parallel_executor
from formule import windspd
from tqdm import tqdm

username = 'bharathc'
password = '@Ce1one$28'

# Define latitude and longitude range for Kansas and Oklahoma
lat_range = slice(33.69, 40.56)
lon_range = slice(-103.2, -94.44)

# Define date range from 1981-01 to 2023-06
dates = pd.date_range(start='1981-01', end='2023-06', freq = 'M')

print('Connecting to the dataset...')

# URL of the dataset
dataset_url = 'https://hydro1.gesdisc.eosdis.nasa.gov:443/dods/NLDAS_FORA0125_H.002'

# Setup a session to connect to the dataset
session = setup_session(username, password, check_url=dataset_url)
store = xr.backends.PydapDataStore.open(dataset_url, session=session)

# Open the dataset and select 'ugrd10m' and 'vgrd10m' variables
# Select latitude and longitude range
data_set = xr.open_dataset(store)[['ugrd10m', 'vgrd10m']]
data_set = data_set.sel(lon = lon_range, lat = lat_range)

print('Downloading data...')


# Use parallel execution to download data for all dates
parallel_executor(download_func, dates, max_workers = 8, return_value = False)

print('Writing data to CSV...')

# For each date, load the data and write to CSV
for date in tqdm(dates):
    date_str = date.strftime('%Y-%m')
    ws = np.load(f'/gpfs/data1/cmongp/Bharath/NLDAS_data/{date_str}.npy')
    days, h, w = ws.shape
    ws = ws.reshape(days, -1)
    
    # Function to write data to CSV
    def write_func(i):
        df = pd.DataFrame({'dates': pd.date_range(start = f'{date_str}-01', end = f'{date_str}-{days}', freq='D'),
                            'values': ws[:, i].flatten()})
        df.to_csv(f'/gpfs/data1/cmongp/Bharath/NLDAS_csv/{i}.csv', mode='a', header=False, index=False)
    
    # Use parallel execution to write data to CSV for all grid points
    parallel_executor(write_func, range(h*w), max_workers = 20, return_value = False)