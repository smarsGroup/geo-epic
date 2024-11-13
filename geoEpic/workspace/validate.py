import os
import pandas as pd
import argparse
from geoEpic.io import ConfigParser

def check_files_in_folder_without_extension(df, column_name, folder_path):
    # Get a set of filenames in the folder without extensions
    folder_files = {os.path.splitext(f)[0] for f in os.listdir(folder_path)}
    
    # Track missing files
    missing_files = []
    
    # Check each filename in the DataFrame column (without extension)
    for id in df[column_name]:
        file_name = str(id)
        # Remove the extension from the filename in the DataFrame
        file_name_no_ext = os.path.splitext(file_name)[0]
        if file_name_no_ext not in folder_files:
            missing_files.append(file_name)
    
    return missing_files

def validate_workspace(config_file):
    # Load config
    config = ConfigParser(config_file)
    
    # Required configuration keys and sub-keys
    required_keys = {
        'run_info': None,
        'site': ['dir'],
        'soil': ['files_dir'],
        'weather': ['dir'],
        'opc_dir': None
    }
    
    # Check if all required configuration keys are present
    missing_keys = []
    for key, subkeys in required_keys.items():
        if key not in config.config_data:
            missing_keys.append(key)
        elif subkeys:
            for subkey in subkeys:
                if subkey not in config[key]:
                    missing_keys.append(f"{key}.{subkey}")
    
    # Print any missing configuration keys
    if missing_keys:
        print("Missing configuration keys:")
        for key in missing_keys:
            print(f" - {key}")
        return  # Stop execution if configuration is incomplete
    
    # Load CSV file
    info_df = pd.read_csv(config['run_info'])
    required_columns_csv = {'SiteID', 'soil', 'opc', 'dly', 'lat', 'lon'}
    
    # Check required columns in CSV
    if not required_columns_csv.issubset(set(info_df.columns)):
        raise ValueError("CSV file missing one or more required columns: 'SiteID', 'soil', 'opc', 'dly', 'lat', 'lon'")
    
    # Paths for saving missing file lists
    run_info_dir = os.path.dirname(config['run_info'])
    
    # Check for missing files in each required category and write missing IDs to files if any are missing
    for filetype, column, path in [
        ('site', 'SiteID', config['site']['dir']),
        ('soil', 'soil', config['soil']['files_dir']),
        ('dly', 'dly', os.path.join(config['weather']['dir'], 'Daily')),
        ('opc', 'opc', config['opc_dir'])
    ]:
        missing_files = check_files_in_folder_without_extension(info_df, column, path)
        
        if missing_files:
            # Save missing file list to a text file
            missing_file_path = os.path.join(run_info_dir, f'missing_{filetype}.txt')
            with open(missing_file_path, 'w') as f:
                f.write('\n'.join(missing_files))
            
            # Print summary
            print(f"{len(missing_files)} {filetype} files are missing. IDs written to {missing_file_path}")
        else:
            print(f"All {filetype} files are present.")

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Validate workspace configuration and files.")
    parser.add_argument("-c", "--config", default= "./config.yml", help="Path to the configuration file")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate workspace
    validate_workspace(args.config)

# Uncomment below for script usage
if __name__ == "__main__":
    main()
