import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from osgeo import ogr
import argparse
import geopandas as gpd
from geoEpic.utils import read_gdb_layer, parallel_executor
from geoEpic.io import ConfigParser 
from geoEpic.soil import get_ssurgo_mukeys 
from geoEpic.utils.run_model_util import create_run_info
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

parser = argparse.ArgumentParser(description="soil file creation script")
parser.add_argument("-c", "--config", default= "./config.yml", help="Path to the configuration file")
# parser.add_argument("-r", "--region", default="OK", help="Region code")
# parser.add_argument("-gdb", "--gdb_path", default="./gSSURGO_OK.gdb", help="gdb file path")
# parser.add_argument("-o", "--output_path", default = None, help="outpath path for soil files. If not mentioned, files dir is created in location of gdb")
args = parser.parse_args()

# Open the GDB
config = ConfigParser(args.config)

region = config['Region']
soil_conf = config["soil"]
gdb_path = soil_conf['ssurgo_gdb']
output_path = soil_conf['files_dir']

driver = ogr.GetDriverByName("OpenFileGDB")
gdb_data = driver.Open(gdb_path)


print("Reading GDB (est time: 30 mins)")

#chorizon
columns = [4, 9, 72, 94, 91, 33, 51, 135, 85, 132, 66, 114, 126, 24, 15, 18, 78, 82, 169]
names = ['desgnvert','hzdepb_r','dbthirdb_1','wfifteen_1','wthirdbar1','sandtotal1','silttotal1','ph1to1h2o1','awc_r','sumbases_r','om_r','caco3_r','cec7_r','sieveno101','fraggt10_r','frag3to101','dbovendry1','ksat_r','cokey']
chorizon = read_gdb_layer(gdb_data, 'chorizon', columns, names)
chorizon = chorizon.fillna(0)
chorizon.to_csv(os.path.dirname(gdb_path) + f'/{region}_chorizon.csv', index = False)

#component
columns = [3, 79, 107, 108, 32, 1, 9, 12]
names = ['compname','hydgrp','mukey','cokey','albedodry1','comppct_r','slope_r','slopelen_1']
component = read_gdb_layer(gdb_data, 'component', columns, names)
component = component.fillna(0)
component.to_csv(os.path.dirname(gdb_path) + f'/{region}_component.csv', index = False)

#mapunit
columns = [0, 23]
names = ['MapUnitsym', 'mukey']
mapunit = read_gdb_layer(gdb_data, 'mapunit', columns, names)
mapunit = mapunit.fillna(0)
mapunit.to_csv(os.path.dirname(gdb_path) + f'/{region}_mapunit.csv', index = False)

idx = component.groupby('mukey')['comppct_r'].transform('max') == component['comppct_r']
soil = pd.merge(component[idx], mapunit, on = 'mukey', how = 'left')
soil['albedo'] = soil['albedodry1'] * 0.625

slopelen_1 = soil[['mukey', 'slopelen_1']]
slopelen_1.to_csv(config['site']['slope_length'], index = False)

soil = soil[['mukey', 'compname', 'hydgrp', 'cokey', 'albedo', 'comppct_r', 'MapUnitsym']]
soil['mukey'] = soil['mukey'].astype(int)
soil['hydgrp'] = soil['hydgrp'].replace('', 'C').fillna('C').str.slice(stop=1)
soil['hydgrp_conv'] = soil['hydgrp'].map({'A': 1, 'B': 2, 'C': 3, 'D': 4})

# Merge 'soil' and 'cohorizon' DataFrames and filter data
merged = pd.merge(chorizon, soil, on = 'cokey', how = 'left').fillna(0)
merged['mukey'] = merged['mukey'].astype(int)
merged = merged[(merged['mukey'] > 0) & (merged['wthirdbar1'] > 0)]

# Convert units
soil_layer = pd.DataFrame({
    'mukey': merged['mukey'],
    'Layer_number': merged['desgnvert'],
    'Layer_depth': merged['hzdepb_r'] * 0.01,
    'Bulk_Density': merged['dbthirdb_1'],
    'Wilting_capacity': merged['wfifteen_1'] * 0.01,
    'Field_Capacity': merged['wthirdbar1'] * 0.01,
    'Sand_content': merged['sandtotal1'],
    'Silt_content': merged['silttotal1'],
    'N_concen': 0, 'pH': merged['ph1to1h2o1'],
    'Sum_Bases': merged['sumbases_r'],
    'Organic_Carbon': merged['om_r'] * 0.58,
    'Calcium_Carbonate': merged['caco3_r'],
    'Cation_exchange': merged['cec7_r'],
    'Course_Fragment': 100 - (merged['sieveno101'] + merged['fraggt10_r'] + merged['frag3to101']),
    'cnds' : 0, 'pkrz' : 0, 'rsd' : 0,
    'Bulk_density_dry': merged['dbovendry1'], 'psp' : 0,
    'Saturated_conductivity': merged['ksat_r'] * 3.6
})

