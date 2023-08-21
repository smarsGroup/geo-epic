import os
EPICLib = os.environ.get('EPICLib')
import subprocess
from misc.utils import sample_raster_nearest

def process_gdb(region_code, gdb_path):
    command = f'python3 {EPICLib}/ssurgo/processing.py -r {region_code} -gdb {gdb_path}'
    message = subprocess.Popen(command, shell=True)
    
def get_soil_ids(coords):
    return sample_raster_nearest(f'{EPICLib}/ssurgo/data/SSURGO_try.tif', coords)['band_1'].astype(int)