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

# Check if the OS is Windows and exit if true
if sys.platform.startswith('win'):
    print("Installation not supported for Windows.")
    sys.exit(1)

try:
    import osgeo
    print('GDAL already installed')
except:
    print('Installing GDAL...')
    install_gdal("GDAL-3.4.1-cp39-cp39-manylinux_2_5_x86_64.manylinux1_x86_64.whl")

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

subprocess.check_call(['pip', 'install', '--no-binary', ':all:', 'ruamel.yaml==0.16.12'])
from geoEpic.misc import ConfigParser
config = ConfigParser('./geoEpic/templates/ws_template/config.yml')

config.update_config({'soil' : {'soil_map': f'{home_dir}/GeoEPIC_metadata/SSURGO.tif',},
                      'site': {'elevation': f'{home_dir}/GeoEPIC_metadata/SRTM_1km_US_project.tif',
                                'slope': f'{home_dir}/GeoEPIC_metadata/slope_us.tif',
    }, })

# Function to read the requirements.txt file
def read_requirements():
    with open('requirements.txt', 'r') as file:
        return file.readlines()

# Setup function
setup(
    name='geo-epic',
    version='0.1',
    packages=find_packages(),
    install_requires=read_requirements(),
    include_package_data=True,
    package_data={
        'geoEpic': ['templates/**/**/*',
                    'ssurgo/template.sol',
                    'sites/template.sit',
                    'templates/EPICeditor.xlsm'],
    },
    entry_points={
        'console_scripts': [
            'geo-epic=geoEpic.dispatcher:main',
        ],
    },
)
