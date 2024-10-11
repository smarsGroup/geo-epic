import pandas as pd
import os
import numpy as np
from datetime import datetime,timedelta
from geoEpic.io import DLY

class OPC(pd.DataFrame):
    _metadata = ['header', 'name', 'prms', 'start_year']

    # Class attributes for codes
    plantation_codes = [2, 3, 4]
    harvest_codes = [650]
    fertilizer_code = 71

    @classmethod
    def load(cls, path, start_year=None):
        """
        Load data from an OPC file into DataFrame.
        
        Parameters:
        path (str): Path to the OPC file.

        Returns:
        OPC: An instance of the OPC class containing the loaded data.
        """
        path = str(path)
        if not path.endswith('.OPC'): 
            path += '.OPC'
        widths = [3, 3, 3, 5, 5, 5, 5, 8, 8, 8, 8, 8, 8, 8, 8]
        data = pd.read_fwf(path, widths=widths, skiprows=2, header=None)
        data = data.dropna().astype(float)
        data.columns = ['Yid', 'Mn', 'Dy', 'CODE', 'TRAC', 'CRP', 'XMTU', 'OPV1', 'OPV2', 'OPV3',
                        'OPV4', 'OPV5', 'OPV6', 'OPV7', 'OPV8']
        inst = cls(data)
        with open(path, 'r') as file:
            inst.header = [file.readline() for _ in range(2)]
            if start_year is not None:
                inst.start_year = start_year
            else:
                try:
                    start_year_line = inst.header[0].strip().split(':')[1].strip()
                    inst.start_year = int(start_year_line)
                except (IndexError, ValueError):
                    raise ValueError("Bad Input: start_year must be a specified either in file or as param.")
            inst.header[0] = inst.header[0].split(':')[0].strip() + ' : ' + str(inst.start_year) + '\n'
            
        inst.name = path.split('/')[-1]
        return inst

    def save(self, path):
        """
        Save DataFrame into an OPC file.

        Parameters:
        path (str): Path to save the OPC file.
        """
        # Check if the path is a directory
        if os.path.isdir(path):
            path = os.path.join(path,self.name)
    
        final_data = self[self['Yid']>=1]
        with open(f'{path}', 'w') as ofile:
            ofile.write(''.join(self.header))
            fmt = '%3d%3d%3d%5d%5d%5d%5d%8.3f%8.2f%8.2f%8.3f%8.2f%8.2f%8.2f%8.2f'
            np.savetxt(ofile, final_data.values, fmt=fmt)

    def auto_irrigation(self, on = True):
        luc, _ = self.header[1][:4], self.header[1][4:]
        if on:
            self.header[1] = luc + '  72' + '\n'
        else: 
            self.header[1] = luc + '   0' + '\n'

    def edit_fertilizer_rate(self, rate, year_id=15, month=None, day=None):
        """
        Edit the fertilizer rate for a given year.

        Parameters:
        rate (float): Fertilizer rate to be set.
        year_id (int, optional): Year identifier. Defaults to 15.
        month (int, optional): Month for the fertilizer rate application.  If not provided, the first instance is changed.
        day (int, optional): Day for the fertilizer rate application. Defaults to None.
        """
        condition = (self['CODE'] == self.fertilizer_code) & (self['Yid'] == year_id)
        if month is not None and day is not None:
            condition &= (self['Mn'] == month) & (self['Dy'] == day)
            if condition.any():
                last_index = self[condition].index[-1]
                self.loc[last_index, 'OPV1'] = 0.2 if rate == 0 else rate
        else:
            if condition.any():
                last_index = self[condition].index[-1]
                self.loc[last_index, 'OPV1'] = 0.2 if rate == 0 else rate

    def edit_nrates(self, nrates):
        """
        Edit the fertilizer rates for all years.

        Parameters:
        nrates (list): List of fertilizer rates to be set for each year.
        """
        for i, nrate in enumerate(nrates, start=1):
            self.edit_fertilizer_rate(nrate, i)

    def update_phu(self, dly, cropcom):
        """
        Update the OPV1 value with the calculated PHU from the DLY data for all years and crops.

        Parameters:
        dly (DLY): DLY object containing weather data.
        cropcom (DataFrame): DataFrame containing crop code and TBS values.
        """
        # Convert DLY data to datetime format
        dly['date'] = pd.to_datetime(dly[['year', 'month', 'day']])
        
        # Ensure the cropcom DataFrame columns are of integer type
        cropcom['#'] = cropcom['#'].astype(int)
        cropcom['TBS'] = cropcom['TBS'].astype(float)

        # Get all unique combinations of year_id and harvest codes
        harvest_combinations = self[self['CODE'].isin(self.harvest_codes)][['Yid', 'CRP']].drop_duplicates()

        for _, row in harvest_combinations.iterrows():
            year_id, crop_code = row['Yid'], row['CRP']

            # Get harvest date
            harvest_dates = self.get_harvest_date(year_id, crop_code)
            if not harvest_dates: continue
            harvest_date = list(harvest_dates.values())[0]['date']

            # Get plantation date (considering winter wheat)
            plantation_year_id = year_id - 1 if crop_code == 10 else year_id  # 10 is the code for winter wheat
            plantation_dates = self.get_plantation_date(plantation_year_id, crop_code)
            if not plantation_dates: continue
            plantation_date = list(plantation_dates.values())[0]['date']

            # Get the TBS value
            tbs = cropcom.loc[cropcom['#'] == crop_code, 'TBS'].values[0]
            # Filter data between planting date (PD) and harvesting date (HD)
            dat1 = dly[(dly['date'] > plantation_date) & (dly['date'] < harvest_date)].copy()
            # Calculate Heat Units (HU) and PHU
            HU = (0.5 * (dat1['tmax'] + dat1['tmin'])) - tbs
            HU = HU.clip(lower=0)  # Replace negative values with 0
            phu = HU.sum()

            # Update OPV1 with PHU
            plantation_row_index = list(plantation_dates.values())[0]['index']
            self.loc[plantation_row_index, 'OPV1'] = phu
            
    def get_plantation_date(self, year_id, crop_code=None):
        """
        Retrieve the plantation date(s) for a specific year.

        Parameters:
        year_id (int): Year identifier.
        crop_code (int, optional): Crop code. Defaults to None.

        Returns:
        dict: A dictionary of crop codes and their plantation dates with row indices.
        """
        return self._get_date(year_id, self.plantation_codes, crop_code)

    def get_harvest_date(self, year_id, crop_code=None):
        """
        Retrieve the harvest date(s) for a specific year.

        Parameters:
        year_id (int): Year identifier.
        crop_code (int, optional): Crop code. Defaults to None.

        Returns:
        dict: A dictionary of crop codes and their harvest dates with row indices.
        """
        return self._get_date(year_id, self.harvest_codes, crop_code)
        
    def _get_date(self, year_id, codes, crop_code=None):
        """
        Retrieve the date(s) for a specific year and code(s).

        Parameters:
        year_id (int): Year identifier.
        codes (list): List of codes to search for.
        crop_code (int, optional): Crop code. Defaults to None.

        Returns:
        dict: A nested dictionary of crop codes, their corresponding dates, and row indices.
        """
        result = {}
        
        if crop_code is None:
            cur_rows = self[(self['Yid'] == year_id) & (self['CODE'].isin(codes))]
        else:
            cur_rows = self[(self['Yid'] == year_id) & (self['CODE'].isin(codes)) & (self['CRP'] == crop_code)]
            
        for _, row in cur_rows.iterrows():
            year = year_id + self.start_year - 1
            month = int(row['Mn'])
            day = int(row['Dy'])
            crop = int(row['CRP'])
            try:
                date = datetime(year=year, month=month, day=day)
                result[crop] = {'date': date, 'index': row.name}
            except ValueError:
                print(f"Invalid date for {self.name}: Year {year_id}, Month {month}, Day {day}")
        
        return result
    
    def _adjust_pre_planting_operations(self, new_plant_date, year_id, crop_code):
        """
        Adjust dates for operations before planting for a specific year based on their index.

        Parameters:
        year_id (int): Year identifier.
        crop_code (int): Crop code.
        """
        plantation_dates = self.get_plantation_date(year_id, crop_code)
        if crop_code in plantation_dates:
            plantation_date = plantation_dates[crop_code]['date']
            plantation_idx = plantation_dates[crop_code]['index']
            
            pre_planting_ops = self[(self['Yid'] == year_id) & (self['CRP'] == crop_code) & (self.index < plantation_idx)]
            
            for idx, row in pre_planting_ops.iterrows():
                month = int(self.at[idx, 'Mn'])
                day = int(self.at[idx, 'Dy'])
                cur_opr_date = datetime(new_plant_date.year, month, day)
                offset = plantation_date - cur_opr_date
                adjusted_date = new_plant_date - timedelta(days=offset.days)
                self.at[idx, 'Mn'] = adjusted_date.month
                self.at[idx, 'Dy'] = adjusted_date.day
        
    def _adjust_post_harvesting_operations(self, new_harvest_date, year_id, crop_code):
        """
        Adjust dates for operations after harvesting for a specific year based on their index.

        Parameters:
        year_id (int): Year identifier.
        crop_code (int): Crop code.
        """
        harvest_dates = self.get_harvest_date(year_id, crop_code)
        if crop_code in harvest_dates:
            harvest_date = harvest_dates[crop_code]['date']
            harvest_idx = harvest_dates[crop_code]['index']
            
            post_harvest_ops = self[(self['Yid'] == year_id) & (self['CRP'] == crop_code) & (self.index > harvest_idx)]
            
            for idx, row in post_harvest_ops.iterrows():
                month = int(self.at[idx, 'Mn'])
                day = int(self.at[idx, 'Dy'])
                cur_opr_date = datetime(harvest_date.year, month, day)
                offset = cur_opr_date - harvest_date
                adjusted_date = new_harvest_date + timedelta(days=offset.days)
                self.at[idx, 'Mn'] = adjusted_date.month
                self.at[idx, 'Dy'] = adjusted_date.day
    
    def _stretch_middle_operations(self, year_id, new_planting_date, new_harvest_date, crop_code):
        plantation_dates = self.get_plantation_date(year_id, crop_code)
        harvest_dates = self.get_harvest_date(year_id, crop_code)
        
        if crop_code in plantation_dates and crop_code in harvest_dates:
            prev_plantation_date = plantation_dates[crop_code]['date']
            plantation_idx = plantation_dates[crop_code]['index']
            prev_harvest_date = harvest_dates[crop_code]['date']
            harvest_idx = harvest_dates[crop_code]['index']
            
            original_range = (prev_harvest_date - prev_plantation_date).days
            new_range = (new_harvest_date - new_planting_date).days
            # Process rows between start_index and end_index
            for idx in range(plantation_idx+1, harvest_idx):
                if idx in self.index:
                    row = self.loc[idx]
                    # Calculate the scale of the current date
                    year = int(row['Yid'])+self.start_year-1
                    row_date = datetime(year, int(row['Mn']),int(row['Dy']))
                    days_from_start = (row_date - prev_plantation_date).days
                    scale = days_from_start / original_range
                    # Calculate the new date
                    new_days_from_start = int(scale * new_range)
                    new_date = new_planting_date + timedelta(days=new_days_from_start)
                    # Update the DataFrame in place
                    self.at[idx, 'Mn'] = new_date.month
                    self.at[idx, 'Dy'] = new_date.day
        

    def edit_plantation_date(self, year, month, day, crop_code):
        """
        Edit the plantation date for a given year and crop.

        Parameters:
        year (int): Year.
        month (int): Month of plantation.
        day (int): Day of plantation.
        crop_code (int): Crop code.
        """
        year_id = year - self.start_year + 1
        plantation_dates = self.get_plantation_date(year_id, crop_code)
            
        if crop_code in plantation_dates:
            harvest_dates = self.get_harvest_date(year_id, crop_code)
            new_planting_date = datetime(year,month,day)
            
            plantation_idx = plantation_dates[crop_code]['index']
            new_harvest_date = harvest_dates[crop_code]['date']
            self._stretch_middle_operations(year_id, new_planting_date, new_harvest_date, crop_code)
            self._adjust_pre_planting_operations(new_planting_date, year_id, crop_code)
            self.loc[plantation_idx, ['Mn', 'Dy']] = [month, day]
            return
    
    def edit_operation_date(self, code, year, month, day, crop_code=None):
        """
        Edit the operation date for a given year.

        Parameters:
        code (str): Operation code.
        year (int): Year.
        month (int): Month of operation.
        day (int): Day of operation.
        crop_code (int, optional): Crop code.
        """
        year_id = year - self.start_year + 1
        mask = (self['CODE'] == code) & (self['Yid'] == year_id)
        if crop_code is not None:
            mask &= (self['CRP'] == crop_code)
        self.loc[mask, ['Mn', 'Dy']] = [month, day]
            
    def edit_operation_value(self, code, year, value, crop_code=None):
        """
        Edit the operation value for a given year.

        Parameters:
        code (str): Operation code.
        year (int): Year.
        value (float): New operation value.
        crop_code (int, optional): Crop code.
        """
        year_id = year - self.start_year + 1
        mask = (self['CODE'] == code) & (self['Yid'] == year_id)
        if crop_code is not None:
            mask &= (self['CRP'] == crop_code)
        self.loc[mask, 'OPV1'] = value

    def edit_harvest_date(self, year, month, day, crop_code):
        """
        Edit the harvest date for a given year.

        Parameters:
        year (int): Year.
        month (int): Month of harvest.
        day (int): Day of harvest.
        crop_code (int, optional): Crop code.
        """
        year_id = year - self.start_year + 1
        harvest_dates = self.get_harvest_date(year_id, crop_code)
        
        if crop_code in harvest_dates:
            plantation_dates = self.get_plantation_date(year_id, crop_code)
            new_harvest_date = datetime(year, month, day)
            harvest_idx = harvest_dates[crop_code]['index']
            new_planting_date = plantation_dates[crop_code]['date']
            self._stretch_middle_operations(year_id, new_planting_date, new_harvest_date, crop_code)
            self._adjust_post_harvesting_operations(new_harvest_date, year_id, crop_code)
            self.loc[harvest_idx, ['Mn', 'Dy']] = [month, day]
            return
            
    def edit_crop_dates(self, year, new_planting_date, new_harvest_date, crop_code=None):
        """
        Edit the planting and harvest dates for a given year and crop.

        Parameters:
        year (int): Year.
        new_planting_date (datetime): New planting date.
        new_harvest_date (datetime): New harvest date.
        crop_code (int, optional): Crop code. If not provided, changes the first crop found.
        """
        year_id = year - self.start_year + 1
        
        # Get current plantation dates
        plantation_dates = self.get_plantation_date(year_id, crop_code)

        # Find the first crop if crop_code is not provided
        if crop_code is None:
            if plantation_dates:
                crop_code = next(iter(plantation_dates))
            else:
                raise ValueError(f"No crops found for year {year}")
        elif crop_code not in plantation_dates:
            raise ValueError(f"No planting operation found for crop {crop_code} in year {year}")
        harvest_dates = self.get_harvest_date(year_id, crop_code)

        if not plantation_dates or not harvest_dates:
            raise ValueError(f"No planting or harvest operations found for crop {crop_code} in year {year}")

        plantation_idx = plantation_dates[crop_code]['index']
        harvest_idx = harvest_dates[crop_code]['index']

        # Adjust operations
        self._stretch_middle_operations(year_id, new_planting_date, new_harvest_date, crop_code)
        self._adjust_pre_planting_operations(new_planting_date, year_id, crop_code)
        self._adjust_post_harvesting_operations(new_harvest_date, year_id, crop_code)

        # Update planting date and harvest date
        self.loc[plantation_idx, ['Mn', 'Dy']] = [new_planting_date.month, new_planting_date.day]
        self.loc[harvest_idx, ['Mn', 'Dy']] = [new_harvest_date.month, new_harvest_date.day]
            
    def append(self, second_opc):
        """
        Append another OPC or DataFrame to the current OPC instance.
        Args:
            second_opc (pd.DataFrame or OPC): The data to append.
        Returns:
            OPC: A new OPC instance with combined data.
        Raises:
            ValueError: If second_opc is not a pandas DataFrame or OPC instance.
        """
        if not isinstance(second_opc, (pd.DataFrame, OPC)):
            raise ValueError("The 'second_opc' parameter must be a pandas DataFrame or OPC instance.")
        last_yid = self['Yid'].max()
        # Create a copy to avoid modifying the original data
        second_opc_copy = second_opc.copy()
        # Adjust Yid values
        if second_opc_copy['Yid'].min() != 0:
            second_opc_copy['Yid'] -= second_opc_copy['Yid'].min() - 1
        second_opc_copy['Yid'] += last_yid
        # Combine data
        combined_data = pd.concat([self, second_opc_copy], ignore_index=True)
        # Create new OPC instance
        combined_opc = OPC(combined_data)
        combined_opc.header = self.header
        combined_opc.start_year = self.start_year
        combined_opc.name = self.name
        return combined_opc
