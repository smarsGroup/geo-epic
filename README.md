# EPIC Python Package

EPIC Python package! 

## Installation

### Prerequisites

Before starting the installation, ensure you have `wget`, `conda` or `virtualenv` installed.



### Steps

1. **Download [setup.sh](setup.sh) file (for linux)**

   **Download [setup.bat](setup.bat) file (for windows)**

2. **Create a Virtual Environment**

   It's recommended to setup this package within a virtual environment with python 3.9. Here's how to create one:

   **Using conda:**
   ```bash
   conda create --name epic_env python=3.9
   conda activate epic_env
   ```

   **Using virtualenv:**
   ```bash
   virtualenv epic_env
   source epic_env/bin/activate
   ```
   
3. **Run the Setup Script**

    Once you have your virtual environment ready and activated, execute the setup.sh script:

    For linux
    ```bash
    bash setup.sh
    ```

    For windows
    ```
    setup.bat
    ```

    This will set up everything needed to run the EPIC Python package within your virtual environment.

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

## Run an Experiment
1. Create new workspace
2. Edit config file
3. Prepare the workspace and execute the simulations
