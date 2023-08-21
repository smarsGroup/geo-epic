# %%
import sys
sys.path.insert(0, '/gpfs/data1/cmongp/Bharath/lib/')

# %%
import os
import shutil
import pandas as pd
import numpy as np
import argparse
from utils import *
import subprocess

# %%
parser = argparse.ArgumentParser()
parser.add_argument(
        "-b",
        "--base_dir",
        type=str,
        default='/gpfs/data1/cmongp/rohitN/CSM/Exp4TFPStudy/OK/Testing',
        help="The path to the base directory containing common_inputfiles and EPICModel",
    )
parser.add_argument(
        "-e",
        "--epic_csv",
        type=str,
        default='/gpfs/data1/cmongp/Bharath/OKTPN_1.csv',
        help="The path to the EPIC_csv_file from which DAT listfiles are prepared",
    )
parser.add_argument(
        "-s",
        "--soil_csv",
        type=str,
        default='/gpfs/data1/cmongp/Bharath/ks_ok_soils.csv',
        help="The path to the soil csv file containing info about soil ids and locations",
    )
parser.add_argument(
        "--test",
        action='store_true',
        help="Check if the EPIC simulations are running fine for the first 100 IDs",
    )
parser.add_argument(
        "--test_num_ids",
        type=int,
        default=100,
        help="Meniton the number of runids to test. IDs taken from the first row to until 'test_num_ids' row.",
    )
parser.add_argument(
        "-n",
        "--num_cores",
        type=int,
        default=20,
        help="number of cores to run the EPIC model on",
    )
opt = parser.parse_args()

# %%
EPIC_csv = pd.read_csv(opt.epic_csv)
if opt.test:
    EPIC_csv = EPIC_csv.head(opt.test_num_ids)
df_ls = EPIC_csv.to_dict('records')

