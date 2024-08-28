import os
import shutil
import subprocess
from glob import glob
import numpy as np
import pandas as pd
from geoEpic.misc import ConfigParser, parallel_executor
from geoEpic.misc.utils import *


class EPICModel:
    def __init__(self, path):
        self.base_dir = os.getcwd()
        self.executable = path
        self.path = os.path.dirname(self.executable)
        # Make the model executable
        subprocess.Popen(f'chmod +x {self.executable}', shell=True).wait()
        # Model run options
        self.start_year = 2014
        self.duration = 10
        self.output_dir = None
        self.log_dir = './'
    
    def setup(self, config):
        self.start_year = config.get('start_year', 2014) 
        self.duration = config.get('duration', 10)
        self.output_dir = config.get('output_dir', self.output_dir) 
        self.log_dir = config.get('log_dir', self.log_dir)
        # Ensure output and log directories exist
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)
    
    @classmethod
    def from_config(cls, config_path):
        config = ConfigParser(config_path)
        instance = cls(config['EPICModel'])
        instance.base_dir = config.dir
        instance.setup(config)
        instance.set_output_types(config['output_types'])
        return instance

    def set_output_types(self, output_types):
        self.output_types = output_types
        print_file = os.path.join(self.path, 'PRNT0810.DAT')
        outputs_to_enable = ' '.join(output_types).lower().split()

        # Read all lines from the file
        with open(print_file, 'r') as file:
            lines = file.readlines()

        # Extract and process lines containing extensions
        exts_1 = lines[49].replace('*', ' ').strip().split()  # Line 50, zero-based index
        exts_2 = lines[50].replace('*', ' ').strip().split()  # Line 51, zero-based index

        # Get the original toggle lines
        toggle_line_1 = lines[14].strip().split()  # Line 15, zero-based index
        toggle_line_2 = lines[15].strip().split()  # Line 16, zero-based index

        # Prepare full lists of extensions and toggles
        exts = exts_1 + exts_2
        toggles = toggle_line_1 + toggle_line_2

        # Set toggles based on whether the extension is in the outputs_to_enable list
        for i, ext in enumerate(exts):
            toggles[i] = '1' if ext.lower() in outputs_to_enable else '0'

        # Split the combined toggles back into two parts
        new_toggle_line_1 = ''.join(toggles[:len(toggle_line_1)])
        new_toggle_line_2 = ''.join(toggles[len(toggle_line_1):])

        # Replace the old lines with the new ones in the list of lines
        lines[14] = new_toggle_line_1 + '\n'
        lines[15] = new_toggle_line_2 + '\n'

        # Write the modified lines back to the file
        with open(print_file, 'w') as file:
            file.writelines(lines)

    def run(self, site):
        # Assumes 'row' is a dictionary containing FieldID, x, y, and other needed keys
        fid = site.site_id
        new_dir = os.path.join(self.base_dir, 'EPICRuns', str(fid))
    
        # Delete the new directory if it exists and create a new one
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        shutil.copytree(self.model_dir, new_dir)
        os.chdir(new_dir)

        dly = site.get_dly()
        dly.save(fid)
        dly.to_monthly(fid)
        
        self.writeDATFiles(site)

        # Run the model and handle outputs
        command = f'nohup ./{self.executable} > {os.path.join(self.log_dir, f"{fid}.out")} 2>&1'
        subprocess.Popen(command, shell=True).wait()

        # Check and move output files
        for out_type in self.output_types:
            out_path = f'{fid}.{out_type}'
            if not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
                os.chdir(self.base_dir)
                shutil.rmtree(new_dir)
                raise Exception(f"Output file ({out_type}) not found. \n Check {os.path.join(self.log_dir, f"{fid}.out")} for details")
            site.outputs[out_type] = out_path
            
        if self.output_dir is not None:
            for out_type in self.output_types:
                out_path = f'{fid}.{out_type}'
                dst = os.path.join(self.output_dir, f'{fid}.{out_type}')
                shutil.move(out_path, dst)
                site.outputs[out_type] = dst
            os.remove(os.path.join(self.log_dir, f"{fid}.out"))
            os.chdir(self.base_dir)
            shutil.rmtree(new_dir)
        else:
            os.chdir(self.base_dir)

    def writeDATFiles(self, site):
        fid = site.site_id
        with open(f'./EPICRUN.DAT', 'w') as ofile:
            fmt = '%8d %8d %8d 0 1 %8d  %8d  %8d  0   0  %2d   %4d   10.00   2.50  2.50  0.1/'
            np.savetxt(ofile, [[int(fid)]*6 + [self.duration, self.start_year]], fmt=fmt)
            
        with open(f'./ieSite.DAT', 'w') as ofile:
            fmt = '%8d    "%s"\n'%(fid, site.sit_path)
            ofile.write(fmt)

        with open(f'./ieSllist.DAT', 'w') as ofile:
            fmt = '%8d    "%s"\n'%(fid, site.sol_path)  
            ofile.write(fmt)

        with open(f'./ieWedlst.DAT', 'w') as ofile:
            fmt = '%8d    "./%s.DLY"\n'%(str(fid))  
            ofile.write(fmt)

        with open(f'./ieWealst.DAT', 'w') as ofile:
            fmt = '%8d    "./%s.INP"   %.2f   %.2f  NB            XXXX\n'%(fid, str(fid), site.lon, site.lat)
            ofile.write(fmt)
        
        with open(f'./ieOplist.DAT', 'w') as ofile:
            fmt = '%8d    "%s"\n'%(fid, site.opc_path)
            ofile.write(fmt)
