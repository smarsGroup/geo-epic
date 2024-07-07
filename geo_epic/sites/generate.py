import os
import numpy as np
import pandas as pd
from geo_epic.misc.utils import parallel_executor
from geo_epic.misc.raster_utils import sample_raster_nearest
import argparse

parser = argparse.ArgumentParser(description="Process raster data and save results.")
parser.add_argument("-o", "--out_dir", type=str, required=True, help="Output directory to save results.")
parser.add_argument("-i", "--info_file", type=str, required=True, help="Path to the info file.")
parser.add_argument("-ele", "--elevation", type=str, required=True, help="Path to the SRTM_1km_US_project.tif")
parser.add_argument("-slope", "--slope_us", type=str, required=True, help="Path to the slope_us.tif")
parser.add_argument("-sl", "--slope_len", type=str, required=True, help="Path to the slope_len.csv")
args = parser.parse_args()

info = pd.read_csv(args.info_file)
coords = info[['x', 'y']].values

prefix = f'{os.path.dirname(__file__)}'

info['ele'] = sample_raster_nearest(args.elevation, coords)['band_1']
info['slope'] = sample_raster_nearest(args.slope_us, coords)['band_1']

info = info.fillna(0)
info['ssu'] = info['soil_id'].astype(int)
info['slope_steep'] = round(info['slope'] / 100, 2)

slope_len = pd.read_csv(args.slope_len)
slope_len = slope_len[['mukey', 'slopelen_1']]
slope_len['mukey'] = slope_len['mukey'].astype(int)
slope_len['slopelen_1'] = slope_len['slopelen_1'].astype(float)
info = pd.merge(info, slope_len, how='left', left_on='ssu', right_on='mukey')

print("writing site files")
#site template
with open(f"{prefix}/template.sit", 'r') as f:
    template = f.readlines()

def write_site(row):
    with open(os.path.join(args.out_dir, f"{int(row['FieldID'])}.sit"), 'w') as f:
        # Modify the template lines
        template[0] = 'USA crop simulations\n'
        template[1] = 'Prototype\n'
        template[2] = f'ID: {int(row["FieldID"])}\n'
        template[3] = f'{row["y"]:8.2f}{row["x"]:8.2f}{row["ele"]:8.2f}{template[3][24:]}'  # This will replace the first 24 characters
        template[4] = f'{template[4][:48]}{row["slopelen_1"]:8.2f}{row["slope_steep"]:8.2f}{template[4][64:]}'  # This will replace characters 49 to 64
        template[6] = '                                                   \n'
        # Write the modified template to the new file
        f.writelines(template)

info_ls = info.to_dict('records')
# print(info_ls)

parallel_executor(write_site, info_ls, max_workers = 80)