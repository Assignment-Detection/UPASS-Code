# UPASS - Upload & Pliagarise Alert SyStem

UPASS monitors the internet daily for matches to your assignment questions. 
Upon detection of a hit, UPASS sends an email notification.

## What is UPASS

UPASS monitors the internet daily for matches to your assignment questions. Upon detection of a hit, UPASS sends an email notification. 

UPASS will need to be setup and run on a single computer at your institute, however once setup, it can be used by anyone to submit their assignments to from any computer.

Please note that both a SerpStack account and Google account will be required for UPASS to be setup and run. Both are free, however, you may be required to upgrade your SerpStack account to a subscription plan to have sufficient API requests to run UPASS once several assignments have been submitted.

## What is this repository

This is for the code savvy and interested who would like to understand how our UPASS software works. Please refer to our sister, UPASS Software Package repository: 

https://github.com/Assignment-Detection/UPASS-Package-zip

The above respository houses the actual UPASS Software, and within, explains what UPASS is and the process for setting it up at your institute.


## Files & Directories

 - The bin directory contains backend files and directories used by UPASS
 - service-account-credentials is a directory where the Google Cloud Platform Service Account json file is to be put (refer to UPASS Setup Procedure.pdf for details)
 - venv is the virtual environment directory, allowing for the git to be simply cloned and used
 - UPASS Setup Procedure.pdf contains the instructions for setting up the UPASS assignment detail submission form and linking it with the UPASS backend
 - The details for the gmail account which UPASS will use to send notification emails are to be put in the gmail_username.txt and gmail_password.txt files
 - The name of the google sheet linked with the UPASS assignment submission form is to be put in the google_sheet_name.txt file (refer to UPASS Setup Procedure.pdf for details)
 - run_upass.py is to be executed daily after UPASS has been setup, this script executes the daily checks of the UPASS system
 - Your serpstack api key is to be put into the serpstack_api_access_key.py file (refer to UPASS Setup Procedure.pdf for details)
 - setup_upass.py is to be executed once after completing the steps in UPASS Setup Procedure.pdf, this script finalises the setup and confirms that UPASS has been set up correctly
 - upass_overview.py can be executed to view the details of the assignments that are currently uploaded to UPASS (after it has been setup). It also tells the user the number of current assignments in UPASS and the total number of search terms for these assignments.  


## Copyright

Copyright © 2021-2022 Edmund Pickering, Sam Cunningham, Sarah Dart and Rick Somers. This code is available for non-commercial use only. Commercial use is prohibited unless permission from the authors is given upon request. Any other usage is prohibited without the express permission of the authors. 
