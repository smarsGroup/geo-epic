### Weather Module

Weather input files for EPIC model are created from the below listed sources. During the simulations, these weather files are temporarily stored and are automatically deleted once the simulation is complete. They are not stored offline.

To get weather info and save them as daily and monthy input files, the following command can be used:

```
epic_pkg weather download_daily
```

Note: This command will only function correctly if you have already set up your workspace, and downloaded the crop-sequence boundaries and croped it to your area of interest."

### Sources

- **DAYMET** : [https://daymet.ornl.gov/](https://daymet.ornl.gov/) 
- **NLDAS** : [https://climatedataguide.ucar.edu/climate-data/nldas-north-american-land-data-assimilation-system/](https://climatedataguide.ucar.edu/climate-data/nldas-north-american-land-data-assimilation-system/) 

