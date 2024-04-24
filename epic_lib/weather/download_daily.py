import os
import argparse
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
import rioxarray as rio
import geopandas as gpd
from epic_lib.io import DLY
from epic_lib.weather.daymet import *
import subprocess
from epic_lib.weather.main import DailyWeather
from epic_lib.misc.utils import parallel_executor
from epic_lib.misc import ConfigParser
from epic_lib.misc.raster_utils import raster_to_dataframe, sample_raster_nearest
from epic_lib.dispatcher import dispatch
# Parse command line arguments
parser = argparse.ArgumentParser(description="Downloads daily weather data")
parser.add_argument("-c", "--config", default= "./config.yml", help="Path to the configuration file")
parser.add_argument("-w", "--max_workers", default = 20, help = "No. of maximum workers")
args = parser.parse_args()

curr_dir = os.getcwd()

config = ConfigParser(curr_dir, args.config)

weather = config["weather"]
aoi = config["Fields_of_Interest"]
working_dir = weather["dir"]
region_code = config["code"]
start_date = weather["start_date"]
end_date = weather["end_date"]

print('Processing shape file')

# Define date range from command-line arguments
# dates = pd.date_range(start = start_date, end = end_date, freq = 'M')

print('curr', os.getcwd())
gdf = gpd.read_file(aoi)
gdf = gdf.to_crs(epsg=4326)

# Change working dir
os.makedirs(working_dir, exist_ok = True)
os.chdir(working_dir)


res_value = 0.00901  # 1 km resolution in degree
lon_min, lat_min, lon_max, lat_max = gdf.total_bounds
lon = np.arange(lon_min, lon_max, res_value)
lat = np.arange(lat_min, lat_max, res_value)
lon, lat = np.meshgrid(lon, lat)

# Create a DataArray from the grid
grid = np.arange(lat.size).reshape(lat.shape)
grid = int(region_code)*1e7 + grid

data_set = xr.DataArray(grid, coords=[('y', lat[:, 0]), ('x', lon[0, :])])

# Mask the DataArray using Nebraska's shape
mask = rasterio.features.geometry_mask([geom for geom in gdf.geometry],
                                  transform=data_set.rio.transform(),
                                  invert=True, out_shape=data_set.shape)
data_set = data_set.where(mask)
# Save the DataArray as a GeoTIFF
data_set = data_set.rio.write_crs("EPSG:4326")
data_set.rio.to_raster("./climate_grid.tif")

if not os.path.exists('./NLDAS_csv'):
    dispatch('weather', 'download_windspeed', f'-s {start_date} -e {end_date} \
                    -b {lat_min} {lat_max} {lon_min} {lon_max} -o .', True)

daily_weather = DailyWeather('.', start_date, end_date)

os.makedirs('./Daily', exist_ok = True)
os.makedirs('./Monthly', exist_ok = True)

def create_dly(row):
    _, lon, lat, daymet_id = row.values()
    file_path = os.path.join('./Daily/', f'{int(daymet_id)}.DLY')
    if not os.path.isfile(file_path):
        dly = daily_weather.get(lat, lon)
        dly.save(f'./Daily/{int(daymet_id)}')
        dly.to_monthly(f'./Monthly/{int(daymet_id)}')

cmids = raster_to_dataframe("./climate_grid.tif")
# nldas_id = sample_raster_nearest('./nldas_grid.tif', cmids[['x', 'y']].values)
# cmids['nldas_id'] = nldas_id['band_1']
cmids = cmids.fillna(-1)
cmids = cmids[cmids['band_1'] != -1]
cmids.reset_index(inplace = True)
cmids = cmids.rename(columns={'band_1': 'daymet_id'})

cmids_ls = cmids.to_dict('records')
parallel_executor(create_dly, cmids_ls, max_workers = args.max_workers)

# # Determine the latitude and longitude range based on the provided arguments
# if args.shapefile:
#     # Load the shapefile and get the bounds
#     gdf = gpd.read_file(args.shapefile)
#     bounds = gdf.total_bounds
#     lat_min, lon_min, lat_max, lon_max = bounds[1], bounds[0], bounds[3], bounds[2]
# elif args.state_name:
#     # # Load a shapefile with state boundaries (you need to provide this)
#     # gdf = gpd.read_file('path_to_your_states_shapefile.shp')
#     # # Get the bounds of the specified state
#     # state = gdf[gdf['STATE_NAME'] == args.state_name]
#     # bounds = state.total_bounds
#     # lat_min, lon_min, lat_max, lon_max = bounds[1], bounds[0], bounds[3], bounds[2]

# # Rest of your code...
