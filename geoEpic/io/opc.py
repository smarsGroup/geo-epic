import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
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
        start_year (int, optional): Start year for the OPC file. If not provided, it will be read from the file header.

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
        
        with open(path, 'r') as file:
            header = [file.readline() for _ in range(2)]
            if start_year is not None:
                start_year = start_year
            else:
                try:
                    start_year_line = header[0].strip().split(':')[1].strip()
                    start_year = int(start_year_line)
                except (IndexError, ValueError):
                    raise ValueError("Bad Input: start_year must be specified either in file or as param.")
            header[0] = header[0].split(':')[0].strip() + ' : ' + str(start_year) + '\n'
        
        data['Yr'] = data['Yid'].apply(lambda x: start_year + x - 1)
        
        data['date'] = pd.to_datetime(data[['Yr', 'Mn', 'Dy']].rename(
            columns={'Yr': 'year', 'Mn': 'month', 'Dy': 'day'}
        ))
        inst = cls(data)
        inst.header = header
        inst.start_year = start_year
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
            path = os.path.join(path, self.name)
        
        with open(path, 'w') as ofile:
            ofile.write(''.join(self.header))
            
            final_data = self[self['Yid'] >= 1]
            columns = ['Yid', 'Mn', 'Dy', 'CODE', 'TRAC', 'CRP', 'XMTU', 'OPV1', 'OPV2', 'OPV3',
                       'OPV4', 'OPV5', 'OPV6', 'OPV7', 'OPV8']
            fmt = '%3d%3d%3d%5d%5d%5d%5d%8.3f%8.2f%8.2f%8.3f%8.2f%8.2f%8.2f%8.2f'
            np.savetxt(ofile, final_data[columns].values, fmt=fmt)

    def auto_irrigation(self, on=True):
        """
        Set or unset auto-irrigation in the OPC file header.

        This method modifies the second line of the header to enable or disable
        auto-irrigation based on the input parameter.

        Parameters:
        on (bool): If True, sets auto-irrigation to 72 (enabled).
                   If False, sets auto-irrigation to 0 (disabled).
                   Defaults to True.
        """
        luc, _ = self.header[1][:4], self.header[1][4:]
        if on:
            self.header[1] = luc + '  72' + '\n'
        else: 
            self.header[1] = luc + '   0' + '\n'

    def edit_fertilizer_rate(self, rate, year=2020, month=None, day=None):
        """
        Edit the fertilizer rate for a given year.

        Parameters:
        rate (float): Fertilizer rate to be set.
        year (int, optional): Year for the fertilizer rate application. Defaults to 2020.
        month (int, optional): Month for the fertilizer rate application. If not provided, the first instance is changed.
        day (int, optional): Day for the fertilizer rate application. Defaults to None.
        """
        condition = (self['CODE'] == self.fertilizer_code) & (self['Yr'] == year)
        if month is not None and day is not None:
            condition &= (self['Mn'] == month) & (self['Dy'] == day)
        
        matching_rows = self[condition]
        if not matching_rows.empty:
            last_index = matching_rows.index[-1]
            self.at[last_index, 'OPV1'] = 0.2 if rate == 0 else rate



    def update_phu(self, dly, cropcom):
        """
        Update the OPV1 value with the calculated PHU from the DLY data for all plantation dates.

        Parameters:
        dly (DLY): DLY object containing weather data.
        cropcom (DataFrame): DataFrame containing crop code and TBS values.
        """
        # Convert DLY data to datetime format
        dly['date'] = pd.to_datetime(dly[['year', 'month', 'day']])
        
        # Ensure the cropcom DataFrame columns are of integer type
        cropcom['#'] = cropcom['#'].astype(int)
        cropcom['TBS'] = cropcom['TBS'].astype(float)

        for season in self.iter_seasons():
            crop_code = season['crop_code']
            plantation_date = season['plantation_date']
            harvest_date = season['harvest_date']

            # Get the TBS value
            tbs = cropcom.loc[cropcom['#'] == crop_code, 'TBS'].values[0]
            # Filter data between planting date (PD) and harvesting date (HD)
            dat1 = dly[(dly['date'] > plantation_date) & (dly['date'] < harvest_date)]

            # Calculate Heat Units (HU) and PHU
            HU = (0.5 * (dat1['tmax'] + dat1['tmin']) - tbs).clip(lower=0)
            # Update OPV1 with PHU
            self.loc[season['plantation_index'], 'OPV1'] = HU.sum()

    def iter_seasons(self, start_year=None, end_year=None):
        """
        Iterate over OPC data, yielding dictionaries containing information for each growing season.

        Parameters:
        start_year (int, optional): The starting year to consider. Defaults to None.
        end_year (int, optional): The ending year to consider. Defaults to None.

        Yields:
        dict: A dictionary containing:
            - plantation_date: The date of plantation
            - harvest_date: The date of harvest
            - crop_code: The crop code
            - operations: A subset of OPC rows for this season
            - plantation_index: The index of the plantation row
        """
        plantation_dates = self[self['CODE'].isin(self.plantation_codes)].sort_values('date')
        harvest_dates = self[self['CODE'].isin(self.harvest_codes)].sort_values('date')

        if start_year:
            plantation_dates = plantation_dates[plantation_dates['date'].dt.year >= start_year]
        if end_year:
            plantation_dates = plantation_dates[plantation_dates['date'].dt.year <= end_year]

        for _, plantation_row in plantation_dates.iterrows():
            crop_code = plantation_row['CRP']
            plantation_date = plantation_row['date']

            # Find the immediate harvest date after this plantation date
            harvest_rows = harvest_dates[
                (harvest_dates['date'] > plantation_date) & 
                (harvest_dates['CRP'] == crop_code)
            ]
            
            if harvest_rows.empty:
                continue  # Skip this season if no harvest date is found
            
            harvest_row = harvest_rows.iloc[0]
            harvest_date = harvest_row['date']

            # Get all operations between plantation and harvest
            operations = self[(self['date'] >= plantation_date) & (self['date'] <= harvest_date)]

            yield {
                'plantation_date': plantation_date,
                'harvest_date': harvest_date,
                'crop_code': crop_code,
                'operations': operations,
                'plantation_index': plantation_row.name
            }

            
    def get_plantation_date(self, year=None, crop_code=None):
        """
        Retrieve the plantation date(s) for a specific year and/or crop code.

        Parameters:
        year (int, optional): Year. Defaults to None.
        crop_code (int, optional): Crop code. Defaults to None.

        Returns:
        dict: A dictionary of crop codes and their plantation dates with row indices.
        """
        return self._get_date(year, self.plantation_codes, crop_code)

    def get_harvest_date(self, year=None, crop_code=None):
        """
        Retrieve the harvest date(s) for a specific year and/or crop code.

        Parameters:
        year (int, optional): Year. Defaults to None.
        crop_code (int, optional): Crop code. Defaults to None.
  
        Returns:
        dict: A dictionary of crop codes and their harvest dates with row indices.
        """
        return self._get_date(year, self.harvest_codes, crop_code)
        
    def _get_date(self, year, codes, crop_code=None):
        """
        Retrieve the date(s) for a specific year and/or code(s).

        Parameters:
        year_id (int, optional): Year identifier. Defaults to None.
        codes (list): List of codes to search for.
        crop_code (int, optional): Crop code. Defaults to None.

        Returns:
        dict: A nested dictionary of crop codes, their corresponding dates, and row indices.
        """
        result = {}
        
        query = self['CODE'].isin(codes)
        if year is not None:
            query &= (self['Yr'] == year)
        if crop_code is not None:
            query &= (self['CRP'] == crop_code)
        
        cur_rows = self[query]
            
        for _, row in cur_rows.iterrows():
            year = int(row['Yr'])
            month = int(row['Mn'])
            day = int(row['Dy'])
            crop = int(row['CRP'])
            try:
                date = datetime(year=year, month=month, day=day)
                result[crop] = {'date': date, 'index': row.name}
            except ValueError:
                print(f"Invalid date for {self.name}: Year {year}, Month {month}, Day {day}")
        
        return result
    
    def validate(self,duration):
        """
        Validate the OPC data to ensure it contains a continuous range of dates without duplicates.

        Parameters:
        duration (int): Duration of the simulation in years.

        Returns:
        bool: True if the data is valid, False otherwise.
        str: Error message if the data is invalid.
        """
        # Check if 'Yr' column contains a continuous range from 1 to duration
        years = self['Yid'].unique()
        # print(np.array_equal(years, np.arange(1, duration)))
        missing_years = set(range(1, duration + 1)) - set(years)
        if missing_years:
            return False, f"Missing the following years: {sorted(missing_years)}."
            # Check if 'date' column is always increasing
        if not self['date'].is_monotonic_increasing:
            return False, "The date is not always increasing."
        
        # Check if each year has at least one plantation code and one harvest code
        for year in range(1, duration + 1):
            year_data = self[self['Yid'] == year]
            if any(year_data['CRP'] == 9):
                continue
            if not any(year_data['CODE'].isin(self.plantation_codes)) and not any(year_data['CODE'].isin(self.harvest_codes)):
                return False, f"Year {year} does not contain any plantation or harvest codes"
        
        return True, ""
    
    def _adjust_pre_planting_operations(self, new_plant_date, crop_code):
        """
        Adjust dates for operations before planting for a specific year based on their index.

        Parameters:
        year_id (int): Year identifier.
        crop_code (int): Crop code.
        """
        plantation_dates = self.get_plantation_date(new_plant_date.year, crop_code)
        if crop_code in plantation_dates:
            plantation_date = plantation_dates[crop_code]['date']
            plantation_idx = plantation_dates[crop_code]['index']
            
            killer_code_indices = self[(self['Yr'] == new_plant_date.year) & (self['CODE'] == 41)].index
 
            pre_planting_ops = self[(self['Yr'] == new_plant_date.year) & (self['CRP'] == crop_code) & (self.index < plantation_idx)]
            
            killer_code_index = killer_code_indices[killer_code_indices < plantation_idx].max()
            
            if not pd.isna(killer_code_index):  # Ensure a valid killer code index was found
                # Filter pre_planting_ops to include only rows after killer_code_index
                pre_planting_ops = pre_planting_ops[pre_planting_ops.index > killer_code_index]
                
            for idx, row in pre_planting_ops.iterrows():
                month = int(self.at[idx, 'Mn'])
                day = int(self.at[idx, 'Dy'])
                cur_opr_date = datetime(new_plant_date.year, month, day)
                offset = plantation_date - cur_opr_date
                adjusted_date = new_plant_date - timedelta(days=offset.days)
                self.at[idx, 'Mn'] = adjusted_date.month
                self.at[idx, 'Dy'] = adjusted_date.day
        
    def _adjust_post_harvesting_operations(self, new_harvest_date, crop_code):
        """
        Adjust dates for operations after harvesting for a specific year based on their index.

        Parameters:
        year_id (int): Year identifier.
        crop_code (int): Crop code.
        """
        harvest_dates = self.get_harvest_date(new_harvest_date.year, crop_code)
        if crop_code in harvest_dates:
            harvest_date = harvest_dates[crop_code]['date']
            harvest_idx = harvest_dates[crop_code]['index']
            
            killer_code_indices = self[(self['Yr'] == new_harvest_date.year) & (self['CODE'] == 41)].index
 
            post_harvest_ops = self[(self['Yr'] == new_harvest_date.year) & (self['CRP'] == crop_code) & (self.index > harvest_idx)]

            killer_code_index = killer_code_indices[killer_code_indices > harvest_idx].min()
            
            if not pd.isna(killer_code_index):  # Ensure a valid killer code index was found
                # Filter pre_planting_ops to include only rows after killer_code_index
                post_harvest_ops = post_harvest_ops[post_harvest_ops.index <= killer_code_index]
            
            
            for idx, row in post_harvest_ops.iterrows():
                month = int(self.at[idx, 'Mn'])
                day = int(self.at[idx, 'Dy'])
                cur_opr_date = datetime(harvest_date.year, month, day)
                offset = cur_opr_date - harvest_date
                adjusted_date = new_harvest_date + timedelta(days=offset.days)
                self.at[idx, 'Mn'] = adjusted_date.month
                self.at[idx, 'Dy'] = adjusted_date.day
    
    def _stretch_middle_operations(self, new_planting_date, new_harvest_date, crop_code):
        plantation_dates = self.get_plantation_date(new_planting_date.year, crop_code)
        harvest_dates = self.get_harvest_date(new_harvest_date.year, crop_code)
        
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
                    year = int(row['Yr'])
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
        plantation_dates = self.get_plantation_date(year, crop_code)
            
        if crop_code in plantation_dates:
            harvest_dates = self.get_harvest_date(year, crop_code)
            new_planting_date = datetime(year,month,day)
            
            plantation_idx = plantation_dates[crop_code]['index']
            new_harvest_date = harvest_dates[crop_code]['date']
            self._stretch_middle_operations(new_planting_date, new_harvest_date, crop_code)
            self._adjust_pre_planting_operations(new_planting_date, crop_code)
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
        mask = (self['CODE'] == code) & (self['Yr'] == year)
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
        mask = (self['CODE'] == code) & (self['Yr'] == year)
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
            
    def edit_crop_season(self, new_planting_date=None, new_harvest_date=None, crop_code=None):
        """
        Edit the planting and/or harvest dates for a given year and crop.

        Parameters:
        year (int): Year.
        new_planting_date (datetime, optional): New planting date. If not provided, only harvest date will be updated.
        new_harvest_date (datetime, optional): New harvest date. If not provided, only planting date will be updated.
        crop_code (int, optional): Crop code. If not provided, changes the first crop found.
        """
        if new_planting_date is None and new_harvest_date is None:
            raise ValueError("At least one of new_planting_date or new_harvest_date must be provided.")


        plantation_dates = self.get_plantation_date(new_planting_date.year, crop_code)
        
        # Find the first crop if crop_code is not provided
        if crop_code is None:
            if plantation_dates:
                crop_code = next(iter(plantation_dates))
            else:
                print(f"No crops found for year {new_planting_date.year}")
                return
                # raise ValueError(f"No crops found for year {new_planting_date.year}")
        elif crop_code not in plantation_dates:
            return
        
        harvest_dates = self.get_harvest_date(new_harvest_date.year, crop_code)

        if not harvest_dates:
            print(f"No harvest operations found for crop {crop_code} in year {new_harvest_date.year}")
            return
            # raise ValueError(f"No harvest operations found for crop {crop_code} in year {new_harvest_date.year}")

        plantation_idx = plantation_dates[crop_code]['index']
        harvest_idx = harvest_dates[crop_code]['index']

        current_planting_date = plantation_dates[crop_code]['date']
        current_harvest_date = harvest_dates[crop_code]['date']

        # Use current dates if new dates are not provided
        new_planting_date = new_planting_date or current_planting_date
        new_harvest_date = new_harvest_date or current_harvest_date

        # Adjust operations
        self._stretch_middle_operations( new_planting_date, new_harvest_date, crop_code)
        if new_planting_date != current_planting_date:
            self._adjust_pre_planting_operations(new_planting_date, crop_code)
            self.loc[plantation_idx, ['Mn', 'Dy']] = [new_planting_date.month, new_planting_date.day]
        if new_harvest_date != current_harvest_date:
            self._adjust_post_harvesting_operations(new_harvest_date, crop_code)
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
        # if second_opc_copy['Yid'].min() != 0:
        #     second_opc_copy['Yid'] -= second_opc_copy['Yid'].min() - 1
        second_opc_copy['Yid'] += last_yid
        # Combine data
        combined_data = pd.concat([self, second_opc_copy], ignore_index=True)
        # Create new OPC instance
        combined_opc = OPC(combined_data)
        combined_opc.header = self.header
        combined_opc.start_year = self.start_year
        combined_opc.name = self.name
        combined_opc['Yr'] = combined_opc['Yid'].apply(lambda x: self.start_year + x - 1)
        combined_opc['date'] = pd.to_datetime(combined_opc[['Yr', 'Mn', 'Dy']].rename(
            columns={'Yr': 'year', 'Mn': 'month', 'Dy': 'day'}
        ))
        
        return combined_opc
