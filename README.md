# UPASS - Upload & Pliagarise Alert SyStem

UPASS monitors the internet daily for matches to your assignment questions. 
Upon detection of a hit, UPASS sends an email notification.

## Description

___Background information on UPASS here___

Please note that both a SerpStack account and Google account will be required for UPASS to be setup and run. Both are free, however, you may be required to upgrade your SerpStack account to a subscription plan to have sufficient API requests to run UPASS once several assignments have been submitted.

## Setup Overview

The setup procedure is as follows:
 - Follow the steps outlined in the UPASS Setup Procedure.docx file to set up the assignment detail submission form and link with to the UPASS backend
 - Run the setup_upass.py file to confirm that the system has beeen set up correctly
 - Put the details for a gmail account into the gmail_account_details.py file and ensure that 'Less secure app access' is turned ON for this account
 - UPASS may now be run daily by executing the run_upass.py file. Note that a paid serpstack (https://serpstack.com/) plan may be required depending on the volume of assignments and search terms uploaded


### Files & Directories

 - The bin directory contains backend files and directories used by UPASS
 - service-account-credentials is a directory where the Google Cloud Platform Service Account json file is to be put (refer to UPASS Setup Procedure.docx for details)
 - venv is the virtual environment directory, allowing for the git to be simply cloned and used
 - UPASS Setup Procedure.docx contains the instructions for setting up the UPASS assignment detail submission form and linking it with the UPASS backend
 - The details for the gmail account which UPASS will use to send notification emails are to be put in the gmail_account_details.py file
 - The name of the google sheet linked with the UPASS assignment submission form is to be put in the google_sheet_name.txt file (refer to UPASS Setup Procedure.docx for details)
 - run_upass.py is to be executed daily after UPASS has been setup, this script executes the daily checks of the UPASS system
 - Your serpstack api key is to be put into the serpstack_api_access_key.py file (refer to UPASS Setup Procedure.docx for details)
 - setup_upass.py is to be executed once after completing the steps in UPASS Setup Procedure.docx, this script finalises the setup and confirms that UPASS has been set up correctly
