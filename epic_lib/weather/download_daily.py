import os
import argparse
import numpy as np
import pandas as pd
import rasterio
import xarray as xr
import geopandas as gpd
from epic_io import DLY
from .daymet import *
from .main import DailyWeather

# Parse command line arguments
parser = argparse.ArgumentParser(description="NLDAS Script with Arguments")
parser.add_argument("-s", "--start_date", default="1981-01", help="Start date (YYYY-MM) for date range")
parser.add_argument("-e", "--end_date", default="2023-06", help="End date (YYYY-MM) for date range")
parser.add_argument("-r", "--region", help="Path to the shapefile")
parser.add_argument("-c", "--region_code", help="An integer, index starts with this code")
parser.add_argument("-w", "--working_dir", required=True, help="Working directory")
args = parser.parse_args()

# Change working dir
os.makedirs(args.working_dir, exist_ok = True)
os.chdir(args.working_dir)

# Define date range from command-line arguments
# dates = pd.date_range(start = args.start_date, end = args.end_date, freq = 'M')
gdf = gpd.read_file(args.region)

res_value = 0.00901  # 1 km resolution in degree
xmin, ymin, xmax, ymax = gdf.total_bounds
lon = np.arange(xmin, xmax, res_value)
lat = np.arange(ymin, ymax, res_value)
lon, lat = np.meshgrid(lon, lat)

# Create a DataArray from the grid
grid = np.arange(lat.size).reshape(lat.shape)
grid = int(args.region_code)*1e7 + grid

data_set = xr.DataArray(grid, coords=[('y', lat[:, 0]), ('x', lon[0, :])])
# Mask the DataArray using Nebraska's shape
mask = rasterio.features.geometry_mask([geom for geom in gdf.geometry],
                                  transform=data_set.rio.transform(),
                                  invert=True, out_shape=data_set.shape)
data_set = data_set.where(mask)
# Save the DataArray as a GeoTIFF
data_set = data_set.rio.write_crs("EPSG:4326")
data_set.rio.to_raster("./climate_grid.tif")

daily_weather = DailyWeather(args.working_dir, args.start_date, args.end_date)

def create_weather_files(row):
    lon, lat, daymet_id = row.values()
    file_path = os.path.join('./Daily/', f'{int(daymet_id)}.DLY')
    if not os.path.isfile(file_path):
        dly = daily_weather.get(lat, lon)
        dly.save(f'./Daily/{int(daymet_id)}')
        dly.to_monthly(f'./Monthly/{int(daymet_id)}')



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