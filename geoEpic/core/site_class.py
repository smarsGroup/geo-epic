import os
from geoEpic.weather import DailyWeather
from geoEpic.io import DLY, SIT

class Site:
    def __init__(self, opc = None, dly = None, sol = None, sit = None, site_id = None):
        self.opc_path = opc
        self.dly_path = dly
        self.sol_path = sol
        self.sit_path = sit
        self.site_id = site_id
        self.outputs = {}

        if sit is not None:
            if site_id is None:
                self.site_id = os.path.basename(sit).split('.')[0]
            self.sit = SIT(self.sit_path)
            self.lat = self.sit.site_info['lat']
            self.lon = self.sit.site_info['lon']

    def __str__(self):
        return (f"Site ID: {self.site_id}\n"
                f"OPC Path: {self.opc_path}\n"
                f"DLY Path: {self.dly_path}\n"
                f"SOL Path: {self.sol_path}\n"
                f"SIT Path: {self.sit_path}")
    
    @classmethod
    def from_config(cls, config, site_info):
        instance = cls()
        # print(site_info)
        instance.opc_path = os.path.join(config['opc_dir'], f"{site_info['opc']}") \
            if str(site_info['opc']).lower().endswith('.opc') else os.path.join(config['opc_dir'], f"{site_info['opc']}.OPC")

        # Append '.DLY' extension only if not already present
        instance.dly_path = os.path.join(config['weather']['dir'], 'Daily',f"{site_info['dly']}") \
            if str(site_info['dly']).lower().endswith('.dly') else os.path.join(config['weather']['dir'], 'Daily',f"{site_info['dly']}.DLY")

        # Append '.SOL' extension only if not already present
        instance.sol_path = os.path.join(config['soil']['files_dir'], f"{site_info['soil']}") \
            if str(site_info['soil']).lower().endswith('.sol') else os.path.join(config['soil']['files_dir'], f"{site_info['soil']}.SOL")

        # Append '.SIT' extension only if not already present
        instance.sit_path = os.path.join(config['site']['dir'], f"{site_info['SiteID']}.sit") 
        instance.site_id = site_info['SiteID']
        instance.lat = site_info['lat']
        instance.lon = site_info['lon']
        # print(site_info)
        return instance


    def get_dly(self):
        if self.dly_path is not None:
            return DLY.load(self.dly_path)