# Subset soil to only include mukeys present in SoilLayer
mukeys_in_soil_layer = soil_layer['mukey'].unique()
soil_orig = soil.copy()
soil = soil[soil['mukey'].isin(mukeys_in_soil_layer)]
soil = soil.sort_values(by = ['mukey'])

#filter soil based on shape file

if 'run_info' in config.config_data and os.path.exists(config['run_info']):
    run_info_df = pd.read_csv(config['run_info'])
    coords = run_info_df[['lon', 'lat']].values
elif 'Area_of_Interest' in config.config_data and os.path.exists(config['Area_of_Interest']):
    aoi_gdf = gpd.read_file(config['Area_of_Interest'])
    aoi_gdf['centroid'] = aoi_gdf.geometry.centroid
    aoi_gdf['lon'] = aoi_gdf['centroid'].x
    aoi_gdf['lat'] = aoi_gdf['centroid'].y
    coords = aoi_gdf[['lon', 'lat']].values
else:
    print("Either 'run_info' or 'Area_of_Interest' must be present in config.yml.")
    exit()
    
aoi_mukeys = get_ssurgo_mukeys(coords, soil_conf['soil_map'])
soil = soil[soil['mukey'].isin(aoi_mukeys)]

print("\nwriting soil files")

if output_path is None:
    outdir = os.path.dirname(config['gdb_path']) + '/files'
else:
    outdir = output_path

os.makedirs(outdir, exist_ok=True)

# filter soil mukey only which is not present
existing_mukeys = [int(f.split('.')[0]) for f in os.listdir(outdir)]
soil = soil[~soil['mukey'].isin(existing_mukeys)]

# Read template file
with open(f'{os.path.dirname(__file__)}/template.sol', 'r') as file:
    template_orig = file.readlines()
padding = ['{:8.2f}'.format(0) for _ in range(23)]
horz = ['       A' for _ in range(23)]
def write_soil(row):
    template = template_orig.copy()
    with open(os.path.join(outdir, f"{row['mukey']}.SOL"), 'w+') as file:
        soil_layer_key = soil_layer[soil_layer['mukey'] == row['mukey']]
        soil_layer_key = soil_layer_key.sort_values(by = ['Layer_depth'])
        len_cols = len(soil_layer_key)
        
        # Generate first three lines of the file
        template[0] = f"ID: {row['mukey']}\n"
        template[1] = '{:8.2f}{:8.2f}'.format(row['albedo'], row['hydgrp_conv']) + template[1][16:]
        template[2] = '{:8.2f}'.format(len_cols + 1) + template[2][8:]
        
        # Generate lines for each row in soil_layer_key dataframe
        vals = (soil_layer_key.iloc[:, 2:21].values).T
        len_rows = len(vals) 
        for i in range(len_rows):
            template[3 + i] = ''.join([f'{val:8.2f}' for val in vals[i]]) + '\n'
    
        # Fill remaining lines with padding
        for i in range(len_rows + 3, 51):
            template[i] = ''.join(padding[:len_cols]) + '\n'
        
        # Fill soil horizon to 'A'
        horz_row_ind = 47
        template[horz_row_ind] = ''.join(horz[:len_cols]) + '\n'
        
        file.writelines(template)
        
soil_ls = soil.to_dict('records')
if( len(soil_ls)>0 ):
    parallel_executor(write_soil, soil_ls, max_workers = 80)

#write soil column in run_info df

info_df_loc=os.path.join(config.dir,'info.csv')
if 'run_info' in config.config_data:
    info_df_loc = config['run_info']
if not os.path.exists(info_df_loc):
    create_run_info(config['Area_of_Interest'],info_df_loc)
run_info_df = pd.read_csv(info_df_loc)
run_info_df['soil'] = aoi_mukeys
run_info_df.to_csv(info_df_loc,index=False)