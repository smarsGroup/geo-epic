# Nitrogen Recommendation Tool

Nitrogen Recommendation Tool for Wheat in Kansas and Oklahoma.

This repository contains the code for a tool that provides nitrogen recommendations for wheat farmers in Kansas and Oklahoma. The tool uses data on fertilizer amount, weather conditions, and crop management practices to make accurate and specific recommendations for nitrogen application.

## Getting Started
These instructions will help you get the project up and running on your local machine and on the GEOG cluster for development and testing purposes.

## Prerequisites
Node.js Latest LTS Version: 18.15.0 (includes npm 9.5.0)

## Setup Instructions and Available Scripts
### Instructions to set up the website in your local environment: ###
Navigate to the project directory and run the following commands:\
Install dependencies using node package manager:\
   `npm install`\
   To run the app in development mode, in your project directory: \
   `npm start`

Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

The page will reload if you make edits.\
You will also see any lint errors in the console.

To launch the test runner in the interactive watch mode: \
`npm test`

See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### Instructions to set up the website on the GEOG cluster and access the website on your local machine: ###

1. Clone the repository to your folder on the cluster.
2. Install PuTTY on your local machine.
3. Open PuTTY and in the Session's window enter the cluster's hostname or IP address and the port number of the destination SSH server. Make sure the connection type is set to SSH.
4. In the left sidebar under the Category options. Navigate to the Connection >> SSH >> Tunnels.
5. Select Local to define the type of SSH port forward.
6. In the Source port field, enter the port number on which the frontend application in running. (Example - Source port: 3000).
7. In the Destination field, enter the destination address followed by the port number. (Example - Destination: localhost:3000).
8. Click Add to add the port forward.
9. Similarly, add another port forward for the backend application. (Example - Source port: 4000, Destination: localhost:4000).
10. Click Open to establish the connection. The tunnel will work until the SSH session is active.
11. Run the following commands:\
`module load node`\
`export NODE_OPTIONS=--max_old_space_size=4096`\
`fuser -n tcp -k 3000`\
`fuser -n tcp -k 5000`
12. Navigate to the "react_leaflet" and "socket_server" project directories in separate terminals and run the following commands:\
`npm install`\
`npm start`
13. Open [http://localhost:3000](http://localhost:3000) to view the website in the browser.

[//]: # (Usage)

[//]: # (The tool will prompt you to enter data on soil type, weather conditions, and crop management practices.)

[//]: # (Based on the information provided, the tool will make a recommendation for nitrogen application in pounds per acre.)

[//]: # (Data)

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