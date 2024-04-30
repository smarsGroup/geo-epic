
# EPIC Python Package

EPIC Python package! 

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

Epic_pkg allows you to run various commands. The structure is:

```bash
epic_pkg {module} {func} -options
```
## List of Modules and Functions:

- ### **workspace**
  - **new**: Create a new workspace with a template structure.
  - **prepare**: Prepare the input files using config file.
  - **list_files**: Create lst.DAT files using config file.
  - **run**: Execute the simulations.

- ### **weather**
  - **download_daily**: Download daily weather data. 
  - **daily2monthly**: Convert daily weather data to monthly.
  - **download_windspeed**: Download wind speed data.

- ### **soil**
  - **process_gdb**: Process ssurgo gdb file.

- ### **sites**
  - **process_aoi**: Process area of interest file.  (TODO)
  - **process_foi**: Process fields of interest file.  (TODO)
  - **generate**: Generate site files from processed data.

For more details on each command and its options, use:
```bash
epic_pkg {module} {func} --help
```
