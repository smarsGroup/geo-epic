
# EPIC Python Package
A toolkit for geospatial crop simulations using EPIC model

!['Maryland_Yield'](./Yield_MD.png)

## Installation

Before starting the setup, ensure you have `wget` and `conda` installed.

Setup a Virtual environment. (conda Recommended)
```bash
conda create --name epic_env python=3.9
conda activate epic_env
```
Install the EPIC Python Package
```bash
pip install git+https://github.com/smarsGroup/EPIC-pkg.git
```
   

## Commands Available

Epic_pkg allows you to run various commands. The structure is as show below:

```bash
epic_pkg {module} {func} -options
```
example usage:
```bash
epic_pkg workspace new -w Test
```
### List of Modules and Functions:

#### **workspace**
  - **new**: Create a new workspace with a template structure.
  - **prepare**: Prepare the input files using config file.
  - **run**: Execute the simulations.
  - **post_process**: Process Output files from simulation runs.
#### **weather**
  - **download_daily**: Download daily weather data. 
  - **daily2monthly**: Convert daily weather data to monthly.
#### **soil**
  - **process_gdb**: Process ssurgo gdb file.
#### **sites**
  - **process_foi**: Process fields of interest file.  (TODO)
  - **generate**: Generate site files from processed data.

For more details on each command and its options, use:
```bash
epic_pkg {module} {func} --help
```