# %%
def process_model(row):
    id = row['OBJECTID']
    # Define paths
    model_dir = os.path.join(opt.base_dir, 'EPICModel')
    new_dir = os.path.join(opt.base_dir, str(id))
    output_dir = os.path.join(opt.base_dir, 'out')

    # Delete the new directory if it exists
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
        
    # Copy EPICModel to a new directory named as id
    shutil.copytree(model_dir, new_dir)
    
    # Assuming the file to edit is file.txt
    # Modify the file as you need
    with open(f'{new_dir}/EPICRUN.DAT', 'w') as ofile:
        fmt = '%8d %8d %8d 0 1 %8d  %8d  %8d  0   0  25   1995   10.00   2.50  2.50  0.1/'
        np.savetxt(ofile, [[int(id)]*6], fmt=fmt)
        
    with open(f'{new_dir}/ieSite.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/site/%d.sit"'
        np.savetxt(ofile, [[row['OBJECTID'], row['base']]], fmt=fmt)

    with open(f'{new_dir}/ieSllist.DAT', 'w') as ofile:
        # fmt = '%8d    "../../common_inputfiles/soils/%d.SOL"' 
        fmt = '%8d    "/gpfs/data1/cmongp/CMS/national_simulations/common_inputfiles/soils/%d.SOL"' 
        np.savetxt(ofile, [[row['OBJECTID'], row['ssu']]], fmt=fmt)

    with open(f'{new_dir}/ieWedlst.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/daily/%d.DLY"'  
        np.savetxt(ofile, [[row['OBJECTID'], row['dly']]], fmt=fmt)

    with open(f'{new_dir}/ieWealst.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/monthly/%d.INP"   %.2f   %.2f  NB            XXXX'  
        np.savetxt(ofile, [[row['OBJECTID'], row['dly'], row['x'], row['y']]], fmt=fmt)
    
    with open(f'{new_dir}/ieOplist.DAT', 'w') as ofile:
        fmt = '%8d    "../../common_inputfiles/OPC/CropRot_%d.OPC"'  
        np.savetxt(ofile, [[row['OBJECTID'], row['rotID']]], fmt=fmt)
    
    # Run the simulation from the new directory
    os.chdir(new_dir)
    command = f'nohup ./EPIC1102Versions_20201015 &> {opt.base_dir}/log/{id}.out'
    message = subprocess.Popen(command, shell=True).wait()
    
    #check for error
    with open(f'{opt.base_dir}/log/{id}.out', 'r') as file:
        lines = file.readlines()
        last_line = lines[-1]  # Get the last line
        if last_line.startswith('EPIC'):
            # Save the id into a file
            with open(f'{opt.base_dir}/saved_ids.txt', 'a') as id_file: 
                id_file.write(f'{id}\n') 

    # Copy the id.ACY and id.ACM files to output dir
    if os.path.exists(os.path.join(new_dir, f'{id}.ACY')):
        shutil.copy(os.path.join(new_dir, f'{id}.ACY'), output_dir)
    if os.path.exists(os.path.join(new_dir, f'{id}.ACM')):
        shutil.copy(os.path.join(new_dir, f'{id}.ACM'), output_dir)
    if os.path.exists(os.path.join(new_dir, f'{id}.ACO')):
        shutil.copy(os.path.join(new_dir, f'{id}.ACO'), output_dir)
    
    # Delete the whole new directory
    os.chdir(opt.base_dir)
    shutil.rmtree(new_dir)

# %%
# process_model({'OBJECTID': 11871139, 'problty': 100.0, 'rotat': 'Continuous Winter wheat', 'rotID': 6.0, 'x': -97.48982658274372, 'y': 36.39636614597452, 'slope': 0.3059178, 'ele': 338, 'ssu': 382525, 'base': 2054239, 'dly': 400064329, 'id': 192069, 'mukey': 382526.0, 'sl_length': 68, 'slope_steep': 0.0, 'nldas_id': 1516})
if not os.path.exists(os.path.join(opt.base_dir, 'out')):
    os.mkdir(os.path.join(opt.base_dir, 'out'))
if not os.path.exists(os.path.join(opt.base_dir, 'log')):
    os.mkdir(os.path.join(opt.base_dir, 'log'))

# %%
parallel_executor(process_model, df_ls, max_workers = opt.num_cores)

# %%
if os.path.exists(os.path.join(opt.base_dir, 'saved_ids.txt')):
    # Take care of failed EPICRunIDS
    failed = pd.read_csv(os.path.join(opt.base_dir, 'saved_ids.txt'))
    EPIC_csv.set_index('OBJECTID', inplace = True)
    EPIC_csv_failed = EPIC_csv.loc[failed.values.flatten()]
    failed_soilids = list(set(EPIC_csv_failed['ssu']))
    
    soil_info_master = pd.read_csv(opt.soil_csv)
    soil_info_master.set_index('band_1', inplace=True)
    valid_soil_ids = soil_info_master.loc[set(soil_info_master.index).difference(failed_soilids)]
    invalid_soil_ids = soil_info_master.loc[failed_soilids]
    inds = find_nearest(invalid_soil_ids, valid_soil_ids, metric = 'minkowski', k = 1)
    invalid_soil_ids['nearest'] = (valid_soil_ids.index.values)[inds]
    soil_info_master.loc[invalid_soil_ids.index.values, 'nearest'] = invalid_soil_ids['nearest'].values
    # soil_info_master.to_csv('/gpfs/data1/cmongp/Bharath/ks_ok_soils.csv')

    EPIC_csv_failed['ssu'] = EPIC_csv_failed['ssu'].apply(lambda x: soil_info_master.loc[int(x), 'nearest'])
    EPIC_csv_failed.to_csv(os.path.join(opt.base_dir, 'failing_ids.csv'))
    EPIC_csv_failed = pd.read_csv(os.path.join(opt.base_dir, 'failing_ids.csv'))

    with open(os.path.join(opt.base_dir, 'failed_soil_ids.txt'), 'w') as f:
        f.write('\n'.join([str(s) for s in failed_soilids]))
    # pd.DataFrame(failed_soilids).to_csv('failing_soil_ids.csv', index = False)

    df_ls = EPIC_csv_failed.to_dict('records')
    parallel_executor(process_model, df_ls, max_workers = opt.num_cores)


