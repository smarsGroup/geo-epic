
# EPIC Python Package

EPIC Python package! 

Doc site - 

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


 # (Data)

[//]: # (The tool uses data on soil type, weather conditions, and crop management practices to make accurate and specific recommendations for nitrogen application. The data used to train the model is not included in this repository, if you want to test the tool you will need to provide your own data.)

## Deployment
The [website](http://nitrogen-recommendation-tool.s3-website-us-east-1.amazonaws.com) is deployed on AWS using Simple Storage Service (S3).

### Instructions to deploy the website on AWS S3: ###
1. Run the following command: `npm run build`
2. Navigate to the [nitrogen-recommendation-tool](https://s3.console.aws.amazon.com/s3/buckets/nitrogen-recommendation-tool?region=us-east-1&tab=objects) S3 bucket.
3. Empty the bucket. Delete all the contents of the bucket.
4. Upload the contents of the "build" folder in the project directory to the S3 bucket.

Cloudfront distribution [link](ddpa7b9k8neah.cloudfront.net) of the website.

## Contributing
If you want to contribute to the project, please open an issue or submit a pull request.
Please take a look at the future tasks for the project [here](https://docs.google.com/document/d/1sk-xRCABPU3FGIs1ClKA7-HYQKUd2Y2Ky3uUMOL6Tjs/edit).

## License
This project is licensed under the MIT License - see the LICENSE.md file for details.

## Contributors
[Keerthan Mahesh](https://github.com/keerthanmahesh), MS Software Engineering, University of Maryland, College Park \
[Disha Radhakrishna](https://github.com/Disha-94), MS Software Engineering, University of Maryland, College Park \
[Pridhvi Krishna Venkata Meduri](https://github.com/mrlancelot), MS Cybersecurity, University of Maryland, College Park

## Questions
If you have any questions, please feel free to contact us at [kmahesh7@umd.edu](), [dradhakr@umd.edu]().