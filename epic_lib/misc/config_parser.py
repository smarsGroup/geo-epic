from ruamel.yaml import YAML
import os

class ConfigParser:

    def __init__(self, config_path):
        self.config_path = config_path
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(sequence=4, offset=2)
        self.config_data = self.load()

    def load(self):
        """Load data from the YAML file."""
        with open(self.config_path, 'r') as file:
            data = self.yaml.load(file)
        return data

    def save(self):
        """Save data to the YAML file."""
        with open(self.config_path, 'w') as file:
            self.yaml.dump(self.config_data, file)

    def recursive_update(self, updates):
        """Recursively update dictionary values."""
        for key, value in updates.items():
            if isinstance(value, dict) and key in self.config_data:
                self.recursive_update(self.config_data[key], value)
            else:
                self.config_data[key] = value

    def update_config(self, updates):
        """Update the current config with new values."""
        self.recursive_update(updates)
        self.save()

    def get(self, key, default=None):
        """Retrieve a value from the configuration."""
        return self.config_data.get(key, default)
    def set(self, key, value):
        """Set a value in the configuration."""
        self.config_data[key] = value
        self.save()  # Optionally save it after setting
# Example usage
config = ConfigParser('config.yml')
config.update_config({
    'soil': {
        'files_dir': './soil_files'
    },
    'Processed_Info': './processed_info.csv'
})
print(config.get('soil'))


    # def _convert_relative_to_absolute_paths(self, data):
    #     """Convert all paths starting with ./ to absolute paths."""
    #     for key, value in data.items():
    #         if isinstance(value, dict):
    #             data[key] = self._convert_relative_to_absolute_paths(value)
    #         elif isinstance(value, str) and value.startswith("./"):
    #             data[key] = os.path.join(os.path.dirname(self.config_path), value[2:])
    #     return data

    def get(self, key, default=None):
        return self.config_data.get(key, default)

    def __getitem__(self, key):
        return self.config_data[key]

    def __repr__(self):
        return repr(self.config_data)

