# geo_epic/simulation/epic_model.py
from .field import Field
import os
import shutil
import numpy as np
import subprocess
from geo_epic.io.inputs import DLY

class EpicModel:
            
    def __init__(self, path):
        """
        Initializes an EpicModel object with the given path.
        
        Parameters:
        path (str): Path to the EPIC model directory.
        """
        self.path = path
        self.parent_folder = os.path.dirname(path)
        self.start_year = None
        self.duration = None
        self.output_types = []
        self.fid = 1
        self.output_files = {}
        self.log_file = ''

    def setup(self, start_year, duration):
        """
        Sets up the model with the given start year and duration.
        
        Parameters:
        start_year (int): The start year for the model simulation.
        duration (int): The duration of the model simulation in years.
        """
        self.start_year = start_year
        self.duration = duration

    def set_output_types(self, output_types):
        """
        Sets the types of output the model should generate.
        
        Parameters:
        output_types (list): A list of output types to generate.
        """
        self.output_types = output_types

    def get_model_info(self):
        """
        Returns the model configuration details.
        
        Returns:
        dict: A dictionary containing the model configuration details.
        """
        return {
            'path': self.path,
            'start_year': self.start_year,
            'duration': self.duration,
            'output_types': self.output_types
        }
    
    def copy_input_file(self, folder_name, input_file):
        input_folder = os.path.join(self.parent_folder, folder_name)
        os.makedirs(input_folder, exist_ok=True)
        shutil.copy(input_file, input_folder)
        
    def write_list_files(self, field):
        
        with open(f'{self.parent_folder}/EPICRUN.DAT', 'w') as ofile:
            fmt = '%8d %8d %8d 0 1 %8d  %8d  %8d  0   0  %2d   %4d   10.00   2.50  2.50  0.1/'
            np.savetxt(ofile, [[int(self.fid)]*6 + [self.duration, self.start_year]], fmt=fmt)
            
        with open(f'{self.parent_folder}/ieSite.DAT', 'w') as ofile:
            site_src = os.path.join(self.parent_folder, 'site')
            site_file_name = os.path.basename(field.sit)
            fmt = '%8d    "%s/%s"\n'%(self.fid, site_src, site_file_name)
            ofile.write(fmt)

        with open(f'{self.parent_folder}/ieSllist.DAT', 'w') as ofile:
            soil_src = os.path.join(self.parent_folder, 'soil')
            soil_file_name = os.path.basename(field.sol)
            fmt = '%8d    "%s/%s"\n'%(self.fid, soil_src, soil_file_name)  
            ofile.write(fmt)

        with open(f'{self.parent_folder}/ieWedlst.DAT', 'w') as ofile:
            weather_folder = os.path.join(self.parent_folder, 'weather')
            weather_file_name = os.path.basename(field.dly)
            fmt = '%8d    "%s/%s"\n'%(self.fid, weather_folder, weather_file_name)  
            ofile.write(fmt)

        with open(f'{self.parent_folder}/ieWealst.DAT', 'w') as ofile:
            weather_folder = os.path.join(self.parent_folder, 'weather')
            monthly_file_name = f'{self.fid}.INP'
            fmt = '%8d    "%s/%s"   %.2f   %.2f  NB            XXXX\n'%(self.fid,weather_folder, monthly_file_name,-95.71 , 37.09 ) # long and lat are center of USA
            ofile.write(fmt)
        
        with open(f'{self.parent_folder}/ieOplist.DAT', 'w') as ofile:
            opc_folder = os.path.join(self.parent_folder, 'opc')
            opc_file_name = os.path.basename(field.opc)
            fmt = '%8d    "%s/%s"\n'%(self.fid, opc_folder, opc_file_name)
            ofile.write(fmt)
        
    def save_monthly(self,field):
        dly_file = DLY.load(field.dly)
        monthly_file_loc = os.path.join(self.parent_folder, 'weather',f'{self.fid}.INP')
        dly_file.to_monthly(monthly_file_loc)
        
    def run(self, field):
        if not isinstance(field, Field):
            raise TypeError("field parameter must be an instance of Field class")
        
        self.copy_input_file('opc',field.opc)
        self.copy_input_file('weather',field.dly)
        self.copy_input_file('site',field.sit)
        self.copy_input_file('soil',field.sol)
        
        self.save_monthly(field)
        
        self.write_mapping_files(field)
        
        log_dir = os.path.join(self.parent_folder,'logs')
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = f'{log_dir}/{self.fid}.txt'
        
        os.chdir(self.parent_folder)
        command = f'{self.path}'
        result = subprocess.run(command, capture_output=True, text=True)

        with open(self.log_file, 'w') as file:
            file.write(result.stdout)
        
        for output_type in self.output_types:
            output_file_path = os.path.join(self.parent_folder, f'{self.fid}.{output_type}')
            self.output_files[output_type] = output_file_path
        
    def get_output_file(self, output_name):
        """
        Returns the path to the specified output file.
        
        Parameters:
        output_name (str): The name of the output file to retrieve.
        
        Returns:
        str: The path to the output file.
        """
        return self.output_files.get(output_name, None)
    
    def get_log_file(self):
        return self.log_file
        
    

# Example usage:
# model = EpicModel(path='./model/EPIC2301dt20230820')
# model.setup(start_year=2014, duration=10)
# model.set_output_types(['ACY', 'DGN'])
