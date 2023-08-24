import os
import subprocess
from misc.raster_utils import sample_raster_nearest
    
def get_soil_ids(coords, ssurgo_map, invalid = None):
    soil_ids = sample_raster_nearest(ssurgo_map, coords)
    soil_ids = soil_ids['band_1'].astype(int)
    return soil_ids