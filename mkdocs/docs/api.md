

## Commands Available
### (ToDo)

Geo-Epic allows you to run various commands. The structure is as show below:

```bash
geo-epic {module} {func} -options
```
example usage:
```bash
geo-epic workspace new -w Test
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
geo-epic {module} {func} --help
```
