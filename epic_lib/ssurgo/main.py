import os
import subprocess
from misc.utils import find_nearest
from misc.raster_utils import raster_to_dataframe
    
def get_soil_ids(coords, ssurgo_map, files_dir):
    ssurgo = raster_to_dataframe(ssurgo_map)
    soil_list = [int(f.split('.')[0]) for f in os.listdir(files_dir)]
    ssurgo = ssurgo[ssurgo['band_1'].isin(soil_list)]
    inds = find_nearest(coords, ssurgo[['x', 'y']].values)
    soil_ids = (ssurgo['band_1'].values)[inds]
    return soil_ids
