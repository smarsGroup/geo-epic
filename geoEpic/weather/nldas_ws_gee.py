import numpy as np
import pandas as pd
from geoEpic.utils import parallel_executor
import argparse
from geoEpic.io import ConfigParser
import geopandas as gpd
import os
import ee
from datetime import datetime, timedelta
from geoEpic.io import DataLogger
from geoEpic.gee.initialize import ee_Initialize
from geoEpic.utils.workerpool import WorkerPool
import shutil
import time
from tqdm import tqdm

# Parse command line arguments
parser = argparse.ArgumentParser(description="NLDAS Script with Arguments")
parser.add_argument("-c", "--config", default= "./config.yml", help="Path to the configuration file")
parser.add_argument("-w", "--max_workers", default = 4, help = "No. of maximum workers")
args = parser.parse_args()

config = ConfigParser(args.config)
max_workers = args.max_workers
weather = config["weather"]
aoi = config["Area_of_Interest"]
start_date = weather["start_date"]
end_date = weather["end_date"]
working_dir = weather["dir"]

# Change working dir
os.makedirs(working_dir, exist_ok = True)
os.chdir(working_dir)

# Access values using args.bbox
if aoi.endswith('.shp'):
    gdf = gpd.read_file(aoi)
    gdf = gdf.to_crs(epsg=4326)
    lon_min, lat_min, lon_max, lat_max = gdf.total_bounds
elif aoi.endswith('.csv'):
    gdf = pd.read_csv(aoi)
    lon_min, lat_min = np.floor(gdf['x'].min() * 1e5)/1e5, np.floor(gdf['y'].min() * 1e5)/1e5
    lon_max, lat_max = np.ceil(gdf['x'].max() * 1e5)/1e5, np.ceil(gdf['y'].max() * 1e5)/1e5

bbox = ee.Geometry.BBox(lon_min, lat_min, lon_max, lat_max)

sql_cache = os.path.join(working_dir,'.cache')
os.makedirs(sql_cache,exist_ok=True)

nldas_data_path = os.path.join(working_dir,'NLDAS_data')
os.makedirs(nldas_data_path,exist_ok=True)

nldas_csv_path = os.path.join(working_dir,'NLDAS_csv')
if os.path.isdir(nldas_csv_path):
    shutil.rmtree(nldas_csv_path)
os.makedirs(nldas_csv_path,exist_ok=True)

data_logger = DataLogger(backend="sql",output_folder=sql_cache)

project_name = ee_Initialize()
pool = WorkerPool(f'gee_global_lock_{project_name}') 
pool.open(40)

def get_pixels_data(date):
    
    date_str = date.strftime('%Y-%m-%d')
    start_date = ee.Date(date_str)
    end_date = start_date.advance(1, 'day')  # Advance one day to cover a 24-hour period
    
    img_collection = ee.ImageCollection('NASA/NLDAS/FORA0125_H002') \
        .filterDate(start_date, end_date) \
        .filterBounds(bbox)
        
    wind_bands = img_collection.select(['wind_u', 'wind_v'])

    image = wind_bands.mean()
    
    wind_u = image.select('wind_u')
    wind_v = image.select('wind_v')
    wind_speed = wind_u.pow(2).add(wind_v.pow(2)).sqrt().rename('wind_speed')
    
    # Add the wind speed band to the image
    image_with_speed = image.addBands(wind_speed)
    
    # Sample the image
    samples = image_with_speed.sample(
        region=bbox,
        scale=12000,  # Adjust as needed
        geometries=True
    )
    
    worker = pool.acquire()

    try:
        df = ee.data.computeFeatures({
                'expression': samples,
                'fileFormat': 'PANDAS_DATAFRAME'
            })
    finally: 
        pool.release(worker)
        
    df['lon'] = df['geo'].apply(lambda x: round(x['coordinates'][0], 2))
    df['lat'] = df['geo'].apply(lambda x: round(x['coordinates'][1], 2))
    df = df.drop(columns=['geo','wind_u','wind_v'])
    
    df.to_csv(os.path.join(nldas_data_path,f'{date_str}.csv'),index=False)

def get_non_downloaded_dates(date_list, output_folder):
    date_strings = {date.strftime('%Y-%m-%d') for date in date_list}

    # Get a set of date strings from filenames in the folder
    available_dates = set()
    for filename in os.listdir(output_folder):
        if filename.endswith(".csv"):
            # Extract date part from filename
            date_part = filename.split(".csv")[0]
            available_dates.add(date_part)

    # Find missing dates by subtracting sets
    missing_dates = date_strings - available_dates
    missing_dates_datetime = [datetime.strptime(date_str, '%Y-%m-%d') for date_str in missing_dates]
    return missing_dates_datetime

def get_dates_list(start_date, end_date):
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    return date_list

dates = get_dates_list(start_date, end_date)
date_strings = {date.strftime('%Y-%m-%d') for date in dates}
filtered_dates = get_non_downloaded_dates(dates,nldas_data_path)
print('Downloading NLDAS windspeed...')
parallel_executor(get_pixels_data, filtered_dates, max_workers = max_workers)


failed_dates = get_non_downloaded_dates(dates,nldas_data_path)
if len(failed_dates)>0:
    print('Retrying Failed dates...')
    time.sleep(2)
    parallel_executor(get_pixels_data, failed_dates, max_workers = max_workers)

print('Writing NLDAS wind speed to csv files...')
for date in tqdm(dates):
    date_str = date.strftime('%Y-%m-%d')
    ws = pd.read_csv(os.path.join(nldas_data_path,f'{date_str}.csv'))
    
    # Function to write data to CSV
    def write_func(ws_data):
        lat = int(ws_data['lat']*100)
        lon = int(ws_data['lon']*100)
        name = f'{lat}a{lon}'
        df = pd.DataFrame([{'date': date_str,
                            'wind_speed': round(ws_data['wind_speed'],2)}])
        df.to_csv(os.path.join(nldas_csv_path,f'{name}.csv'), mode='a', header=False, index=False)
    
    date_ws = ws.to_dict(orient='records')
    
    parallel_executor(write_func, date_ws, max_workers=max_workers, return_value = False,bar=False)
    
date_str = dates[0].strftime('%Y-%m-%d')
ws_loc = pd.read_csv(os.path.join(nldas_data_path,f'{date_str}.csv'))
ws_loc = ws_loc.drop(columns=['wind_speed'])
ws_loc.to_csv(os.path.join(working_dir,'nldas_grid.csv'),index=False)
    