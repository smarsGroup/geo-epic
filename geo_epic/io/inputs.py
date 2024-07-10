import os
import numpy as np
import pandas as pd
from tqdm import tqdm
            
class DLY(pd.DataFrame):
    @classmethod
    def load(cls, path):
        """
        Load data from a DLY file into DataFrame.
        """
        if not path.endswith('.DLY'):
            raise ValueError("The path must end with '.DLY'")
        data = pd.read_fwf(path, widths=[6, 4, 4, 6, 6, 6, 6, 6, 6], header=None)
        data.columns = ['year', 'month', 'day', 'srad', 'tmax', 'tmin', 'prcp', 'rh', 'ws']
        return cls(data)

    def save(self, path):
        """
        Save DataFrame into a DLY file.
        """
        with open(f'{path}.DLY', 'w') as ofile:
            fmt = '%6d%4d%4d%6.2f%6.2f%6.2f%6.2f%6.2f%6.2f'
            np.savetxt(ofile, self.values[1:], fmt = fmt)
    
    def to_monthly(self, path):
        """
        Save as monthly file
        """
        if not path.endswith('.INP'):
            raise ValueError("The path must end with '.INP'")
        
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
        
        with open(path, 'w') as ofile:
            ofile.write('\n'.join(lines))
            
        return ss


class OPC(pd.DataFrame):
    _metadata = ['header', 'name', 'prms']
    @classmethod
    def load(cls, path):
        """
        Load data from an OPC file into DataFrame.
        """
        widths = [3, 3, 3, 5, 5, 5, 5, 8, 8, 8, 8, 8, 8, 8, 8]
        data = pd.read_fwf(path, widths=widths, skiprows=2, header = None)
        data = data.dropna().astype(float)
        # data = data[np.all(np.isfinite(data).all(axis = 1))]
        data.columns = ['Yid', 'Mn', 'Dy', 'CODE', 'TRAC', 'CRP', 'XMTU', 'OPV1', 'OPV2', 'OPV3', 
                        'OPV4', 'OPV5', 'OPV6', 'OPV7', 'OPV8']
        inst = cls(data)
        with open(path, 'r') as file:
            inst.header = [file.readline() for _ in range(2)]
        inst.name = path.split('/')[-1]#'OPC'
        return inst

    def save(self, path):
        """
        Save DataFrame into an OPC file.
        """
        with open(f'{path}/{self.name}', 'w') as ofile:
            ofile.write(''.join(self.header))
            fmt = '%3d%3d%3d%5d%5d%5d%5d%8.3f%8.2f%8.2f%8.3f%8.2f%8.2f%8.2f%8.2f'
            np.savetxt(ofile, self.values, fmt = fmt)

    
    def edit_plantation_info(self, month, day, fert):
        # Modify the Mn and Dy columns for rows where CODE is 2
        data.loc[data[data['CODE'] == 2].index[-1], ['Mn', 'Dy']] = [month, day]

        # Modify the Mn and Dy columns for the penultimate row where CODE is 71
        penultimate_index_71 = data[data['CODE'] == 71].index[-2]
        data.loc[penultimate_index_71, ['Mn', 'Dy']] = [month, day]
        data.loc[data[data['CODE'] == 71].index[-1], 'OPV1'] = r        
        

    def edit_nitrogen_rate(self, rate, year_id = 15):
        # Modify the OPV1 column for the penultimate row where CODE is 71
        if ((self['CODE'] == 71) & (self['Yid'] == year_id)).any():
            self.loc[(self['CODE'] == 71) & (self['Yid'] == year_id), 'OPV1'] = 0.2 if rate == 0 else rate
    
    def edit_nrates(self, nrates):
        for i, nrate in enumerate(nrates, start = 1):
            self.edit_nitrogen_rate(nrate, i)