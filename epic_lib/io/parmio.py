import pandas as pd
import numpy as np
from rpy2.robjects import r, pandas2ri
pandas2ri.activate()
import os

root_path = os.path.dirname(__file__)
script_path = os.path.join(root_path, 'ParmIO.R')
r.source(script_path)

class CropCom(pd.DataFrame):

    @classmethod
    def load(cls, path):
        """
        Load data from a file into DataFrame.
        """
        wd = [5, 5] + [8] * 58 + [50]
        data = pd.read_fwf(path + '/CROPCOM.DAT', widths=wd, skiprows=1)
        inst = cls(data)
        with open(path + '/CROPCOM.DAT', 'r') as file:
            inst.header = [file.readline() for _ in range(2)]
        inst.name = 'CROPCOM'
        inst.prms = None
        return inst

    @property
    def vals(self):
        cols = self.prms['Parm'].values
        return self.loc[0, cols]

    def save(self, path):
        """
        Save DataFrame into an OPC file.
        """
        with open(f'{path}/CROPCOM.DAT', 'w') as ofile:
            ofile.write(''.join(self.header))
            fmt = '%5d%5s' + '%8.2f'*11 + '%8.4f' + \
              '%8.2f'*5 + '%8.4f'*3 + '%8.2f'*6 + '%8.4f'*9 + \
              '%8.3f'*3 + '%8d' + '%8.2f'*18 + '%8.3f' + '  %s'
            np.savetxt(ofile, self.values, fmt = fmt)

    def parm_edit(self, values):
        cols = self.prms['Parm'].values
        values_split = np.split(values, self.split[:-1])
        for i, id in enumerate(self.crops):
            self.loc[self['#'] == id, cols] = values_split[i]

    def set_sensitive(self, df_paths, crops):
        prms = pd.read_csv(df_paths[0])
        for sl in df_paths[1:]:
            df_temp = pd.read_csv(sl)
            prms['Select'] |= df_temp['Select']
        prms = prms[prms['Select'] == 1]
        prms['Range'] = prms.apply(lambda x: (x['Min'], x['Max']), axis = 1)
        self.prms = prms.copy()
        self.crops = crops
        self.split = np.cumsum([len(self.prms)]*len(crops))
    
    def constraints(self):
        return list(self.prms['Range'].values)*len(self.crops)



class ieParm(pd.DataFrame):

    _metadata = ['header', 'name', 'prms', 'split']
    @classmethod
    def load(cls, path):
        """
        Load data from an ieParm file into DataFrame.
        """
        df = r.readParm(path + '/ieParm.DAT')
        df = pd.DataFrame(df)
        df.columns = ["SCRP1_" + str(i) for i in range(1, 31)] + \
                     ["SCRP2_" + str(i) for i in range(1, 31)] + \
                     ["PARM" + str(i) for i in range(1, 113)]
        
        inst = cls(df)
        inst.name = 'ieParm'
        inst.prms = None
        # print(inst)
        return inst

    def save(self, path):
        r.writeParm(self.values, path + '/ieParm.DAT')
    
    def parm_edit(self, values):
        cols = self.prms['Parm'].values
        self.loc[0, cols] = values

    @property
    def vals(self):
        cols = self.prms['Parm'].values
        return self.loc[0, cols]

    def set_sensitive(self, df_paths):
        prms = pd.read_csv(df_paths[0])
        for sl in df_paths[1:]:
            df_temp = pd.read_csv(sl)
            prms['Select'] |= df_temp['Select']
        prms = prms[prms['Select'] == 1]
        prms['Range'] = prms.apply(lambda x: (x['Min'], x['Max']), axis = 1)
        self.prms = prms.copy()
        
    def constraints(self):
        return list(self.prms['Range'].values)



