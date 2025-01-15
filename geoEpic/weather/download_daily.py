import os
import argparse
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
import rioxarray as rio
import geopandas as gpd
from geoEpic.io import DLY, ConfigParser
from geoEpic.weather.daymet import *
import subprocess
from geoEpic.weather.main import DailyWeather
from geoEpic.utils import parallel_executor
from geoEpic.utils import raster_to_dataframe
from geoEpic.dispatcher import dispatch
from geoEpic.utils import GeoInterface
from geoEpic.utils.run_model_util import create_run_info
import sys



# Parse command line arguments
parser = argparse.ArgumentParser(description="Downloads daily weather data")
parser.add_argument("-c", "--config", default= "./config.yml", help="Path to the configuration file")
parser.add_argument("-w", "--max_workers", default = 20, help = "No. of maximum workers")
args = parser.parse_args()

curr_dir = os.getcwd()
config_loc = os.path.abspath(args.config)

config = ConfigParser(args.config)

max_workers = int(args.max_workers)

weather = config["weather"]
aoi = config["Area_of_Interest"]
working_dir = weather["dir"]
region_code = config["code"]
start_date = weather["start_date"].strftime('%Y-%m-%d')
end_date = weather["end_date"].strftime('%Y-%m-%d')

print('Processing shape file')

# Define date range from command-line arguments
# dates = pd.date_range(start = start_date, end = end_date, freq = 'M')

print('workspace directory : ', os.getcwd())

if aoi.endswith('.shp'):
    gdf = gpd.read_file(aoi)
    gdf = gdf.to_crs(epsg=4326)
    lon_min, lat_min, lon_max, lat_max = gdf.total_bounds
elif aoi.endswith('.csv'):
    gdf = pd.read_csv(aoi)
    lon_min, lat_min = np.floor(gdf['x'].min() * 1e5)/1e5, np.floor(gdf['y'].min() * 1e5)/1e5
    lon_max, lat_max = np.ceil(gdf['x'].max() * 1e5)/1e5, np.ceil(gdf['y'].max() * 1e5)/1e5

# Change working dir
os.makedirs(working_dir, exist_ok = True)
os.chdir(working_dir)

res_value = 0.00901  # 1 km resolution in degree

lon = np.arange(lon_min, lon_max, res_value)
lat = np.arange(lat_min, lat_max, res_value)
lon, lat = np.meshgrid(lon, lat)

# Create a DataArray from the grid and save it in climate_grid.tif
if not os.path.exists('./climate_grid.tif'):
    grid = np.arange(lat.size).reshape(lat.shape)
    
    data_set = xr.DataArray(grid, coords=[('y', lat[:, 0]), ('x', lon[0, :])])

    # Mask the DataArray using Nebraska's shape
    if aoi.endswith('.shp'):
        mask = rasterio.features.geometry_mask([geom for geom in gdf.geometry],
                                        transform=data_set.rio.transform(),
                                        invert=True, out_shape=data_set.shape)
        data_set = data_set.where(mask)
    # Save the DataArray as a GeoTIFF
    data_set = data_set.rio.write_crs("EPSG:4326")
    data_set.rio.to_raster("./climate_grid.tif")

# if NLDAS_csv folder does not exist, download the wind speed data
if not os.path.exists('./NLDAS_csv'):
    # dispatch('weather', 'windspeed', f'-s {start_date} -e {end_date} \
    #                 -b {lat_min} {lat_max} {lon_min} {lon_max} -o .', True)
    dispatch('weather', 'windspeed', f'-c {config_loc}', True)
    
daily_weather = DailyWeather('.', start_date, end_date)

os.makedirs('./Daily', exist_ok = True)
os.makedirs('./Monthly', exist_ok = True)

#create dly file
def create_dly(row):
    lon, lat, daymet_id = row.values()
    file_path = os.path.join('./Daily/', f'{int(daymet_id)}.DLY')
    if not os.path.isfile(file_path):
        dly = daily_weather.get(lat, lon)
        dly.save(f'./Daily/{int(daymet_id)}')
        dly.to_monthly(f'./Monthly/{int(daymet_id)}')


'''
Below commented code creates list of climate ids from the clim_grid.tif raster file
'''
# cmids = raster_to_dataframe("./climate_grid.tif")
# # nldas_id = sample_raster_nearest('./nldas_grid.tif', cmids[['x', 'y']].values)
# # cmids['nldas_id'] = nldas_id['band_1']
# cmids = cmids.fillna(-1)
# cmids = cmids[cmids['band_1'] != -1]
# cmids.reset_index(inplace = True)
# cmids = cmids.rename(columns={'band_1': 'daymet_id'})

# #remove existing daymet ids in output folder from input args
# present_daymet_ids = [int(f.split('.')[0]) for f in os.listdir('./Daily')]
# cmids['daymet_id'] = cmids['daymet_id'].astype(int)
# cmids = cmids[~cmids['daymet_id'].isin(present_daymet_ids)]

# cmids_ls = cmids.to_dict('records')



'''
Below code creates info.csv file. and creates list of climate ids from the info.csv file
'''
lookup = GeoInterface('./climate_grid.tif')

def get_clim_id(lat, lon):
    return int(lookup.lookup(lat, lon)['band_1'])

info_df_loc = config['run_info']
if not os.path.exists(info_df_loc):
    create_run_info(config['Area_of_Interest'],info_df_loc)
run_info_df = pd.read_csv(info_df_loc)

clim_id_list = []
for index, row in run_info_df.iterrows():
    clim_id = get_clim_id(row['lat'], row['lon'])
    clim_id_list.append({'lon': row['lon'], 'lat': row['lat'],  'band_1': clim_id})
    # print(f'Climate ID: {clim_id}')
    run_info_df.at[index, 'dly'] = int(clim_id)


#parallel execute to create dly files
if( len(clim_id_list)>0 ):
    create_dly(clim_id_list[0])
    parallel_executor(create_dly, clim_id_list[1:], max_workers = max_workers)

run_info_df = run_info_df.astype({'dly': int})
run_info_df.to_csv(info_df_loc,index=False)

