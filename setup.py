import os
import sys
from setuptools import setup, find_packages
import subprocess
import urllib.request

def install_gdal(filename):
    # Download the wheel file
    url = "https://smarslab-files.s3.amazonaws.com/epic-utils/" + filename
    urllib.request.urlretrieve(url, filename)
    subprocess.check_call(['pip', 'install', filename])
    os.remove(filename)

# Check if the OS is Windows
is_windows = sys.platform.startswith('win')

# Download and install the appropriate GDAL wheel file based on the OS
if is_windows:
    install_gdal("GDAL-3.4.1-cp39-cp39-win_amd64.whl")
else:
    install_gdal("GDAL-3.4.1-cp39-cp39-manylinux_2_5_x86_64.manylinux1_x86_64.whl")
    
# Define metadata directory in the user's home folder and create it if it doesn't exist
home_dir = os.path.expanduser("~")
metadata_dir = os.path.join(home_dir, 'epic_pkg_metadata')
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

subprocess.check_call(['pip', 'install', '--no-binary', ':all:', 'ruamel.yaml==0.16.12'])

from epic_lib.misc import ConfigParser
config = ConfigParser('./', './epic_lib/ws_template/config.yml')

config.update_config({'sites': {
        'elevation': f'{home_dir}/epic_pkg_metadata/SRTM_1km_US_project.tif',
        'slope_us': f'{home_dir}/epic_pkg_metadata/slope_us.tif',
        'ssurgo_map': f'{home_dir}/epic_pkg_metadata/SSURGO.tif',
    } })

# Function to read the requirements.txt file
def read_requirements():
    with open('requirements.txt', 'r') as file:
        return file.readlines()

# Setup function
setup(
    name='epic_pkg',
    version='0.1',
    packages=find_packages(),
    install_requires=read_requirements(),
    include_package_data=True,
    package_data={
        'epic_lib': ['ws_template/**/*',
                    'ssurgo/template.sol',
                    'sites/template.sit'],
    },
    entry_points={
        'console_scripts': [
            'epic_pkg=epic_lib.dispatcher:main',
        ],
    },
)

