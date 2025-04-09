import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from geoEpic.soil.sda import SoilDataAccess

class SOL:
    def __init__(self, soil_id=None, albedo=None, hydgrp=None, num_layers=None, layers_df=None):
        """
        Initialize the Soil class with soil properties.

        Args:
            soil_id (int): Soil ID (mukey).
            albedo (float): Soil albedo.
            hydgrp (str): Hydrological group.
            num_layers (int): Number of soil layers.
            layers_df (pd.DataFrame): DataFrame with soil properties.
                Columns: Layer_depth, Bulk_Density, Wilting_capacity, Field_Capacity,
                Sand_content, Silt_content, N_concen, pH, Sum_Bases, Organic_Carbon,
                Calcium_Carbonate, Cation_exchange, Course_Fragment, cnds, pkrz, rsd,
                Bulk_density_dry, psp, Saturated_conductivity
            num_layers_after_split (int): Number of layers after splitting by the EPIC model (TSLN in the SOL file format).
        """
        self.soil_id = soil_id
        self.albedo = albedo
        self.hydgrp = hydgrp
        self.num_layers = num_layers
        self.layers_df = layers_df
        self.num_layers_after_split = 10

    @classmethod
    def from_sda(cls, query):
        """
        Create a Soil object from Soil Data Access using a query.

        Args:
            query (int or str): Query string for SoilDataAccess. (mukey or WKT str)

        Returns:
            Soil: A new Soil object populated with data from SDA.
        """
        layers_df = SoilDataAccess.fetch_properties(query)
        
        soil_id = int(layers_df['mukey'].iloc[0])
        albedo = layers_df['albedo'].iloc[0]
        hydgrp = layers_df['hydgrp'].iloc[0]
        num_layers = len(layers_df)
        
        return cls(soil_id=soil_id, albedo=albedo, hydgrp=hydgrp, num_layers=num_layers, layers_df=layers_df)
    
    def save(self, filepath, template=None):
        """
        Save the soil data to a file using a template.

        Args:
            filepath (str): Path to save the soil file.
            template (list): Optional list of template lines.

        Raises:
            ValueError: If soil properties DataFrame is empty.
        """
        if self.layers_df is None:
            raise ValueError("Soil properties DataFrame is empty. Nothing to save.")
        
        if template is not None:
            template_lines = template.copy()
        else:
            with open(f'{os.path.dirname(__file__)}/template.SOL', 'r') as file:
                template_lines = file.readlines()
        
        template_lines[0] = f"ID: {self.soil_id}\n"
        hydgrp_conv = {'A': 1, 'B': 2, 'C': 3, 'D': 4}.get(self.hydgrp, 3)  # Default to 3 if not found
        template_lines[1] = '{:8.2f}{:8.2f}'.format(self.albedo, hydgrp_conv) + template_lines[1][16:]
        template_lines[2] = '{:8.2f}'.format(self.num_layers_after_split) + template_lines[2][8:]
        
        columns_order = [
            'Layer_depth', 'Bulk_Density', 'Wilting_capacity', 'Field_Capacity',
            'Sand_content', 'Silt_content', 'N_concen', 'pH', 'Sum_Bases',
            'Organic_Carbon', 'Calcium_Carbonate', 'Cation_exchange', 'Course_Fragment',
            'cnds', 'pkrz', 'rsd', 'Bulk_density_dry', 'psp', 'Saturated_conductivity',
        ]
        self.layers_df = self.layers_df[columns_order]
        self.layers_df = self.layers_df.sort_values(by='Layer_depth', ascending=True)
        self.layers_df = self.layers_df.reset_index(drop=True)
        self.layers_df = self.layers_df.fillna(0)
        vals = self.layers_df.values.T
        len_rows = len(vals)
        for i in range(len_rows):
            template_lines[3 + i] = ''.join([f'{val:8.2f}' for val in vals[i]]) + '\n'
        
        padding = ['{:8.2f}'.format(0) for _ in range(23)]
        for i in range(len_rows + 3, 51):
            template_lines[i] = ''.join(padding[:self.num_layers]) + '\n'
        
        horz = ['       A' for _ in range(23)]
        # Fill soil horizon to 'A'
        horz_row_ind = 47
        template[horz_row_ind] = ''.join(horz[:self.num_layers]) + '\n'
        
        with open(filepath, 'w+') as file:
            file.writelines(template_lines)
    
    def validate(self):
        hydgrp_conv = {'A': 1, 'B': 2, 'C': 3, 'D': 4}.get(self.hydgrp, 3)  # Default to 3 if not found
        if not (0 <= self.albedo <= 1):
            return False, "Albedo should be between 0 and 1."
        if hydgrp_conv not in [1, 2, 3, 4]:
            return False, "Hydrological group should be one of 'A', 'B', 'C', or 'D'."
        if not (1 <= self.num_layers <= 10):
            return False, "Number of layers should be between 1 and 10."
        # Validate each column based on the provided criteria
        for index, row in self.layers_df.iterrows():
            if not (0.01 <= row['Layer_depth'] <= 10.0):
                return False, f"Layer_depth should be between 0.01 and 10.0. Found {row['Layer_depth']} at index {index}."
            if not (0.5 <= row['Bulk_Density'] <= 2.5):
                return False, f"Bulk_Density should be between 0.5 and 2.5. Found {row['Bulk_Density']} at index {index}."
            if row['Wilting_capacity'] != 0 and not (0.01 <= row['Wilting_capacity'] <= 0.5):
                return False, f"Wilting_capacity should be between 0.01 and 0.5. Found {row['Wilting_capacity']} at index {index}."
            if not (0.1 <= row['Field_Capacity'] <= 0.9):
                return False, f"Field_Capacity should be between 0.1 and 0.9. Found {row['Field_Capacity']} at index {index}."
            if not (1 <= row['Sand_content'] <= 99):
                return False, f"Sand_content should be between 1 and 99. Found {row['Sand_content']} at index {index}."
            if not (1 <= row['Silt_content'] <= 99):
                return False, f"Silt_content should be between 1 and 99. Found {row['Silt_content']} at index {index}."
            if row['N_concen'] != 0 and not (100 <= row['N_concen'] <= 5000):
                return False, f"N_concen should be between 100 and 5000. Found {row['N_concen']} at index {index}."
            if not (3 <= row['pH'] <= 9):
                return False, f"pH should be between 3 and 9. Found {row['pH']} at index {index}."
            if row['Sum_Bases'] != 0 and not (0 <= row['Sum_Bases'] <= 150):
                return False, f"Sum_Bases should be between 0 and 150. Found {row['Sum_Bases']} at index {index}."
            if row['Organic_Carbon'] != 0 and not (0.1 <= row['Organic_Carbon'] <= 10):
                return False, f"Organic_Carbon should be between 0.1 and 10. Found {row['Organic_Carbon']} at index {index}."
            if row['Calcium_Carbonate'] != 0 and not (0 <= row['Calcium_Carbonate'] <= 99):
                return False, f"Calcium_Carbonate should be between 0 and 99. Found {row['Calcium_Carbonate']} at index {index}."
            if row['Cation_exchange'] != 0 and not (0 <= row['Cation_exchange'] <= 150):
                return False, f"Cation_exchange should be between 0 and 150. Found {row['Cation_exchange']} at index {index}."
            if row['Course_Fragment'] != 0 and not (0 <= row['Course_Fragment'] <= 99):
                return False, f"Course_Fragment should be between 0 and 99. Found {row['Course_Fragment']} at index {index}."
            if row['cnds'] != 0 and not (0.01 <= row['cnds'] <= 500):
                return False, f"cnds should be between 0.01 and 500. Found {row['cnds']} at index {index}."
            if row['pkrz'] != 0 and not (0 <= row['pkrz'] <= 20):
                return False, f"pkrz should be between 0 and 20. Found {row['pkrz']} at index {index}."
            if row['rsd'] != 0 and not (0 <= row['rsd'] <= 20):
                return False, f"rsd should be between 0 and 20. Found {row['rsd']} at index {index}."
            if row['Bulk_density_dry'] != 0 and not (0 <= row['Bulk_density_dry'] <= 2.0):
                return False, f"Bulk_density_dry should be between 0 and 2.0. Found {row['Bulk_density_dry']} at index {index}."
            if not (0 <= row['psp'] <= 0.9):
                return False, f"psp should be between 0 and 0.9. Found {row['psp']} at index {index}."
            if row['Saturated_conductivity'] != 0 and not (0.00001 <= row['Saturated_conductivity'] <= 100):
                return False, f"Saturated_conductivity should be between 0.00001 and 100. Found {row['Saturated_conductivity']} at index {index}." 

        return True, ""
        
    @classmethod
    def load(cls, filepath):
        """
        Load soil data from a file and return a Soil object.

        Args:
            filepath (str): Path to the soil file.

        Returns:
            Soil: A new Soil object populated with data from the file.
        """
        with open(filepath, 'r') as file:
            lines = file.readlines()
        
        try:
            soil_id = int(lines[0].strip().split(":")[1].strip())
        except (IndexError, ValueError):
            soil_id = ""
        
        albedo = float(lines[1][0:8].strip())
        hydgrp_conv = float(lines[1][8:16].strip())
        hydgrp_map = {1: 'A', 2: 'B', 3: 'C', 4: 'D'}
        hydgrp = hydgrp_map.get(int(hydgrp_conv), 'C')
        
        num_layers = len(lines[3].split())
        
        properties_data = [[] for _ in range(num_layers)]
        for i in range(3, 3 + 19):
            line = lines[i]
            values = [float(line[i:i+8]) for i in range(0, len(line.strip()), 8)]
            for j, value in enumerate(values):
                if j < num_layers:
                    properties_data[j].append(value)
        max_length = max(len(prop) for prop in properties_data)
        properties_data = [prop + [None] * (max_length - len(prop)) for prop in properties_data]
        
        columns = [
            'Layer_depth', 'Bulk_Density', 'Wilting_capacity', 'Field_Capacity',
            'Sand_content', 'Silt_content', 'N_concen', 'pH', 'Sum_Bases',
            'Organic_Carbon', 'Calcium_Carbonate', 'Cation_exchange', 'Course_Fragment',
            'cnds', 'pkrz', 'rsd', 'Bulk_density_dry', 'psp', 'Saturated_conductivity',
        ]
        layers_df = pd.DataFrame(properties_data, columns=columns)
        
        return cls(soil_id=soil_id, albedo=albedo, hydgrp=hydgrp, num_layers=num_layers, layers_df=layers_df)
    
   
