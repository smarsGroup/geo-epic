### Weather data sources 

#### a) DAYMET
Link: [https://daymet.ornl.gov/](https://daymet.ornl.gov/) 

#### b) NLDAS
Link: [https://climatedataguide.ucar.edu/climate-data/nldas-north-american-land-data-assimilation-system/](https://climatedataguide.ucar.edu/climate-data/nldas-north-american-land-data-assimilation-system/) 

Using the crop-sequence boundary, the weather files are automatically downloaded to create input files for AOI, but weather files are stored on the server while operating the simulations without offline storage and deleted automatically after simulation.
To download weather files automatically, use the following commands:
```
epic_pkg weather download daily
```
This command will only work if you already installed the package, created workspace and downloaded the crop-sequence-boundary.
