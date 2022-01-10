from os import path,  mkdir, listdir
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def main():
    # Confirm package download complete
    if not path.exists(path.join('bin')) \
            or not path.exists(path.join('bin/cheating-website-list')) \
            or not path.exists(path.join('bin/takedown-instructions'))\
            or not path.isfile(path.join('bin/takedown-instructions/Removal of Content from Websites.pdf')) \
            or not path.isfile(path.join('bin/cheating-website-list/cheating_websites.csv')) \
            or not path.isfile('serpstack_api_access_key.txt') \
            or not path.isfile('google_sheet_name.txt') \
            or not path.exists(path.join('service-account-credentials')):
        print('installation incomplete - try reinstalling package')
        return


    # Confirm serpstack api key has been entered into serpstack_api_access_key.txt and is valid
    if not path.getsize('serpstack_api_access_key.txt') > 0:
        print('serpstack api key not entered into serpstack_api_access_key.txt')
        return
    else:
        with open('serpstack_api_access_key.txt') as f:
            access_key = f.readlines()[0]
            params = {'access_key': access_key}
            api_result = requests.get('http://api.serpstack.com/search', params)
            if api_result.status_code != 200:
                print('API Response not received')
            else:
                if '"code": 101' in api_result.text:
                    print('Serpstack API access key invalid')
                    return


    # Confirm google sheets name and credentials valid
    if not path.getsize('google_sheet_name.txt') > 0:
        print('google sheets name not entered into google_sheets_name.txt')
        return
    else:
        with open('google_sheet_name.txt') as f:
            try:
                SHEET_NAME = f.readlines()[0]
                scopes = ['https://www.googleapis.com/auth/spreadsheets',
                    "https://www.googleapis.com/auth/drive.file",
                    "https://www.googleapis.com/auth/drive"]
                files = listdir('service-account-credentials')
                for file in files:
                    if 'json' in file:
                        cred_path = 'service-account-credentials/' + file
                creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scopes)
                client = gspread.authorize(creds)
                sheet = client.open(SHEET_NAME).sheet1
                DATA_TO_PULL = 'Form Responses 1'
                sheet.spreadsheet.values_get(range=DATA_TO_PULL)
                data = sheet.spreadsheet.values_get(range=DATA_TO_PULL)
            except:
                print('google sheets name or credentials invalid')


    # Create directory for serp results and upass overview
    if not path.exists(path.join('bin/serp-results')):
        mkdir(path.join('bin/serp-results'))
    if not path.exists(path.join('bin/upass-overview')):
        mkdir(path.join('bin/upass-overview'))


    # Create upass overview csv
    if not path.isfile(path.join('bin/upass-overview/overview.csv')):
        df = pd.DataFrame(list())
        df.to_csv(path.join('bin/upass-overview/overview.csv'))


if __name__ == '__main__':
    main()