class DLY(pd.DataFrame):
    @classmethod
    def load(cls, path):
        """
        Load data from a DLY file into DataFrame. If an additional column exists, include it.
        """
        path = str(path)
        if not path.endswith('.DLY'): 
            path += '.DLY'

        # Attempt to load with and without the additional column
        base_widths = [6, 4, 4, 6, 6, 6, 6, 6, 6]  # Original widths
        extended_widths = base_widths + [6]      # Include extra width for the additional column

        # Attempt to load with the additional column
        data = pd.read_fwf(path, widths=extended_widths, header=None)
        data.columns = ['year', 'month', 'day', 'srad', 'tmax', 'tmin', 'prcp', 'rh', 'ws', 'co2']
        if data["co2"].isnull().all():
            data.drop(columns=["co2"], inplace=True)
            
        return cls(data)

    def validate(self, start_year=None, end_year=None):
        """
        Validate the DataFrame to ensure it contains a continuous range of dates 
        between start_year and end_year, without duplicates and within valid ranges.
        """
        # Create the full date range
        date_range = pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-31', freq='D')
        expected_df = pd.DataFrame({
            'year': date_range.year,
            'month': date_range.month,
            'day': date_range.day
        })
        
        valid_ranges = {
            'month': (1, 12),
            'day': (1, 31),
            'srad': (0.01, 900),
            'tmin': (-50, 100),
            'tmax': (-50, 100),
            'prcp': (0, 900),
            'rh': (0, 1),
            'ws': (0, 900)
        }

        # Remove duplicate rows from the DataFrame
        self.drop_duplicates(subset=['year', 'month', 'day'], inplace=True)
        # Merge with expected dates to find any missing rows
        merged_df = pd.merge(expected_df, self, on=['year', 'month', 'day'], how='left')
        # Check for missing dates
        missing_dates = merged_df[merged_df.isnull().any(axis=1)][['year', 'month', 'day']]
        if not missing_dates.empty:
            message = f"Missing rows for the following dates: {missing_dates}"
            return False, message
        
        # Check for values out of valid ranges
        for column, (min_val, max_val) in valid_ranges.items():
            if not merged_df[column].between(min_val, max_val).all():
                invalid_rows = merged_df[~merged_df[column].between(min_val, max_val)][['year', 'month', 'day', column]]
                message = f"Values out of range for column '{column}': {invalid_rows}"
                return False, message
        
        return True, ""

    def save(self, path):
        """
        Save DataFrame into a DLY file.
        """
        # Remove duplicate rows from the DataFrame
        self.drop_duplicates(subset=['year', 'month', 'day'], inplace=True)

        path = str(path)
        if not path.endswith('.DLY'): 
            path += '.DLY'

        # Check if 'new_col' exists
        if 'co2' in self.columns:
            # Extended format string for additional column
            fmt = '%6d%4d%4d%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f'
            values = self[['year', 'month', 'day', 'srad', 'tmax', 'tmin', 'prcp', 'rh', 'ws', 'co2']].values
        else:
            # Original format string
            fmt = '%6d%4d%4d%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f'
            values = self[['year', 'month', 'day', 'srad', 'tmax', 'tmin', 'prcp', 'rh', 'ws']].values

        # Write to file
        with open(path, 'w') as ofile:
            np.savetxt(ofile, values, fmt=fmt)
    
    
    def to_monthly(self, path):
        """
        Save as monthly file
        """
        # Remove duplicate rows from the DataFrame
        self.drop_duplicates(subset=['year', 'month', 'day'], inplace=True)
        grouped = self.groupby('month')
        # Calculate mean for all columns except 'prcp'
        ss = grouped.mean()
        dayinmonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        ss['prcp'] = ss['prcp'] * dayinmonth
        # Standard deviations
        ss['sdtmx'] = grouped['tmax'].std()
        ss['sdtmn'] = grouped['tmin'].std()
        ss['sdrf'] = grouped['prcp'].std()
        # Additional calculations
        ss['dayp'] = grouped.apply(lambda x: (x['prcp'] > 0.5).sum() / len(x))
        ss['skrf'] = 3 * abs(ss['prcp'] - ss['prcp'].median()) / ss['sdrf']
        ss['prw1'] = grouped.apply(lambda x: np.sum(np.diff(x['prcp'] > 0.5) == -1) / len(x))
        # ss['prw2'] = grouped.apply(lambda x: np.sum((x['prcp'] > 0.5).shift().fillna(False) & (x['prcp'] > 0.5)) / len(x))
        ss['prw2'] = grouped.apply(lambda x: np.sum((x['prcp'].fillna(0) > 0.5).shift(fill_value=False) & (x['prcp'].fillna(0) > 0.5)) / len(x))
        ss['wi'] = 0
        # Reorder columns
        ss = ss[['tmax', 'tmin', 'prcp', 'srad', 'rh', 'ws', 'sdtmx', 'sdtmn', 'sdrf', 'dayp', 'skrf', 'prw1', 'prw2', 'wi']]
        ss.columns = ['OBMX', 'OBMN', 'RMO', 'OBSL', 'RH','UAVO', 'SDTMX', 'SDTMN','RST2', 'DAYP', 'RST3', 'PRW1', 'PRW2', 'WI']
        order = [0, 1, 6, 7, 2, 8, 10, 11, 12, 9, 13, 3, 4, 5]
        ss = ss[ss.columns[order]]
        values = np.float64(ss.T.values)
        
        lines = ['Monthly', ' ']
        fmt = "%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f%5s"
        for i, row in enumerate(values):
            line = fmt % tuple(row.tolist() + [str(ss.columns[i])])
            lines.append(line)
        
        path = str(path)
        if not path.endswith('.INP'): path += '.INP'
        with open(path, 'w') as ofile:
            ofile.write('\n'.join(lines))
        return ss


