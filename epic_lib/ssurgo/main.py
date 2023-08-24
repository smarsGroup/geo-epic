import os
import subprocess
from misc.raster_utils import sample_raster_nearest
    
def get_soil_ids(coords):
    return sample_raster_nearest(f'{EPICLib}/ssurgo/data/SSURGO_try.tif', coords)['band_1'].astype(int)