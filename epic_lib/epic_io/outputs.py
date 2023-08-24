import os
import numpy as np
import pandas as pd

class ACY:
    def __init__(self, file_path):
        """
        Initialize the ACY object by reading from an ACY file.
        """
        self.name = os.path.basename(file_path)
        self.data = self._readACY(file_path)

    def _readACY(self, file_path):
        """
        Private method to read ACY data.
        """
        widths = [5, 5, 5] + [9] * 31 + [10] * 4
        data = pd.read_fwf(file_path, widths = widths, skiprows = 11)
        if data.empty: raise ValueError('Data is Empty')
        data.columns = ['YR', 'RT#', 'CPNM', 'YLDG', 'YLDF', 'WCYD', 'HI', 'BIOM', 'RW', 'YLN', 'YLP', 'YLC', 'FTN',
                        'FTP', 'FTK', 'IRGA', 'IRDL', 'WUEF', 'GSET', 'CAW', 'CRF', 'CQV', 'COST', 'COOP', 'RYLG',
                        'RYLF', 'PSTF', 'WS', 'NS', 'PS', 'KS', 'TS', 'AS', 'SS', 'PPOP', 'IPLD', 'IGMD', 'IHVD']
        return data

    def get_var(self, varname):
        """
        Extract variable from the ACY data.
        """
        var_data = self.data[['YR', varname]].copy()
        var_data = var_data.groupby('YR', as_index=False).max()
        var_data = var_data.reset_index().sort_values('YR')
        return var_data
        
        
class DWC:
    def __init__(self, file_path):
        """
        Initialize the DWC object by reading from a DWC file.
        """
        self.name = os.path.basename(file_path)
        self.data = self._readDWC(file_path)

    def _readDWC(self, file_path):
        """
        Private method to read DWC data.
        """
        widths = [5, 4, 4] + [9] * 14
        data = pd.read_fwf(file_path, widths = widths, skiprows = 11)
        if data.empty: raise ValueError('Data is Empty')
        data.columns = ['Y', 'M', 'D', 'PRCP', 'PET', 'ET', 'EP', 'Q', 'SSF', 'PRK',
                     'QDRN', 'IRGA', 'QIN', 'RZSW', 'WTBL', 'GWST', ' SW']
        data['Date'] = pd.to_datetime(data[['Y', 'M', 'D']].astype(str).agg('-'.join, axis=1))
        return data

    def get_var(self, varname):
        """
        Extract variable from the DWC data.
        """
        return self.data[['Date', varname]].copy()


class DGN:
    def __init__(self, file_path):
        """
        Initialize the DGN object by reading from a DGN file.
        """
        self.name = os.path.basename(file_path)
        self.data = self._readDGN(file_path)

    def _readDGN(self, file_path):
        """
        Private method to read DGN data.
        """
        widths = [5, 4, 4] + [12] * 55
        data = pd.read_fwf(file_path, widths=widths, skiprows=11)
        if data.empty: raise ValueError('Data is Empty')
        data.columns = ["Y", "M", "D", "PDSW", "RSPC", "NPPC", "NEEC", "PRCP", "SNOF", "SNOM",
                        "PET", "ET", "EP", "YON", "QNO3", "VNO3", "NMN", "GMN", "DN2O", "DN2",
                        "DN", "NFIX", "NITR", "AVOL", "NIMO", "USLE", "FNO", "CLCH", "CQV", "YOC",
                        "ZNH3", "ZNO3", "NO31", "PRK1", "LN31", "ALB", "HUI", "AJHI", "LAI", "BIOM",
                        "RW", "STL", "STD", "HI", "YLDX", "YLDF", "UNO3", "NPP", "NEE", "LSN", "LMN",
                        "BMN", "HSN", "HPN", "TWN", "PRKP", "WOC", "AWC"]
        data['Date'] = pd.to_datetime(data[['Y', 'M', 'D']].astype(str).agg('-'.join, axis=1))
        return data

    def get_var(self, varname):
        """
        Extract variable from the DGN data.
        """
        if varname == 'AGB':
            var_data = self.data[['Date']].copy()
            var_data['AGB'] = self.data['BIOM'] - self.data['RW']
        else:
            var_data = self.data[['Date', varname]].copy()
        
        return var_data


class DTP:
    def __init__(self, file_path):
        """
        Initialize the DTP object by reading from a DTP file.
        """
        self.name = os.path.basename(file_path)
        self.data = self._readDTP(file_path)

    def _readDTP(self, file_path):
        """
        Private method to read DTP data.
        """
        widths = [5, 4, 4] + [12] * 17
        data = pd.read_fwf(file_path, widths=widths, skiprows=13)
        if data.empty: raise ValueError('Data is Empty')
        data.columns = ["Y", "M", "D", 'DP', 'Tot'] + ['SW{}'.format(i) for i in range(1, 16)]
        data['Date'] = pd.to_datetime(data[['Y', 'M', 'D']].astype(str).agg('-'.join, axis=1))
        return data

    def get_var(self, varname):
        """
        Extract variable from the DTP data.
        """
        return self.data[['Date', varname]].copy()


class DCS:
    def __init__(self, file_path):
        """
        Initialize the DCS object by reading from a DCS file.
        """
        self.name = os.path.basename(file_path)
        self.data = self._readDCS(file_path)

    def _readDCS(self, file_path):
        """
        Private method to read DCS data.
        """
        widths = [5, 4, 4, 5, 8] + [10] * 35
        data = pd.read_fwf(file_path, widths=widths, skiprows=13)
        if data.empty: raise ValueError('Data is Empty')
        data.columns = ["Y", "M", "D", 'RT', 'CPNM', 'HUI', 'AJHI', 'LAI', 'BIOM', 'RW', 'STL',
                        'HI', 'YLDX', 'YLDF', 'UNO3', 'NPP', 'NEE', 'ET', 'WS', 'NS', 'PS', 'KS',
                        'TS', 'AS', 'SS'] + ['RW{}'.format(i) for i in range(1, 16)]
        data['Date'] = pd.to_datetime(data[['Y', 'M', 'D']].astype(str).agg('-'.join, axis=1))
        return data

    def get_var(self, varname):
        """
        Extract variable from the DCS data.
        """
        return self.data[['Date', varname]].copy()
    
    
class ACM:
    def __init__(self, file_path):
        """
        Initialize the ACM object by reading from an ACM file.
        """
        self.name = os.path.basename(file_path)
        self.data = self._readACM(file_path)

    def _readACM(self, file_path):
        """
        Private method to read ACM data.
        """
        widths = [5, 5, 5] + [9] * 24
        data = pd.read_fwf(file_path, widths=widths)
        if data.empty: raise ValueError('Data is Empty')

        data.columns = ["Y", "RT#", "PRCP", "ET_pot", "ET", "Q", "SSF", "PRK", "CVF", "MUSS", "YW", "GMN",
                        "NMN", "NFIX", "NITR", "AVOL", "DN", "YON", "QNO3", "SSFN", "PRKN", "MNP", "YP",
                        "QAP", "PRKP", "LIME", "OCPD", "TOC", "APBC", "TAP", "TNO3"]
        return data

    def get_var(self, varname):
        """
        Extract variable from the ACM data.
        """
        return self.data[[varname]].copy()