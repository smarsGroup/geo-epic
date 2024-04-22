# EPIC Python Package

EPIC Python package! 

Documentation site - https://smarsgroup.github.io/EPIC-pkg/

To update document site, use this command - "mkdocs gh-deploy --force"

## Installation

### Prerequisites

Before starting the installation, ensure you have `wget` and `conda` are installed.

#### for wget
```
apt-get install wget
dpkg -l | grep wget
```
#### for conda
1. Download the installer:
  Miniconda installer for Linux.
  Anaconda Distribution installer for Linux.
  Miniforge installer for Linux.
2. Verify your installer hashes.
3. In your terminal window, run:
```
bash <conda-installer-name>-latest-Linux-x86_64.sh
```

### Installing Package

1. Setup a Virtual environment. (conda Recommended)
   ```
   conda create --name epic_env python=3.9
   conda activate epic_env
   ```
2. Install the EPIC Python Package
   ```
   pip install git+https://github.com/smarsGroup/EPIC-pkg.git
   ```
   
## Commands Available

Epic_pkg allows you to run various commands. The basic structure is:

```bash
epic_pkg module func -options
```
You need to apply the following commands and sub-commands to perform different operations:

## List of Modules and Functions:

- **workspace**
  - new: Create a new workspace with a template structure.
  - prepare: Prepare the input files using config file.
  - list_files: Create lst.DAT files using config file.
  - run: Execute the simulations.

  Example: 
  ```
  epic_pkg workspace new -w Test
  ```
  It will create a new workspace within a new folder named 'Test'

- **weather**
  - download_daily: Download daily weather data. 
  - daily2monthly: Convert daily weather data to monthly.
  - download_windspeed: Download wind speed data.

  Example:
  ```
  epic_pkg weather download_daily -w Weather
  ```
  It will automatically download daily weather data from Daymet and NLDAS servers and save in the new folder named 'Weather'. Temperature, Solar radiation and Relative humidity are accessed from Daymet while wind speed from NLDAS servers respectivley.
  
  #### Note: In epic package, weather data is not stored offline in the system as it consumes large space, it works on the cloud storage. But if you want to download and store weather files, then only use these commands.



- **soil**
  - process_gdb: Process ssurgo gdb file.



- **sites**
  - process_aoi: Process area of interest file.  (TODO)
  - process_foi: Process fields of interest file.  (TODO)
  - generate: Generate site files from processed data.


### For more details on each command and its options, use:
```bash
epic_pkg module func --help
```
Example:
```
epic_pkg workspace --help
```
It will give all the given information about workspace module.

## Run an EPIC Experiment
### 1. Create new workspace
```bash
epic_pkg workspace new -w Test
cd Test
```
It willl create a new workspace in the new directory named 'Test'. This 'Test' folder will automatically create sub-folders for EPIC model like model, opc, sites, soil, weather and a config.yml doc in it. 

### 2. Download the soil data and put it in the respective folder
#### a) For soil:
Go to https://www.nrcs.usda.gov/resources/data-and-reports/gridded-soil-survey-geographic-gssurgo-database and download the required soil database
Example: For Maryland, go to State Database-soils|Powered by Box link to download gSSURGO_MD.zip and keep it in soil folder after extarcing it.
#### b) For Weather and sites 
Go to https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/index.php and Download the Crop Sequence Boundaries 2016-2023 dataset and extract it. This crop sequence boundary contains the crop-field shapefiles for whole USA. You can clip it for your AOI. Like if you are working in Maryland state, just clip it for Maryland and keep it in a new folder named 'CropRotations'.

#### NOTE: Using the crop-sequence boundary, the weather and sites files are automatically downloaded to create input files for AOI, but only the sites files are downloaded offline and stored in the respective folder. Weather files are stored on the server while operating the simulations without offline storage and deleted automatically after simulation.

### 3. Edit config file as needed
Since this package is designed to work for USA-based study regions. In the config.yml file, you need to change the following rows as per your AOI and convenience, but you can follow the following practice:
#### Let's say you have to run the model for Maryland state of USA, change following rows:
a) EXPName: EPIC RUN (Carbon or Nitrogen Assessment) (You can keep anything)
Region: Maryland
code: MD
Fields_of_Interests: ./CropRotations/MDRotFilt.shp
##### Note: This MDRotFilt.shp is the same file we downloaded and kept in the CropRotations folder in the previous step.
b) Soil: 
gdb_path: 4. Before going to editing the 
./soil/MD_slopelen_1.csv
#### Note: The thumb-rule is that the config file should be edited considering the code name of the study region. Like you did it here by replacing MD in the config file throughout.

### 4. Prepare OPC File
OPC refers to the agricultural management practice files which is yet to automated. For now, you need to prpare management files and keep it in a new folder named 'OPC' inside the 'Test' directory.

### 5. Prepare the workspace
```bash
epic_pkg workspace prepare
```
This command will automatically pre-process the input files before simulation.


### 6. And execute the simulations
```bash
epic_pkg workspace run
```
This command will simulate the operation/s and automatically save the results in a new folder named 'Output'.

### 7. Post-process the output files
You need to post-process the resultant files according to your interests. Generally, as an agricultural reserachers you need to process the DGN and ACY files.

#### For DGN files
You need to run this scrpit:


#### For ACY files
You need to run the follwoing script:
