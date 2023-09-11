# EPIC Python Package

EPIC Python package! 

## Installation

### Prerequisites

Before starting the installation, ensure you have `wget`, `conda` or `virtualenv` installed.



### Steps

1. **Download [setup.sh](setup.sh) file**

2. **Create a Virtual Environment**(optional)

   Python 3.9v is required for this package. So it's recommended to setup this package within a virtual environment. Here's how to create one:

   **Using conda: (Recommended)**
   ```linux and windows
   conda create --name epic_env python=3.9
   conda activate epic_env
   ```

   **Using virtualenv:**
   ```bash(linux)
   virtualenv epic_env
   source epic_env/bin/activate
   ```
   
   ***Windows:***
   ```windows
   cd my-project
   virtualenv --python C:\Path\To\Python\python.exe venv
   .\venv\Scripts\activate
   ```
   
4. **Run the Setup Script**

    Once you have your virtual environment ready and activated, execute the setup.sh script:

    ***Linux:***
    ```linux(bash)
    bash setup.sh
    ```
    
    ***Windows:***
    ```windows
    setup.bat
    ```

    This will set up everything needed to run the EPIC Python package within your virtual environment.

## Commands Available

Epic_pkg allows you to run various commands. The structure is:

```bash
epic_pkg module func -options
```

## List of Modules and Functions:

- **exp**
  - **new**: Create a workspace with a template structure.
  - **prep**: Prepare the workspace with a provided configuration.
  - **run**: Execute the simulations.
- **weather**
  - **download_windspeed**: Download wind speed data.
  - **download_daily**: Download daily weather data. (TODO)
  - **daily2monthly**: Convert daily weather data to monthly.  (TODO)
- **soil**
  - **process_gdb**: Process ssurgo gdb file.
- **site**
  - **generate**: Generate site files.

For more details on each command and its options, use:
```bash
epic_pkg module func --help
```

## Steps
1. Create new workspace
2. Edit config file
3. Prepare the workspace and execute the simulations







