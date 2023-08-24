# EPIC Python Package

EPIC Python package! 

## Installation

### Prerequisites

Before starting the installation, ensure you have `wget`, `conda` or `virtualenv` installed.

### Steps

1. **Download [https://github.com/smarsGroup/EPIC-utils/blob/master/setup.sh](link)**

2. **Create a Virtual Environment**

   It's recommended to setup this package within a virtual environment. Here's how to create one:

   **Using conda:**
   ```bash
   conda create --name epic_env python=3.8
   conda activate epic_env
   ```

   **Using virtualenv:**
   ```bash
   virtualenv epic_env
   source epic_env/bin/activate
   ```
3. **Run the Setup Script**

    Once you have your virtual environment ready and activated, execute the setup.sh script:

    ```bash
    bash setup.sh
    ```
    This will set up everything needed to run the EPIC Python package within your virtual environment.

## Commands Available

Epic_pkg allows you to run various commands. The structure is:

```bash
epic_pkg command_name -options
```

### List of Commands:
- create_ws: Create a workspace with a template structure.
- prep: Prepare the workspace with a provided configuration.
- run: Execute the simulations.
- download_windspeed: Download wind speed data.
- process_soils: Process ssurgo gdb file.
- generate_site: Generate site details.

For more details on each command and its options, use:
```bash
epic_pkg command_name --help
```
   







