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
        data = pd.read_fwf(f'{path}.DLY', widths=[6, 4, 4, 6, 6, 6, 6, 6, 6], header=None)
        data.columns = ['year', 'month', 'day', 'srad', 'tmax', 'tmin', 'prcp', 'rh', 'ws']
        return cls(data)

    def save(self, path):
        """
        Save DataFrame into a DLY file.
        """
        with open(f'{path}.DLY', 'w') as ofile:
            fmt = '%6d%4d%4d%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f'
            np.savetxt(ofile, self.values[1:], fmt = fmt)
    
    def set_start_date(self,start_date):
        start_date_pd = pd.to_datetime('1990-1')
        ref_year = start_date_pd.year
        ref_month = start_date_pd.month
        ref_day = start_date_pd.day

        # Create a boolean mask for rows where the date is greater than the reference date
        mask = (self['year'] >= ref_year) | \
            ((self['year'] == ref_year) & (self['month'] >= ref_month)) | \
            ((self['year'] == ref_year) & (self['month'] == ref_month) & (self['day'] >= ref_day))

        # Filter the DataFrame using the mask
        self= self[mask]
    
    def to_monthly(self, path):
        """
        Save as monthly file
        """
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
        
        with open(f'{path}.INP', 'w') as ofile:
            ofile.write('\n'.join(lines))
            
        return ss


class OPC(pd.DataFrame):
    _metadata = ['header', 'name', 'prms', 'start_year']

    @classmethod
    def load(cls, path):
        """
        Load data from an OPC file into DataFrame.
        
        Parameters:
        path (str): Path to the OPC file.

        Returns:
        OPC: An instance of the OPC class containing the loaded data.
        """
        widths = [3, 3, 3, 5, 5, 5, 5, 8, 8, 8, 8, 8, 8, 8, 8]
        data = pd.read_fwf(path, widths=widths, skiprows=2, header=None)
        data = data.dropna().astype(float)
        data.columns = ['Yid', 'Mn', 'Dy', 'CODE', 'TRAC', 'CRP', 'XMTU', 'OPV1', 'OPV2', 'OPV3',
                        'OPV4', 'OPV5', 'OPV6', 'OPV7', 'OPV8']
        inst = cls(data)
        with open(path, 'r') as file:
            inst.header = [file.readline() for _ in range(2)]
            try:
                start_year_line = inst.header[0].strip().split(':')[1].strip()
                inst.start_year = int(start_year_line)
            except (IndexError, ValueError):
                inst.start_year = 2006  # Default start year
                inst.header[0] = inst.header[0].strip() + ' : ' + str(inst.start_year) + '\n'

        inst.name = path.split('/')[-1]
        return inst

    def save(self, path):
        """
        Save DataFrame into an OPC file.

        Parameters:
        path (str): Path to save the OPC file.
        """
        with open(f'{path}/{self.name}', 'w') as ofile:
            ofile.write(''.join(self.header))
            fmt = '%3d%3d%3d%5d%5d%5d%5d%8.3f%8.2f%8.2f%8.3f%8.2f%8.2f%8.2f%8.2f'
            np.savetxt(ofile, self.values, fmt=fmt)

    def edit_plantation_date(self, year_id, month, day):
        """
        Edit the plantation date for a given year.

        Parameters:
        year_id (int): Year identifier.
        month (int): Month of plantation.
        day (int): Day of plantation.
        """
        plantation_code_3_idx = self[(self['CODE'] == 3) & (self['Yid'] == year_id)].index
        if not plantation_code_3_idx.empty:
            self.loc[plantation_code_3_idx, ['Mn', 'Dy']] = [month, day]
            return
        plantation_code_2_idx = self[(self['CODE'] == 2) & (self['Yid'] == year_id)].index
        if not plantation_code_2_idx.empty:
            self.loc[plantation_code_2_idx, ['Mn', 'Dy']] = [month, day]
            return

    def edit_nitrogen_rate(self, rate, year_id=15, month=None, day=None):
        """
        Edit the nitrogen rate for a given year.

        Parameters:
        rate (float): Nitrogen rate to be set.
        year_id (int, optional): Year identifier. Defaults to 15.
        month (int, optional): Month for the nitrogen rate application. Defaults to None.
        day (int, optional): Day for the nitrogen rate application. Defaults to None.
        """
        condition = (self['CODE'] == 71) & (self['Yid'] == year_id)
        if month is not None and day is not None:
            condition &= (self['Mn'] == month) & (self['Dy'] == day)
            if condition.any():
                last_index = self[condition].index[-1]
                self.loc[last_index, 'OPV1'] = 0.2 if rate == 0 else rate
        else:
            if condition.any():
                last_index = self[condition].index[-1]
                self.loc[last_index, 'OPV1'] = 0.2 if rate == 0 else rate

    def edit_harvest_date(self, year_id, month, day):
        """
        Edit the harvest date for a given year.

        Parameters:
        year_id (int): Year identifier.
        month (int): Month of harvest.
        day (int): Day of harvest.
        """
        harvest_code_650_idx = self[(self['CODE'] == 650) & (self['Yid'] == year_id)].index
        if not harvest_code_650_idx.empty:
            self.loc[harvest_code_650_idx, ['Mn', 'Dy']] = [month, day]

    def edit_nrates(self, nrates):
        """
        Edit the nitrogen rates for multiple years.

        Parameters:
        nrates (list): List of nitrogen rates to be set for each year.
        """
        for i, nrate in enumerate(nrates, start=1):
            self.edit_nitrogen_rate(nrate, i)

    def update_phu(self, dly, cropcom):
        """
        Update the OPV1 value with the calculated PHU from the DLY data for all years.

        Parameters:
        dly (DLY): DLY object containing weather data.
        cropcom (DataFrame): DataFrame containing crop code and TBS values.
        """
        # Convert DLY data to datetime format
        dly['date'] = pd.to_datetime(dly[['year', 'month', 'day']])
        
        # Ensure the cropcom DataFrame columns are of integer type
        cropcom['#'] = cropcom['#'].astype(int)
        cropcom['TBS'] = cropcom['TBS'].astype(float)

        years = self['Yid'].unique()
        for year_id in years:
            # Get plantation and harvest dates from the OPC file
            plantation_date = self[(self['CODE'].isin([2, 3])) & (self['Yid'] == year_id)].iloc[0]
            harvest_date = self[(self['CODE'] == 650) & (self['Yid'] == year_id)].iloc[0]
            
            pd_year = self.start_year + int(plantation_date['Yid']) - 1
            hd_year = self.start_year + int(harvest_date['Yid']) - 1

            pd_date = datetime(pd_year, int(plantation_date['Mn']), int(plantation_date['Dy']))
            hd_date = datetime(hd_year, int(harvest_date['Mn']), int(harvest_date['Dy']))

            # Get the crop code and TBS value
            crop_code = int(plantation_date['CRP'])
            tbs = cropcom.loc[cropcom['#'] == crop_code, 'TBS'].values[0]

            # Filter data between planting date (PD) and harvesting date (HD)
            dat1 = dly[(dly['date'] > pd_date) & (dly['date'] < hd_date)].copy()

            # Calculate Heat Units (HU) and PHU
            HU = (0.5 * (dat1['tmax'] + dat1['tmin'])) - tbs
            HU = HU.clip(lower=0)  # Replace negative values with 0
            phu = HU.sum()

            # Update OPV1 with PHU
            self.loc[(self['CODE'].isin([2, 3])) & (self['Yid'] == year_id), 'OPV1'] = phu
