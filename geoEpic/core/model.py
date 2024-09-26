import os
import shutil
import subprocess
from glob import glob
import numpy as np
import pandas as pd
from geoEpic.io import ConfigParser


class EPICModel:
    """
    A model class to handle the setup and execution of the EPIC model simulations.

    Attributes:
        base_dir (str): The base directory for model runs.
        executable (str): Path to the executable model file.
        path (str): Directory path where the executable is located.
        executable_name (str): Name of the executable file.
        start_year (int): Starting year for the model simulation.
        duration (int): Duration of the model simulation.
        output_dir (str): Directory to store model outputs.
        log_dir (str): Directory to store logs.
    """

    def __init__(self, path):
        """
        Initialize an EPICModel instance with the path to the executable model.

        Args:
            path (str): Path to the executable model file.
        """
        self.base_dir = os.getcwd()
        self.executable = path
        self.path = os.path.dirname(self.executable)
        self.executable_name = os.path.basename(self.executable)
        self.start_year = 2014
        self.duration = 10
        self.output_dir = os.path.dirname(self.path)
        self.log_dir = os.path.dirname(self.path)
        self.output_types = ['ACY']
        subprocess.Popen(f'chmod +x {self.executable}', shell=True).wait()

        # Define the path to the RAM-backed filesystem
        self.shm_path = '/dev/shm'  # On Linux systems

        # Copy the model folder to /dev/shm during initialization
        self.model_shm_path = os.path.join(self.shm_path, 'EPICModel')
        if os.path.exists(self.model_shm_path):
            shutil.rmtree(self.model_shm_path)
        shutil.copytree(self.path, self.model_shm_path)

        # Update paths to point to the copied folder in /dev/shm
        self.executable = os.path.join(self.model_shm_path, self.executable_name)
        self.path = self.model_shm_path


    def setup(self, config):
        """
        Set up the model run configurations based on provided settings.

        Args:
            config (dict): Configuration dictionary containing model settings.
        """
        self.start_year = config.get('start_year', 2014)
        self.duration = config.get('duration', 10)
        self.output_dir = config.get('output_dir', self.output_dir)
        self.log_dir = config.get('log_dir', self.log_dir)
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)

    @classmethod
    def from_config(cls, config_path):
        """
        Create an EPICModel instance from a configuration path.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            EPICModel: A configured instance of the EPICModel.
        """
        config = ConfigParser(config_path)
        instance = cls(config['EPICModel'])
        instance.base_dir = config.dir
        instance.setup(config)
        instance.set_output_types(config['output_types'])
        return instance

    def set_output_types(self, output_types):
        """
        Set the model output types and update the model's print file to enable specified outputs.

        Args:
            output_types (list of str): List of output types to be enabled.
        """
        self.output_types = output_types
        print_file = os.path.join(self.path, 'PRNT0810.DAT')
        outputs_to_enable = ' '.join(output_types).lower().split()
        with open(print_file, 'r') as file:
            lines = file.readlines()

        exts = lines[49].replace('*', ' ').strip().split() + lines[50].replace('*', ' ').strip().split()
        toggles = lines[14].strip().split() + lines[15].strip().split()

        for i, ext in enumerate(exts):
            toggles[i] = '1' if ext in outputs_to_enable else '0'

        lines[14] = '   ' + '   '.join(toggles[:len(lines[14].strip().split())]) + '\n'
        lines[15] = '   ' + '   '.join(toggles[len(lines[14].strip().split()):]) + '\n'
        with open(print_file, 'w') as file:
            file.writelines(lines)

    def run(self, site):
        """
        Execute the model for the given site and manage outputs.

        Args:
            site (Site): A site instance containing site-specific configuration.
        """
        fid = site.site_id
        # Use the model folder in /dev/shm as the source
        source_dir = self.model_shm_path
        # Destination directory within /dev/shm for this site
        new_dir = os.path.join(self.shm_path, 'EPICRUNS', str(fid))

        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        shutil.copytree(source_dir, new_dir)
        os.chdir(new_dir)

        
        dly = site.get_dly()
        dly.save(fid)
        dly.to_monthly(fid)
        
        self.writeDATFiles(site)
        command = f'nohup ./{self.executable_name} > {os.path.join(self.log_dir, f"{fid}.out")} 2>&1'
        subprocess.Popen(command, shell=True).wait()
        self.handle_outputs(site, new_dir)
        os.remove(os.path.join(self.log_dir, f"{fid}.out"))
        os.chdir(self.base_dir)
        shutil.rmtree(new_dir)

    def handle_outputs(self, site, new_dir):
        """
        Check and manage the outputs generated by the model.

        Args:
            site (Site): The site for which the model was run.
            fid (str): Field identifier for the site.
            new_dir (str): Directory where the model run was executed.
        """
        fid = site.site_id
        for out_type in self.output_types:
            out_path = f'{fid}.{out_type}'
            if not (os.path.exists(out_path) and os.path.getsize(out_path) > 0):
                os.chdir(self.base_dir)
                shutil.rmtree(new_dir)
                log_path = os.path.join(self.log_dir, f"{fid}.out")
                raise Exception(f"Output file ({out_type}) not found. Check {log_path} for details")
            site.outputs[out_type] = out_path
            
        # if self.output_dir:
        for out_type in self.output_types:
            out_path = f'{fid}.{out_type}'
            dst = os.path.join(self.output_dir, f'{fid}.{out_type}')
            shutil.move(out_path, dst)
            site.outputs[out_type] = dst
        # else:
        #     os.chdir(self.base_dir)

    def writeDATFiles(self, site):
        """
        Write configuration data files required for the model run for multiple sites.

        Args:
            sites (list): A list of Site objects for which data files are being prepared.
        """
        with open('./EPICRUN.DAT', 'w') as ofile:
            fmt = '%8d %8d %8d 0 1 %8d  %8d  %8d  0   0  %2d   %4d   10.00   2.50  2.50  0.1/'
            np.savetxt(ofile, [[int(site.site_id)]*6 + [self.duration, self.start_year]], fmt=fmt)
        
        with open('./ieSite.DAT', 'w') as ofile:
            fmt = '%8d    "%s"\n' % (site.site_id, site.sit_path)
            ofile.write(fmt)

        with open('./ieSllist.DAT', 'w') as ofile:
            fmt = '%8d    "%s"\n' % (site.site_id, site.sol_path)
            ofile.write(fmt)

        with open('./ieWedlst.DAT', 'w') as ofile:
            fmt = '%8d    "./%s.DLY"\n' % (site.site_id, str(site.site_id))
            ofile.write(fmt)

        with open('./ieWealst.DAT', 'w') as ofile:
            fmt = '%8d    "./%s.INP"   %.2f   %.2f  NB            XXXX\n' % (site.site_id, str(site.site_id), site.lon, site.lat)
            ofile.write(fmt)
        
        with open('./ieOplist.DAT', 'w') as ofile:
            fmt = '%8d    "%s"\n' % (site.site_id, site.opc_path)
            ofile.write(fmt)

    def auto_irrigation(self, bir, efi=None, vimx=None, armn=None, armx=None):
        """
        Update the irrigation settings in the EPICCONT.DAT file.
        Only BIR is required. Other parameters will be updated only if they are not None.

        :param file_path: Path to the EPICCONT.DAT file
        :param bir: Water stress factor to trigger automatic irrigation (BIR) - required
        :param efi: Runoff volume/Volume irrigation water applied (EFI) - optional
        :param vimx: Maximum annual irrigation volume (VIMX) in mm - optional
        :param armn: Minimum single application volume (ARMN) in mm - optional
        :param armx: Maximum single application volume (ARMX) in mm - optional
        """
        file_path = os.path.join(self.path, 'EPICCONT.DAT')
        with open(file_path, 'r+') as file:
            lines = file.readlines()
            if len(lines) < 6:
                raise ValueError("File does not have enough lines to update irrigation parameters.")
            
            # Split existing line into list of values
            values = lines[4].split()
            # Update mandatory BIR and optional parameters if provided
            values[5] = f"{bir:6.2f}"
            if efi is not None:
                values[6] = f"{efi:6.2f}"
            if vimx is not None:
                values[7] = f"{vimx:6.2f}"
            if armn is not None:
                values[8] = f"{armn:6.2f}"
            if armx is not None:
                values[9] = f"{armx:6.2f}"
            
            # Join back into a single string
            lines[4] = '  ' + '  '.join([f"{float(v):6.2f}" for v in values]) + '\n'
            
            file.seek(0)
            file.writelines(lines)

    def auto_Nfertilization(self, bft0, fnp=None, fmx=None):
        """
        Update the nitrogen settings in the EPICCONT.DAT file.
        Only BFT0 is required. Other parameters will be updated only if they are not None.

        :param file_path: Path to the EPICCONT.DAT file
        :param bft0: Nitrogen stress factor to trigger auto fertilization (BFT0) - required
        :param fnp: Fertilizer application variable (FNP) - optional
        :param fmx: Maximum annual N fertilizer applied for a crop (FMX) - optional
        """
        file_path = os.path.join(self.path, 'EPICCONT.DAT')
        with open(file_path, 'r+') as file:
            lines = file.readlines()
            if len(lines) < 6:
                raise ValueError("File does not have enough lines to update nitrogen parameters.")
            
            # Split existing line into list of values
            values = lines[5].split()
            # Update mandatory BFT0 and optional parameters if provided
            values[0] = f"{bft0:6.2f}"
            if fnp is not None:
                values[1] = f"{fnp:6.2f}"
            if fmx is not None:
                values[2] = f"{fmx:6.2f}"
            
            # Join back into a single string
            lines[5] = '  ' + '  '.join([f"{float(v):6.2f}" for v in values]) + '\n'
            
            file.seek(0)
            file.writelines(lines)
