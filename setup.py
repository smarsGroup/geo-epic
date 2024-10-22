import os
import sys
from setuptools import setup, find_packages
import subprocess
import urllib.request

# Check if the OS is Windows and use appropriate commands
is_windows = sys.platform.startswith('win')

# Function to run commands based on the OS
def run_command(command):
    if is_windows:
        return subprocess.run(command, shell=True, check=True)
    else:
        return subprocess.run(command, check=True)

# try:
#     import osgeo
#     print('GDAL already installed')
# except:
#     print('Installing GDAL...')
#     run_command('conda install -c conda-forge gdal --no-update-deps')

# try:
#     # Check if Redis is installed
#     if is_windows:
#         run_command('redis-cli --version')
#     else:
#         run_command(["redis-server", "--version"])
#     print("Redis is already installed.")
# except:
#     print("Installing Redis...")
#     run_command(['conda', 'install', '-c', 'conda-forge', 'redis'])

# Define metadata directory in the user's home folder
home_dir = os.path.expanduser("~")
metadata_dir = os.path.join(home_dir, 'GeoEPIC_metadata')

# Check if the epic_pkg_metadata directory already exists, create it if it doesn't, 
# and skip downloading files if it does.
if not os.path.exists(metadata_dir):
    os.makedirs(metadata_dir)
    # List of files to download
    files_to_download = [
        "https://smarslab-files.s3.amazonaws.com/epic-utils/slope_us.tif",
        "https://smarslab-files.s3.amazonaws.com/epic-utils/SRTM_1km_US_project.tif",
        "https://smarslab-files.s3.amazonaws.com/epic-utils/SSURGO.tif"
    ]
    # Download the files to the metadata directory
    for file_url in files_to_download:
        filename = os.path.join(metadata_dir, os.path.basename(file_url))
        urllib.request.urlretrieve(file_url, filename)
else:
    print(f"'{metadata_dir}' already exists, skipping file downloads.")

# Function to read the requirements.txt file
def read_requirements():
    with open('requirements.txt', 'r') as file:
        return file.readlines()

# run_command('pip install --no-binary :all: ruamel.yaml==0.16.2')

# Setup function
setup(
    name='geo_epic',
    version='1.0',
    packages=find_packages(),
    install_requires=read_requirements(),
    include_package_data=True,
    package_data={
        'geoEpic': ['assets/**/**/*',
                    'soil/template.sol',
                    'sites/template.sit',
                    'assets/EPICeditor.xlsm',
                    'gee_utils/config.json',
                    ],
    },
    entry_points={
        'console_scripts': [
            'geo_epic=geoEpic.dispatcher:main',
        ],
    },
)


# subprocess.check_call(['pip', 'install', '--no-binary', ':all:', 'ruamel.yaml==0.16.2'])

# from geoEpic.io.config_parser import ConfigParser

# config = ConfigParser('./geoEpic/assets/ws_template/config.yml')

# config.update({'soil' : {'soil_map': f'{home_dir}/GeoEPIC_metadata/SSURGO.tif',},
#                 'site': {'elevation': f'{home_dir}/GeoEPIC_metadata/SRTM_1km_US_project.tif',
#                          'slope': f'{home_dir}/GeoEPIC_metadata/slope_us.tif',
#     }, })
