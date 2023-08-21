import os
EPICLib = os.environ.get('EPICLib')

import subprocess

def generate_site_files(info_file, out_dir):
    command = f'python3 {EPICLib}/sit/generate.py -i {info_file} -o {out_dir}'
    message = subprocess.Popen(command, shell=True)

# def get_site_info(coords):
#     prefix = f'{EPICLib}/ssurgo/data'
#     info = coords
#     info['ssu'] = sample_raster_nearest(f'{prefix}/SSURGO_try.tif', coords.values)['band_1'].astype(int)
#     info['ele'] = sample_raster_nearest(f'{prefix}/SRTM_1km_US_project.tif', coords.values)['band_1']
#     info['slope'] = sample_raster_nearest(f'{prefix}/slope_us.tif', coords.values)['band_1']
#     info = info.fillna(0)
#     info['slope_steep'] = round(info['slope'] / 100, 2)

#     # Reading slopelen CSV file
#     slope_len = pd.read_csv(f"{prefix}/slopelen_1.csv")
#     slope_len = slope_len[['mukey', 'slopelen_1']]
#     slope_len['mukey'] = pd.to_numeric(slope_len['mukey'], errors='coerce')
#     slope_len['mukey'] = slope_len['mukey'].fillna(0)
#     slope_len['mukey'] = slope_len['mukey'].astype(int)
#     info = pd.merge(info, slope_len, how='left', left_on='ssu', right_on='mukey')
#     info.drop(['x', 'y'], axis=1, inplace=True)
#     return info