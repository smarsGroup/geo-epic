# EPIC Python Package

EPIC Python package! 

## Installation

### Prerequisites

Before starting the installation, ensure you have `wget`, `conda` or `virtualenv` installed.



### Steps

1. **Download [setup.sh](setup.sh) file**

2. **Create a Virtual Environment**

   It's recommended to setup this package within a virtual environment. Here's how to create one:

   **Using conda:**
   ```bash
   conda create --name epic_env python=3.10
   conda activate epic_env
   ```

   **Using virtualenv:**
   ```bash
   virtualenv epic_env
   source epic_env/bin/activate
   ```

3. **Install GDAL**
   
   **Using conda:**
   ```bash
   conda install -c conda-forge gdal
   ```
   
4. **Run the Setup Script**

    Once you have your virtual environment ready and activated, execute the setup.sh script:

    ```bash
    bash setup.sh
    ```
    This will set up everything needed to run the EPIC Python package within your virtual environment.

## Commands Available

Epic_pkg allows you to run various commands. The structure is:

```bash
epic_pkg module func -options
```

## List of Modules and Functions:

- **weather**
  - **download_windspeed**: Download wind speed data.
  - **download_daily**: Download daily weather data.
- **soil**
  - **process_gdb**: Process ssurgo gdb file.
- **site**
  - **generate**: Generate site files.
- **exp**
  - **prep**: Prepare the workspace with a provided configuration.
  - **run**: Execute the simulations.
  - **new**: Create a workspace with a template structure.

For more details on each command and its options, use:
```bash
epic_pkg module func --help
```
   







