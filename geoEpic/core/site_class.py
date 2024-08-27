import os
from geoEpic.weather import DailyWeather
from geoEpic.io import DLY, SIT

class Site:
    def __init__(self, opc, dly, sol, sit, site_id=None):
        self.opc_path = opc
        self.dly_path = dly
        self.sol_path = sol
        self.sit_path = sit
        if site_id is None:
            self.site_id = os.path.basename(sit).split('.')[0]
        else:
            self.site_id = site_id
        self.outputs = {}
        self.sit = SIT(self.sit_path)
        self.lat = self.sit.site_info['lat']
        self.lon = self.sit.site_info['lon']

    def __str__(self):
        return (f"Site ID: {self.site_id}\n"
                f"OPC Path: {self.opc_path}\n"
                f"DLY Path: {self.dly_path}\n"
                f"SOL Path: {self.sol_path}\n"
                f"SIT Path: {self.sit_path}")
    
    
    def get_dly(self):
        if self.dly_path is not None:
            return DLY(self.dly_path)