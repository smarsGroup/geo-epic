# Run an EPIC Experiment

### 1. Create new workspace
```bash
epic_pkg workspace new -w Test
cd Test
```
It willl create a new workspace in the new directory named 'Test'. This 'Test' folder will automatically create sub-folders for EPIC model like model, opc, sites, soil, weather and a config.yml doc in it. You need to to go to Test folder before simulation starts.

### 2. Input data preparation
#### a) For soil:
Go to [https://www.nrcs.usda.gov/resources/data-and-reports/gridded-soil-survey-geographic-gssurgo-database](https://www.nrcs.usda.gov/resources/data-and-reports/gridded-soil-survey-geographic-gssurgo-database) and download the required soil database. 

Example: For Maryland, go to State Database-soils|Powered by Box link to download gSSURGO_MD.zip and keep it in soil folder after extarcing it.
#### b) For Weather and sites 
Go to [https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/index.php](https://www.nass.usda.gov/Research_and_Science/Crop-Sequence-Boundaries/index.php) and Download the Crop Sequence Boundaries 2016-2023 dataset and extract it. This crop sequence boundary contains the crop-field shapefiles for whole USA. You can clip it for your AOI. Like if you are working in Maryland state, just clip it for Maryland and keep it in a new folder named 'CropRotations'.

**NOTE**: Using the crop-sequence boundary, the weather and sites files are automatically downloaded to create input files for AOI, but only the sites files are downloaded offline and stored in the respective folder. Weather files are stored on the server while operating the simulations without offline storage and deleted automatically after simulation.
To download weather files automatically, use the following commands:
```
epic_pkg weather download daily
```
This command will only work if you already installed the package, created workspace and downloaded the crop-sequence-boundary.

### 3. Edit config file as needed
Since this package is designed to work for USA-based study regions. In the config.yml file, you need to change the following rows as per your AOI and convenience, but you can adopt the following practice:

**Let's say you have to run the model for Maryland state of USA, change following rows:**

a) EXPName: EPIC RUN (Carbon or Nitrogen Assessment) (You can keep anything)
Region: Maryland
code: MD
Fields_of_Interests: ./CropRotations/MDRotFilt.shp

**Note:** This MDRotFilt.shp is the same file we downloaded and kept in the CropRotations folder in the previous step.
b) Soil: 
gdb_path: 4. Before going to editing the 
./soil/MD_slopelen_1.csv

**The thumb-rule is that the config file should be edited considering the code name of the study region. Like you did it here by replacing MD in the config file throughout.**

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

This command will also create a **post_process.pynb** doc which will have an example code to visualize the required parameters from ACY and DGN files. 

You can edit this code as per your requirements. You just have to identify the parameters and edit accordingly.

## Example Visualization

### 7. Post-process the output visualization
You need to post-process the output files according to your interests. Generally, as an agricultural reserachers you need to process the DGN and ACY files.

#### For post-processing
```
epic_pkg workspace post_process
```
This will run the example code **post_process.pynb** which has been created in the Test folder. It will take a variable called 'YLDG' which denotes the yearly yield in t/ha/yr for all the sites and put it in a sepearte column corresponding to all the site ids with creatinh a yldg.csv file.


#### For visualization
```
epic_pkg workspace visualize
```
It will simply plot the 'YLDG' variable corresponding to the site ids and crate a map for study region. 

### Your example plot will look like this:
!['Maryland_Yield'](./Yield_MD.png)