class SIT:
    def __init__(self, site_info = None):
        """
        Initialize the SiteFile class with a dictionary of site information.

        Parameters:
        site_info (dict): Dictionary containing site information (optional).
        """
        self.template = []
        self.site_info = {
            "ID": None,
            "lat": None,
            "lon": None,
            "elevation": None,
            "slope_length": None,
            "slope_steep": None
        }

        if site_info: self.site_info.update(site_info)

    @classmethod
    def load(cls, file_path):
        """
        Class method to load the .sit file and return a SiteFile instance.

        Parameters:
        file_path (str): Path to the .sit file.

        Returns:
        SiteFile: An instance of the SiteFile class with loaded data.
        """
        instance = cls()
        with open(file_path, 'r') as file:
            instance.template = file.readlines()

        # Extract information based on the template positions
        instance.site_info["ID"] = instance.template[2].split(":")[1].strip()
        instance.site_info["lat"] = float(instance.template[3][0:8].strip())
        instance.site_info["lon"] = float(instance.template[3][8:16].strip())
        instance.site_info["elevation"] = float(instance.template[3][16:24].strip())
        instance.site_info["slope_length"] = float(instance.template[4][48:56].strip())
        instance.site_info["slope_steep"] = float(instance.template[4][56:64].strip())

        return instance

    def save(self, output_dir):
        """
        Save the current site information to a .sit file.

        Parameters:
        output_dir (str): Directory where the .sit file will be saved, or the full path including the .sit extension.
        """
        if not self.site_info["ID"]:
            raise ValueError("Site ID is not set. Cannot write to file.")

        # Determine if output_dir already includes the .sit extension
        if output_dir.endswith('.sit'):
            output_file_path = output_dir
        else:
            output_file_path = os.path.join(output_dir, f"{self.site_info['ID']}.sit")
        
        # Modify the template lines or create a new template if not read from a file
        if not self.template:
            self.template = [''] * 7  # Assuming the template has at least 7 lines
        self.template[0] = 'Crop Simulations\n'
        self.template[1] = 'Prototype\n'
        self.template[2] = f'ID: {self.site_info["ID"]}\n'
        self.template[3] = f'{self.site_info["lat"]:8.2f}{self.site_info["lon"]:8.2f}{self.site_info["elevation"]:8.2f}{self.template[3][24:]}' if len(self.template) > 3 else ''
        self.template[4] = f'{self.template[4][:48]}{self.site_info["slope_length"]:8.2f}{self.site_info["slope_steep"]:8.2f}{self.template[4][64:]}' if len(self.template) > 4 else ''
        self.template[6] = '                                                   \n' if len(self.template) > 6 else ''
        
        # Write the modified template to the new file
        with open(output_file_path, 'w') as f:
            f.writelines(self.template)

        # print(f"File written to: {output_file_path}")
    
    def validate(self):
        """
        Validates the site information.
        This method checks if the site information provided in the `site_info` dictionary
        meets the specified criteria for latitude, longitude, elevation, slope steepness,
        and slope length.
        Returns:
            tuple: A tuple containing a boolean and a string. The boolean indicates whether
                   the validation was successful (True) or not (False). The string provides
                   a message describing the result of the validation.
        Validation Criteria:
            - Latitude should be between -90 and 90.
            - Longitude should be between -180 and 180.
            - Elevation should be between -200 and 8000.
            - Slope steepness should be between 0 and 1.
            - Slope length should be between 0 and 90.
        """
        
        if not (-90 <= self.site_info["lat"] <= 90):
            return False, "Latitude should be between -90 and 90."
        if not (-180 <= self.site_info["lon"] <= 180):
            return False, "Longitude should be between -180 and 180."
        if not (-200 <= self.site_info["elevation"] <= 8000):
            return False, "Elevation should be between -200 and 8000."
        if not (0 <= self.site_info["slope_steep"] <= 1):
            return False, "Slope steepness should be between 0 and 1."
        if not (0 <= self.site_info["slope_length"] <= 90):
            return False, "Slope length should be between 0 and 90."
        return True, ""
        