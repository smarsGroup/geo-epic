import os
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime

class DLY(pd.DataFrame):
    @classmethod
    def load(cls, path):
        """
        Load data from a DLY file into DataFrame.
        """
        path = str(path)
        if not path.endswith('.DLY'): path += '.DLY'
        data = pd.read_fwf(path, widths=[6, 4, 4, 6, 6, 6, 6, 6, 6], header=None)
        data.columns = ['year', 'month', 'day', 'srad', 'tmax', 'tmin', 'prcp', 'rh', 'ws']
        return cls(data)

    def validate(self, start_year, end_year):
        """
        Validate the DataFrame to ensure it contains a continuous range of dates 
        between start_year and end_year, without duplicates.
        """
        # Create the full date range
        date_range = pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-31', freq='D')
        expected_df = pd.DataFrame({
            'year': date_range.year,
            'month': date_range.month,
            'day': date_range.day
        })

        # Remove duplicate rows from the DataFrame
        self.drop_duplicates(subset=['year', 'month', 'day'], inplace=True)
        # Merge with expected dates to find any missing rows
        merged_df = pd.merge(expected_df, self, on=['year', 'month', 'day'], how='left')
        # Check for missing dates
        missing_dates = merged_df[merged_df.isnull().any(axis=1)][['year', 'month', 'day']]
        if not missing_dates.empty:
            print("Missing rows for the following dates:")
            print(missing_dates)
            return False
        return True

    def save(self, path):
        """
        Save DataFrame into a DLY file.
        """
        # Remove duplicate rows from the DataFrame
        self.drop_duplicates(subset=['year', 'month', 'day'], inplace=True)
        path = str(path)
        if not path.endswith('.DLY'): path += '.DLY'
        with open(path, 'w') as ofile:
            fmt = '%6d%4d%4d%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f'
            np.savetxt(ofile, self.values[:], fmt = fmt)
    
    
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
        