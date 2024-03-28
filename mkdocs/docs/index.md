
# EPIC Python Package

EPIC Python package! 

Documentation site - https://smarsgroup.github.io/EPIC-pkg/

To update document site, use this command - "mkdocs gh-deploy --force"

## Installation

### Prerequisites

Before starting the installation, ensure you have `wget` and `conda` are installed.


### Steps

1. Setup a Virtual environment. (conda Recommended)
   ```
   conda create --name epic_env python=3.9
   conda activate epic_env
   ```
2. Install the package
   ```
   pip install git+https://github.com/smarsGroup/EPIC-pkg.git
   ```
   
## Commands Available

Epic_pkg allows you to run various commands. The structure is:

```bash
epic_pkg module func -options
```
## List of Modules and Functions:

- **workspace**
  - **new**: Create a new workspace with a template structure.
  - **prepare**: Prepare the input files using config file.
  - **list_files**: Create lst.DAT files using config file.
  - **run**: Execute the simulations.
- **weather**
  - **download_daily**: Download daily weather data. 
  - **daily2monthly**: Convert daily weather data to monthly.
  - **download_windspeed**: Download wind speed data.
- **soil**
  - **process_gdb**: Process ssurgo gdb file.
- **sites**
  - **process_aoi**: Process area of interest file.  (TODO)
  - **process_foi**: Process fields of interest file.  (TODO)
  - **generate**: Generate site files from processed data.

For more details on each command and its options, use:
```bash
epic_pkg module func --help
```
