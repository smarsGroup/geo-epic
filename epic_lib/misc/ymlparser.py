from ruamel.yaml import YAML
import os

class ConfigParser:

    def __init__(self, curr_dir, config_path):
        self.config_path = config_path
        self.dir = curr_dir
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(sequence=4, offset=2)
        self.config_data = self.load()

    def _update_relative_paths(self, data):
        """Recursively update paths starting with './' in the data."""
        if isinstance(data, str) and data.startswith('./'):
            data = os.path.join(self.dir, data[2:])
            return data
        if isinstance(data, dict):
            data = data.copy()
            for key, value in data.items():
                if isinstance(value, str) and value.startswith('./'):
                    data[key] = os.path.join(self.dir, value[2:])
        return data

    def load(self):
        """Load data from the YAML file."""
        with open(self.config_path, 'r') as file:
            data = self.yaml.load(file)
        return data

    def save(self):
        """Save data to the YAML file."""
        with open(self.config_path, 'w') as file:
            self.yaml.dump(self.config_data, file)

    def recursive_update(self, data, updates):
        """Recursively update dictionary values."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in data:
                data[key] = self.recursive_update(data[key].copy(), value)
            else:
                data[key] = value
        return data

    def update_config(self, updates):
        """Update the current config with new values."""
        self.config_data = self.recursive_update(self.config_data, updates)
        self.save()

    def get(self, key, default=None):
        """Retrieve a value from the configuration."""
        data = self.config_data.get(key, default)
        return self._update_relative_paths(data)
    
    def update(self, key, value):
        """Set a value in the configuration."""
        self.config_data[key] = value
        self.save() 
    
    def __getitem__(self, key):
        return self.get(key, None)

    def __repr__(self):
        return repr(self.config_data)
        
if __name__ == '__main__':
    # Example usage
    config = ConfigParser('config.yml')
    config.update_config({
        'soil': {
            'files_dir': './soil_files'
        },
        'Processed_Info': './processed_info.csv'
    })
    print(config.get('soil'))


