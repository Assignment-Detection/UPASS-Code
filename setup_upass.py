from os import path,  mkdir, listdir
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
import tkinter as tk
import ctypes
from tkinter import Label


def create_error_popup(error_message):
    '''
    Creates a new Tkinter popup window displaying the input error message
        Parameters:
            error_message (str): The error message to be displayed in the popup window
    '''
    # Create tkinter window
    window = tk.Tk()

    # Set window title
    window.title('UPASS Setup Error')

    # Set window size & position
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    window_width = int(screen_width / 2.5)
    window_height = int(screen_height / 2)
    window.geometry(str(window_width) + 'x' + str(window_height))
    window.geometry('%dx%d+%d+%d' % (window_width, window_height, 0, 0))

    # Fill with labels
    label1 = Label(window, text="UPASS Setup Error Occured", font=("Helvetica", 18))
    label1.pack(ipady=10, anchor='center')


    label2 = Label(window, text='The details of the error are:', font=("Helvetica", 14))
    label2.pack(ipady=10)

    label3 = Label(window, text=error_message, font=("Helvetica", 13), wraplength=300, justify="center")
    label3.pack(ipady=50)

    label4 = Label(window, text='Please fix this error and then try running the setup again', font=("Helvetica", 10))
    label4.pack(ipady=30)

    window.mainloop()


def create_success_popup():
    '''
    Creates a new Tkinter popup window displaying text informing of a successful setup of UPASS
    '''
    # Create tkinter window
    window = tk.Tk()

    # Set window title
    window.title('UPASS Setup Error')

    # Set window size & position
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    window_width = int(screen_width / 2.5)
    window_height = int(screen_height / 3)
    window.geometry(str(window_width) + 'x' + str(window_height))
    window.geometry('%dx%d+%d+%d' % (window_width, window_height, 0, 0))

    # Fill with labels
    label1 = Label(window, text="UPASS Setup Complete", font=("Helvetica", 18))
    label1.pack(ipady=10, anchor='center')

    label3 = Label(window, text='UPASS has been setup successfully. You may now close this window and use UPASS.', font=("Helvetica", 13), wraplength=300, justify="center")
    label3.pack(ipady=50)

    window.mainloop()


def main():
    # Confirm package download complete
    if not path.exists(path.join('bin')) \
            or not path.exists(path.join('bin/cheating-website-list')) \
            or not path.isfile(path.join('bin/cheating-website-list/cheating_websites.csv')) \
            or not path.isfile('serpstack_api_access_key.txt') \
            or not path.isfile('google_sheet_name.txt') \
            or not path.isfile('gmail_username.txt') \
            or not path.isfile('gmail_password.txt') \
            or not path.exists(path.join('service-account-credentials')):
        create_error_popup('installation incomplete - try redownloading package')
        return


    # Confirm serpstack api key has been entered into serpstack_api_access_key.txt and is valid
    if not path.getsize('serpstack_api_access_key.txt') > 0:
        create_error_popup('serpstack api key not entered into serpstack_api_access_key.txt')
        return
    else:
        with open('serpstack_api_access_key.txt') as f:
            access_key = f.readlines()[0]
            params = {'access_key': access_key}
            api_result = requests.get('http://api.serpstack.com/search', params)
            if api_result.status_code != 200:
                create_error_popup('SerpStack API Response not received')
            else:
                if '"code": 101' in api_result.text:
                    create_error_popup('Serpstack API access key invalid')
                    return


    # Confirm google sheets name and credentials valid
    if not path.getsize('google_sheet_name.txt') > 0:
        create_error_popup('google sheets name not entered into google_sheets_name.txt')
        return
    else:
        with open('google_sheet_name.txt') as f:
            try:
                SHEET_NAME = f.readlines()[0]
                scopes = ['https://www.googleapis.com/auth/spreadsheets',
                    "https://www.googleapis.com/auth/drive.file",
                    "https://www.googleapis.com/auth/drive"]
                if 'json' in listdir('service-account-credentials')[0]:
                    cred_path = 'service-account-credentials/' + listdir('service-account-credentials')[0]
                else:
                    create_error_popup('Too many files in service-account-credentials folder')
                    return
                creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scopes)
                client = gspread.authorize(creds)
                sheet = client.open(SHEET_NAME).sheet1
                DATA_TO_PULL = 'Form Responses 1'
                sheet.spreadsheet.values_get(range=DATA_TO_PULL)
                data = sheet.spreadsheet.values_get(range=DATA_TO_PULL)
            except:
                create_error_popup('google sheets name or credentials invalid')
                return


    # Confirm gmail username and password valid
    if not path.getsize('gmail_username.txt') > 0:
        create_error_popup('gmail username not entered into gmail_username.txt')
        return
    if not path.getsize('gmail_password.txt') > 0:
        create_error_popup('gmail password not entered into gmail_password.txt')
        return
    else:
        with open('gmail_username.txt') as f:
            with open('gmail_password.txt') as g:
                try:
                    gmail_user = f.readlines()[0]
                    gmail_password = g.readlines()[0]
                    server = 'smtp.gmail.com:587'
                    server = smtplib.SMTP(server)
                    server.ehlo()
                    server.starttls()
                    server.login(gmail_user, gmail_password)
                    server.quit()

                    # Create directory for serp results and upass overview
                    if not path.exists(path.join('bin/serp-results')):
                        mkdir(path.join('bin/serp-results'))
                    if not path.exists(path.join('bin/upass-overview')):
                        mkdir(path.join('bin/upass-overview'))

                    # Create upass overview csv
                    if not path.isfile(path.join('bin/upass-overview/overview.csv')):
                        df = pd.DataFrame(list())
                        df.to_csv(path.join('bin/upass-overview/overview.csv'))

                    create_success_popup()

                except:
                    create_error_popup('gmail account details incorrect or less secure apps not enabled')


if __name__ == '__main__':
    main()