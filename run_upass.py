from os import listdir, path, mkdir
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import ast
import time
import requests
from urllib.parse import urlparse
from prettytable import PrettyTable
from tldextract import extract
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib


# Gmail account details
from gmail_account_details import gmail_user, gmail_password # The login details of the upass gmail account


# Constants
NUM_SERP_RESULTS = 100 # Number of serp results saved for each search term
SEARCH_RANK_CHEATING_URL_THRESHOLD = 10 # Threshold for known cheating websites to be flagged
SEARCH_RANK_NONCHEATING_URL_THRESHOLD = 5 # Threshold for new websites to be flagged
UPASS_FORM_COLUMNS = ['Timestamp', 'Course Contact Name', 'Assignment Title', 'Assignment End Date',
           'Notification Email Address(es)', 'Search Term 1', 'Search Term 2', 'Search Term 3', 'Search Term 4',
           'Search Term 5', 'Search Term 6', 'Search Term 7', 'Search Term 8', 'Search Term 9', 'Search Term 10',
           'Search Term 11', 'Search Term 12', 'Search Term 13', 'Search Term 14', 'Search Term 15',
           'Search Term 16', 'Search Term 17', 'Search Term 18', 'Search Term 19', 'Search Term 20'] # The column names of the upass form response sheet
UPASS_OVERVIEW_COLUMNS = ['Assignment Title', 'Course Contact Name', 'Email Addresses', 'End Date', 'Search Terms'] # The column names of the upass overview csv file


# Global variables
upass_overview_csv_filepath = path.join('bin/upass-overview/overview.csv')


def import_upass_form_data():
    '''
    Returns a dataframe containing the upass google form responses

        Returns:
            upass_form_data_df (pd.DataFrame):      Dataframe containing each field of the upass form responses. Data columns are as follows:
            ============================================================================================================================
            Timestamp (str):                        The date and time of the response
            Course Contact Name (str):              The name submitted in the respective upass form question
            Assignment Title (str):                 The title of the assignment submitted in the respective upass form question
            Assignment End Date (str):              The end date of the assignment submitted in the respective upass form question in the form mm/dd/yyyy
            Notification Email Assress(es) (str):   The email addresses (one per line) f the assignment submitted in the respective upass form question
            Search Term 1 (str):                    A search term submitted in the respective upass form question
            Search Term 2 (str):                    A search term submitted in the respective upass form question
            Search Term 3 (str):                    A search term submitted in the respective upass form question
            ...
            ...
            ...
            Search Term 20 (str):                   A search term submitted in the respective upass form question
            ============================================================================================================================
    '''
    with open('google_sheet_name.txt') as f:
        try:
            SHEET_NAME = f.readlines()[0]
            scopes = ['https://www.googleapis.com/auth/spreadsheets',
                      "https://www.googleapis.com/auth/drive.file",
                      "https://www.googleapis.com/auth/drive"]
            cred_path = 'service-account-credentials/' + listdir('service-account-credentials')[0]
            creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scopes)
            client = gspread.authorize(creds)
            sheet = client.open(SHEET_NAME).sheet1
            DATA_TO_PULL = 'Form Responses 1'
            sheet.spreadsheet.values_get(range=DATA_TO_PULL)
            upass_form_data = sheet.spreadsheet.values_get(range=DATA_TO_PULL)['values']

            # Put the upass form response data into a dataframe
            for row in upass_form_data:
                if len(row) < len(UPASS_FORM_COLUMNS):
                    row += [''] * (len(UPASS_FORM_COLUMNS) - len(row))
            upass_form_data_df = pd.DataFrame(upass_form_data[1:], columns=UPASS_FORM_COLUMNS)
            return upass_form_data_df
        except:
            print('google sheets name or credentials invalid')
            return


def import_upass_overview_csv():
    '''
    Returns the upass overview csv file as a pd.DataFrame. This csv file contains the details of all the assignments which are in the upass backend
    '''
    upass_overview_df = pd.read_csv(upass_overview_csv_filepath)

    # If no assignments have been moved into upass overview csv file yet, give the overview df its column names
    if upass_overview_df.size == 0:
        upass_overview_df = pd.DataFrame(columns=UPASS_OVERVIEW_COLUMNS)

    return upass_overview_df


def find_new_assignment_details(upass_forms_data_df, upass_overview_df):
    '''
    Returns a dataframe containing the assignment details of the assignments which have been uploaded to the upass form
    but not moved into the upass backend (i.e. details moved into the the overview csv)

        Parameters:
            upass_forms_data_df (pd.DataFrame):     Dataframe containing each field of the upass form responses. Data columns are as follows:
            ============================================================================================================================
            Timestamp (str):                        The date and time of the response
            Course Contact Name (str):              The name submitted in the respective upass form question
            Assignment Title (str):                 The title of the assignment submitted in the respective upass form question
            Assignment End Date (str):              The end date of the assignment submitted in the respective upass form question in the form mm/dd/yyyy
            Notification Email Assress(es) (str):   The email addresses (one per line) f the assignment submitted in the respective upass form question
            Search Term 1 (str):                    A search term submitted in the respective upass form question
            Search Term 2 (str):                    A search term submitted in the respective upass form question
            Search Term 3 (str):                    A search term submitted in the respective upass form question
            ...
            ...
            ...
            Search Term 20 (str):                   A search term submitted in the respective upass form question
            ============================================================================================================================

            upass_overview_df (pd.DataFrame):       Dataframe containing the backend details of each assignment in upass. Data columns are as follows:
            ============================================================================================================================
            Assignment Title (str):                 The title of the assignment
            Course Contact Name (str):              The name of the course contact for the assignment
            Email Addresses (list[str]):            The notification email addresses for the assignment, one address per list item
            End Date (str):                         String representation of the assignment end date in the form dd/mm/yyyy
            Search Terms (list[str]):               The search terms for the assignment, one serch term per list item
            ============================================================================================================================

        Returns:
            all_new_assignments_df (pd.DataFrame):  Dataframe containing the details of all assignments which are in the upass_forms_data_df but not the upass_overview_df.
            Data columns are as follows:
            ============================================================================================================================
            Assignment Title (str):                 The title of the assignment
            Course Contact Name (str):              The name of the course contact for the assignment
            Email Addresses (list[str]):            The notification email addresses for the assignment, one address per list item
            End Date (str):                         String representation of the assignment end date in the form dd/mm/yyyy
            Search Terms (list[str]):               The search terms for the assignment, one serch term per list item
            ============================================================================================================================
    '''

    # Create empty df to fill with potential new assignment details
    all_new_assignments_df = pd.DataFrame(columns=upass_overview_df.columns)

    # Iterate over the form responses dataframe and extract new assignments details
    for index, row in upass_forms_data_df.iterrows():
        assignment_title = row['Assignment Title']
        if assignment_title not in list(upass_overview_df['Assignment Title']):
            assignment_title = row['Assignment Title']
            course_contact_name = row['Course Contact Name']
            email_addresses = row['Notification Email Address(es)'].split('\n')
            end_date = datetime.strptime(row['Assignment End Date'], '%m/%d/%Y').date().strftime('%d/%m/%Y')
            search_terms = []
            for column_name, column_value in row.iteritems():
                if 'Search Term' in column_name and column_value != '':
                    search_terms += [column_value]
            new_assignment_details = pd.DataFrame()
            new_assignment_details['Assignment Title'] = [assignment_title]
            new_assignment_details['Course Contact Name'] = [course_contact_name]
            new_assignment_details['Email Addresses'] = [str(email_addresses)]
            new_assignment_details['End Date'] = [end_date]
            new_assignment_details['Search Terms'] = [str(search_terms)]
            all_new_assignments_df = all_new_assignments_df.append(new_assignment_details)
    return all_new_assignments_df


def update_overview_csv(assignment_title, course_contact_name, email_addresses, end_date, search_terms,
                        upass_overview_df):
    '''
    Adds a new assignment's details into the upass overview csv

        Parameters:
            assignment_title (str):             The title of the assignment
            course_contact_name (str):          The name of the course contact for the assignment
            email_addresses (list[str]):        The notification email addresses for the assignment, one address per list item
            end_date (str):                     String representation of the assignment end date in the form dd/mm/yyyy
            search_terms (list[str]):           The search terms for the assignment, one serch term per list item
            upass_overview_df (pd.DataFrame):   Dataframe containing the backend details of each assignment in upass. Data columns are as follows:
            ============================================================================================================================
            Assignment Title (str):             The title of the assignment
            Course Contact Name (str):          The name of the course contact for the assignment
            Email Addresses (list[str]):        The notification email addresses for the assignment, one address per list item
            End Date (str):                     String representation of the assignment end date in the form dd/mm/yyyy
            Search Terms (list[str]):           The search terms for the assignment, one serch term per list item
            ============================================================================================================================
    '''
    new_details_df = pd.DataFrame()
    new_details_df[UPASS_OVERVIEW_COLUMNS[0]] = [assignment_title]
    new_details_df[UPASS_OVERVIEW_COLUMNS[1]] = [course_contact_name]
    new_details_df[UPASS_OVERVIEW_COLUMNS[2]] = str(email_addresses)
    new_details_df[UPASS_OVERVIEW_COLUMNS[3]] = datetime.strptime(end_date, '%d/%m/%Y').date().strftime('%d/%m/%Y')
    new_details_df[UPASS_OVERVIEW_COLUMNS[4]] = str(search_terms)

    # Drop duplicates if they exist in the overview before replacing
    if assignment_title in upass_overview_df['Assignment Title'].to_list():
        upass_overview_df = upass_overview_df.drop(
        upass_overview_df[assignment_title == upass_overview_df['Assignment Title']].index)
        print(assignment_title + ' duplticate removed in upass overview csv')

    # Append the new details
    upass_overview_df = upass_overview_df.append(new_details_df, ignore_index=True)
    upass_overview_df.to_csv(upass_overview_csv_filepath, index=False)
    print(assignment_title + ' has been uploaded into the overview csv')


def create_new_serp_directory(assignment_title):
    '''
    Creates a new directory where the serp results for the assignment will be saved
        Parameters:
            assignment_title (str): The title of the assignment
    '''
    if not path.exists(path.join('bin/serp-results/' + assignment_title)):
        mkdir(path.join('bin/serp-results/' + assignment_title))
        print('New serp results directory created for ' + assignment_title)
    else:
        print('New serp results directory could not be created for ' + assignment_title)


def get_urls_serpstack(search_term):
    '''
    Returns a list containing the serp result urls for input search query
        Parameters:
            search_term (str): The search term for which the serp results will be returned
        Returns:
            final_serp_result_urls (list[str]): A list containing the serp results. The first element is the url of the first serp result, the second element is the url of the second serp result, ...
    '''
    time.sleep(0.1)

    # Create serpstack request parameters
    with open('serpstack_api_access_key.txt') as f:
        access_key = f.readlines()[0]
        num_searches = NUM_SERP_RESULTS
        page = 1
        params = {
            'access_key': access_key,
            'num': num_searches,
            'page': page,
            'gl': 'au',
            'query': search_term
        }

    # Get serp results from serpstack
    api_result = requests.get('http://api.serpstack.com/search', params)
    api_response = api_result.json()

    # Notify user is API response is invalid
    if api_result.status_code != 200:
       print('Invalid API response for ' + search_term)

    # Extract the top search results up to the number set by NUM_SERP_RESULTS
    try:
        top_serp_results = api_response['organic_results'][0:NUM_SERP_RESULTS]
    except:
        top_serp_results = []

    # Extract the urls from the
    serp_result_urls = []
    for result in top_serp_results:
        serp_result_urls += [(result['url'])]

    # Fill to the number specified by NUM_SERP_RESULTS if needed
    final_serp_result_urls = []
    for i in range(NUM_SERP_RESULTS):
        if i < len(serp_result_urls):
            current_response = serp_result_urls[i]
            final_serp_result_urls += [current_response]
        else:
            final_serp_result_urls += ['no search result']

    return final_serp_result_urls


def create_serp_result_csv_files(search_terms, assignment_title):
    '''
    Creates a csv file containing the serp results for each search term for the assignment
        Paramenters:
            search_terms (list[str]):   The search terms for the assignment, one serch term per list item
            assignment_title (str):     The title of the assignment
    '''
    search_number = 1
    for search in search_terms:
        serp_results_df = pd.DataFrame()
        serp_urls = get_urls_serpstack(search)
        current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        serp_results_df[current_datetime] = serp_urls
        filepath = path.join('bin/serp-results/' + assignment_title + '/search' + str(search_number) + '.csv')
        serp_results_df.to_csv(filepath, index=False)
        search_number += 1
    print('Serp result csv files created for ' + assignment_title)


def unique(list1):
    '''
    Returns a list containing only the unique elements from the input list
    '''
    unique_list = []
    for x in list1:
        if x not in unique_list:
            unique_list.append(x)
    return unique_list


def find_initial_cheating_serp_urls(search_terms, assignment_title):
    '''
    Returns a list containing any urls from the serp results for the assignment which have a known cheating website domain
        Paramters:
            search_terms (list[str]):   The search terms for the assignment, one serch term per list item
            assignment_title (str):     The title of the assignment
        Returns:
            unique_serp_cheating_urls (list[str]): A list containing all the unique serp result urls from known cheating website domains for the assignment
    '''
    # Import the list of cheating website domains
    filepath = path.join('bin/cheating-website-list/cheating_websites.csv')
    cheating_domain_list = pd.read_csv(filepath)['domain'].tolist()

    # Lowercase the urls in the cheating domain list
    for i in range(len(cheating_domain_list)):
        cheating_domain_list[i] = cheating_domain_list[i].lower()

    # Create a list to save cheating serp result urls to
    serp_result_cheating_urls = []

    # Go through serp results and save cheating serp results urls
    search_number = 1
    for search in search_terms:
        # Open url ranks from csv
        filepath = path.join('bin/serp-results/' + assignment_title + '/search' + str(search_number) + '.csv')
        serpstack_ranks_df = pd.read_csv(filepath)

        # Extract the serp result urls as a list
        serpstack_urls = [serpstack_ranks_df[col_name].unique() for col_name in serpstack_ranks_df.columns][
            0].tolist()

        # Extract the domains from the urls
        serpstack_url_domains = []
        for url in serpstack_urls:
            domain = urlparse(url).netloc
            serpstack_url_domains += [domain]

        # Save the serp result urls and respective domains to a dataframe
        serpstack_url_df = pd.DataFrame(columns=['url', 'domain'])
        serpstack_url_df['url'] = serpstack_urls
        serpstack_url_df['domain'] = serpstack_url_domains

        # Find cheating domains below the rank threshold and save them
        for index, row in serpstack_url_df.iterrows():
            if index <= SEARCH_RANK_CHEATING_URL_THRESHOLD - 1:
                url = row['url']
                domain = row['domain']
                if domain in cheating_domain_list and '.xml' not in url:
                    serp_result_cheating_urls += [url]

        # Extract the unique urls
        unique_serp_cheating_urls = unique(serp_result_cheating_urls)
        search_number += 1

    if len(unique_serp_cheating_urls) == 0:
        print('SerpStack found no cheating matches')
    else:
        print('SerpStack found cheating matches')
    return unique_serp_cheating_urls


def send_upload_confirmation_notification_email(email_addresses, assignment_title, course_contact_name, unique_serp_cheating_urls, end_date):
    '''
    Sends an upload confirmation notification email to the course contact for the assignment
        Parameters:
            email_addresses (list[str]):        The notification email addresses for the assignment, one address per list item
            assignment_title (str):             The title of the assignment
            course_contact_name (str):          The name of the course contact for the assignment
            unique_serp_cheating_urls (list[str]): A list containing all the unique serp result urls from known cheating website domains for the assignment
            end_date (str):                     String representation of the assignment end date in the form dd/mm/yyyy
    '''

    # A list to save the domains of the cheating urls
    domains = []

    # Formatting email text depending on if cheating urls have been found for the assignment
    if len(unique_serp_cheating_urls) == 0: # No cheating urls identified
        text = """
                Dear {recipient},

                Your assignment, {assignment}, has been successfully uploaded to UPASS. UPASS will be monitoring for potential uploads of your assignment until {date}.

                Kind regards,
                UPASS:  Upload and Plagarise Alert SyStem

                To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.
                """
        html = """
            <html><body><p>Dear {recipient},</p>
            <p>Your assignment, {assignment}, has been successfully uploaded to UPASS. UPASS will be monitoring for potential uploads of your assignment until {date}.</p>
            <p>Kind regards,<br>
            UPASS:  Upload and Plagarise Alert SyStem</p>
            <p>To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.</p>
            </body></html>
            """
        text = text.format(recipient=course_contact_name, assignment=assignment_title, date=end_date)
        html = html.format(recipient=course_contact_name, assignment=assignment_title, date=end_date)

    else: # Cheaing urls identified
        # Create a table for the email containing the domain, webpage name, and url for each found cheating url
        tabular_fields = ["Domain", "Webpage Name", "Link"]
        tabular_table = PrettyTable()
        tabular_table.field_names = tabular_fields
        for url in unique_serp_cheating_urls:
            tsd, td, tsu = extract(url)
            domain = td + '.' + tsu
            domains += [domain]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            }
            html_page = requests.get(url, headers=headers).text
            soup = BeautifulSoup(html_page, "html.parser")
            try:
                title = soup.find('title').text
            except:
                title = 'Webpage name could not be found'
            tabular_table.add_row([domain, title, url])
        text = """
        Dear {recipient},

        Your assignment, {assignment}, has been successfully uploaded to UPASS. UPASS will be monitoring for potential uploads of your assignment until {date}. The following websites were identified as already containing information covered in your assignment.

        These are websites which are known for contract cheating.

        {table}

        Kind regards,
        UPASS:  Upload and Plagarise Alert SyStem

        To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.
        """
        html = """
    <html><body><p>Dear {recipient},</p>
    <p>Your assignment, {assignment}, has been successfully uploaded to UPASS. UPASS will be monitoring for potential uploads of your assignment until {date}. The following websites were identified as already containing information covered in your assignment.</p>
    <p>These are websites which are known as contract cheating websites.</p>
    {table}
    <p>Kind regards,<br>
    UPASS:  Upload and Plagarise Alert SyStem</p>
    <p>To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.</p>
    </body></html>
    """
        table_text = tabular_table
        table_html = table_text.get_html_string().replace('<table>', '<table border=1>')
        text = text.format(recipient=course_contact_name, assignment=assignment_title, table=table_text,
                           date=end_date)
        html = html.format(recipient=course_contact_name, assignment=assignment_title, table=table_html,
                           date=end_date)

    # Construct the MIMEMultipart email
    message = MIMEMultipart("alternative", None, [MIMEText(text), MIMEText(html, 'html')])
    message['Subject'] = 'UPASS Submission - ' + assignment_title + ' - Upload success'
    message['From'] = gmail_user
    message['To'] = ','.join(email_addresses)

    # Add removal of content instructions if there are cheating websites
    if len(domains) > 1:
        attachment_directory = path.join('bin/takedown-instructions/Removal of Content from Websites.pdf')
        with open(attachment_directory, "rb") as opened:
            opened_file = opened.read()
        attachedfile = MIMEApplication(opened_file, _subtype="pdf")
        attachedfile.add_header('content-disposition', 'attachment', filename='Removal of Content from Websites.pdf')
        message.attach(attachedfile)

    # Send confirmation notification email
    try:
        server = 'smtp.gmail.com:587'
        server = smtplib.SMTP(server)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, email_addresses, message.as_string())
        server.quit()
        print('New upload confirmation notification email sent for ' + assignment_title)
    except:
        print('Failed to send new upload notification email for ' + assignment_title)


def get_new_serp_results(search_terms, assignment_title):
    '''
    Finds the new serp results for an assignment, saves them to their respective serp results csv and returns a list containing all new serp results
       Paramters:
           search_terms (list[str]):   The search terms for the assignment, one serch term per list item
           assignment_title (str):     The title of the assignment
       Returns:
           new_serp_urls (list[str]):   A list containing all the new serp result urls for the assignment
       '''
    new_serp_urls = []
    search_number = 1
    for search in search_terms:
        new_serp_urls_for_search_term = get_urls_serpstack(search)
        new_serp_urls += new_serp_urls_for_search_term
        filepath = path.join('bin/serp-results/' + assignment_title + '/search' + str(search_number) + '.csv')
        updated_serpstack_urls_df = pd.read_csv(filepath)
        current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        updated_serpstack_urls_df[current_datetime] = new_serp_urls_for_search_term
        updated_serpstack_urls_df.to_csv(filepath, index=False)
        search_number += 1
    print('New serp ranks found and saved to csv for ' + assignment_title)
    return new_serp_urls


def upload_new_assignments_to_backend(all_new_assignments_df, upass_overview_df):
    '''
    Adds new assignment details into the upass backend, notifies course contacts that their assignments have been
    uploaded, and finds 4 sets of serp results for the assignments' search terms

        Parameters:

            all_new_assignments_df (pd.DataFrame):  Dataframe containing the details of all assignments which are in the upass_forms_data_df but not the upass_overview_df.
            Data columns are as follows:
            ============================================================================================================================
            Assignment Title (str):                 The title of the assignment
            Course Contact Name (str):              The name of the course contact for the assignment
            Email Addresses (list[str]):            The notification email addresses for the assignment, one address per list item
            End Date (str):                         String representation of the assignment end date in the form dd/mm/yyyy
            Search Terms (list[str]):               The search terms for the assignment, one serch term per list item
            ============================================================================================================================

            upass_overview_df (pd.DataFrame):       Dataframe containing the backend details of each assignment in upass. Data columns are as follows:
            ============================================================================================================================
            Assignment Title (str):                 The title of the assignment
            Course Contact Name (str):              The name of the course contact for the assignment
            Email Addresses (list[str]):            The notification email addresses for the assignment, one address per list item
            End Date (str):                         String representation of the assignment end date in the form dd/mm/yyyy
            Search Terms (list[str]):               The search terms for the assignment, one serch term per list item
            ============================================================================================================================
    '''

    # Do nothing if there are no new assignments
    if len(all_new_assignments_df) == 0:
        return
    # Perform necessary functions for all new assignments
    else:
        for indew, row in all_new_assignments_df.iterrows():
            #Extract assignment details
            assignment_title = row['Assignment Title']
            course_contact_name = row['Course Contact Name']
            email_addresses = ast.literal_eval(row['Email Addresses'])
            end_date = row['End Date']
            search_terms = ast.literal_eval(row['Search Terms'])

            # Add assignment details into upass overview csv
            update_overview_csv(assignment_title, course_contact_name, email_addresses, end_date, search_terms,
                                upass_overview_df)

            # Create a new directory to save the serp results for the assignment
            create_new_serp_directory(assignment_title)

            # Get the serp results for each question and create csv containing them
            create_serp_result_csv_files(search_terms, assignment_title)

            # Find any cheating websites in the serp results for the assignment
            unique_serp_cheating_urls = find_initial_cheating_serp_urls(search_terms, assignment_title)

            # Send upload confirmation notification email to assignment contact person
            send_upload_confirmation_notification_email(email_addresses, assignment_title, course_contact_name,
                                                        unique_serp_cheating_urls, end_date)

            # Get 3 more sets of serp results for the assignment (necessary for upass non-cheating url identification)
            for i in range(3):
                get_new_serp_results(search_terms, assignment_title)


def get_previous_serp_urls(assignment_title, search_terms):
    '''
    Returns a list containing all the previous serp result urls for the assignment's search terms
        Paramters:
            assignment_title (str):                 The title of the assignment
            search_terms (list[str]):               The search terms for the assignment, one serch term per list item
        Returns:
            previous_serpstack_urls (list[str]):    A list containing all the urls of the previous serp results, one url per list element
    '''
    # Create a list to hold all previous serp results
    previous_serpstack_urls = []
    for search_number in range(len(search_terms)):
        search_number += 1
        # Read in the previous serp results for the search term
        filepath = path.join('bin/serp-results/' + assignment_title + '/search' + str(search_number) + '.csv')
        initial_serpstack_ranks_df = pd.read_csv(filepath)
        for column in initial_serpstack_ranks_df:
            # Convert the previous results for the search term to a list and append it to the list of all previous serp results
            previous_serpstack_urls += initial_serpstack_ranks_df[column].to_list()
    # Remove the 'no search result' elements in the list, leaving only urls
    previous_serpstack_urls = [x for x in previous_serpstack_urls if "no search result" not in x]
    return previous_serpstack_urls


def identify_new_cheating_urls(new_serp_urls, previous_serp_urls):
    '''
    Returns a list containing new urls from the serp results for the assignment which have a known cheating website domain
        Parameters:
            new_serp_urls (list[str]):              A list containing all the new serp result urls for the assignment
            previous_serpstack_urls (list[str]):    A list containing all the urls of the previous serp results, one url per list element
        Returns:
            new_cheating_urls (list[str]):          A list containing the identified new cheating urls
    '''

    # Import the list of cheating website domains
    filepath = path.join('bin/cheating-website-list/cheating_websites.csv')
    cheating_domain_list = pd.read_csv(filepath)['domain'].tolist()

    # Lowercase the urls in the cheating domain list
    for i in range(len(cheating_domain_list)):
        cheating_domain_list[i] = cheating_domain_list[i].lower()

    # Create a list to save the new cheating serp result urls to
    serp_result_cheating_urls = []

    # Extract the urls within the search rank threshold for all search terms
    new_serp_urls_within_cheating_threshold = []
    num_search_terms = int(len(new_serp_urls) / NUM_SERP_RESULTS)
    for i in range(num_search_terms):
        min_index = NUM_SERP_RESULTS*i
        max_index = min_index + SEARCH_RANK_CHEATING_URL_THRESHOLD
        new_serp_urls_within_cheating_threshold += new_serp_urls[min_index:max_index]

    # Extract only new urls within the search rank threshold for all search terms
    for url in new_serp_urls_within_cheating_threshold:
        if url not in previous_serp_urls:
            serp_result_cheating_urls += [url]

    # Identify which new urls have a cheating domain and save them
    new_cheating_serp_urls = []
    for url in serp_result_cheating_urls:
        domain = urlparse(url).netloc
        if domain in cheating_domain_list and '.xml' not in url:
            new_cheating_serp_urls += [url]

    return new_cheating_serp_urls


def identify_non_cheating_url_matches(new_serp_urls, previous_serp_urls):
    '''
    Returns a list containing new urls from the serp results for the assignment which have a known cheating website domain
        Parameters:
            new_serp_urls (list[str]):              A list containing all the new serp result urls for the assignment
            previous_serpstack_urls (list[str]):    A list containing all the urls of the previous serp results, one url per list element
        Returns:
            new_non_cheating_urls (list[str]):          A list containing the identified new cheating urls
    '''
    # Import the list of cheating website domains
    filepath = path.join('bin/cheating-website-list/cheating_websites.csv')
    cheating_domain_list = pd.read_csv(filepath)['domain'].tolist()

    # Lowercase the urls in the cheating domain list
    for i in range(len(cheating_domain_list)):
        cheating_domain_list[i] = cheating_domain_list[i].lower()

    # Create a list to save the new non cheating serp result urls to
    serp_result_non_cheating_urls = []

    # Extract the urls within the search rank threshold for all search terms
    new_serp_urls_within_non_cheating_threshold = []
    num_search_terms = int(len(new_serp_urls) / NUM_SERP_RESULTS)
    for i in range(num_search_terms):
        min_index = NUM_SERP_RESULTS * i
        max_index = min_index + SEARCH_RANK_NONCHEATING_URL_THRESHOLD
        new_serp_urls_within_non_cheating_threshold += new_serp_urls[min_index:max_index]

    # Extract urls which have a non-cheating domain
    for url in new_serp_urls_within_non_cheating_threshold:
        domain = urlparse(url).netloc
        if domain not in cheating_domain_list and '.xml' not in url:
            serp_result_non_cheating_urls += [url]

    # Extract the never before seen urls from the non-cheating urls within the search rank threshold
    new_non_cheating_urls = []
    for url in serp_result_non_cheating_urls:
        if url not in previous_serp_urls:
            new_non_cheating_urls += [url]

    # Remove any 'no search result' urls which may have been identified through the algorithm
    new_non_cheating_urls[:] = [x for x in new_non_cheating_urls if "no search result" not in x]

    return new_non_cheating_urls


def send_new_match_notification_email(email_addresses, assignment_title, course_contact_name, new_cheating_serp_urls, new_non_cheating_serp_urls, end_date):
    '''
    Sends an new match notification email to the course contact for the assignment
        Parameters:
            email_addresses (list[str]):        The notification email addresses for the assignment, one address per list item
            assignment_title (str):             The title of the assignment
            course_contact_name (str):          The name of the course contact for the assignment
            new_cheating_serp_urls (list[str]):      A list containing the identified new cheating urls
            new_non_cheating_urls (list[str]):  A list containing the identified new cheating urls
            end_date (str):                     String representation of the assignment end date in the form dd/mm/yyyy
    '''

    # Ensure no duplicate urls in url lists
    new_cheating_serp_urls = list(set(new_cheating_serp_urls))
    new_non_cheating_serp_urls = list(set(new_non_cheating_serp_urls))

    # Generate the body of the email depending on the type of urls identified
    # No urls identified
    if len(new_cheating_serp_urls) == 0 and len(new_non_cheating_serp_urls) == 0:
        return

    # Only cheating urls identified websites
    elif len(new_cheating_serp_urls) != 0 and len(new_non_cheating_serp_urls) == 0:
        # Create a table for the email containing the domain, webpage name, and url for each found cheating url
        tabular_fields = ["Domain", "Webpage Name", "Link"]
        tabular_table = PrettyTable()
        tabular_table.field_names = tabular_fields
        for url in new_cheating_serp_urls:
            tsd, td, tsu = extract(url)
            domain = td + '.' + tsu
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            }
            html_page = requests.get(url, headers=headers).text
            soup = BeautifulSoup(html_page, "html.parser")
            try:
                title = soup.find('title').text
            except:
                title = 'Webpage name could not be found'
            tabular_table.add_row([domain, title, url])
        text = """
                Dear {recipient},

                UPASS has been monitoring for potential uploads of your assignment, {assignment}.  The following has been detected:

                Likely uploads
                These are websites which are known for contract cheating.  When UPASS detects a match for one of these websites, it is classified as a likely upload.

                {table}

                UPASS will continue to monitor for uploads until {date}.

                Kind regards,
                UPASS:  Upload and Plagarise Alert SyStem

                To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.
                """
        html = """
            <html><body><p>Dear {recipient},</p>
            <p>UPASS has been monitoring for potential uploads of your assignment, {assignment}.  The following has been detected:</p>
            <p><b>Likely uploads</b><br>
            These are websites which are known for contract cheating.  When UPASS detects a match one for of these websites, it is classified as a likely upload.</p>
            {table}
            <p>UPASS will continue to monitor for uploads until {date}.</p>
            <p>Kind regards,<br>
            UPASS:  Upload and Plagarise Alert SyStem</p>
            <p>To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.</p>
            </body></html>
            """
        table_text = tabular_table
        table_html = table_text.get_html_string().replace('<table>', '<table border=1>')
        text = text.format(recipient=course_contact_name, assignment=assignment_title, table=table_text,
                           date=end_date)
        html = html.format(recipient=course_contact_name, assignment=assignment_title, table=table_html,
                           date=end_date)

    # Only non-cheating urls identified
    elif len(new_cheating_serp_urls) == 0 and len(new_non_cheating_serp_urls) != 0:
        # Create a table for the email containing the domain, webpage name, and url for each found non-cheating url
        tabular_fields = ["Domain", "Webpage Name", "Link"]
        tabular_table = PrettyTable()
        tabular_table.field_names = tabular_fields
        for url in new_non_cheating_serp_urls:
            tsd, td, tsu = extract(url)
            domain = td + '.' + tsu
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            }
            try:
                html_page = requests.get(url, headers=headers).text
                soup = BeautifulSoup(html_page, "html.parser")
                title = soup.find('title').text
            except:
                title = 'Webpage name could not be found'
            tabular_table.add_row([domain, title, url])
        text = """
                Dear {recipient},

                    UPASS has been monitoring for potential uploads of your assignment, {assignment}.  The following has been detected:

                    Potential uploads
                    These are websites which are not known for contract cheating.  When UPASS detects a match for one of these websites, it is classified as a potential upload. These are probably not matches, but have been highlighted to you for your consideration.

                    {table}

                    UPASS will continue to monitor for uploads until {date}.

                    Kind regards,
                    UPASS:  Upload and Plagarise Alert SyStem

                    To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.
                    """
        html = """
                <html><body><p>Dear {recipient},</p>
                <p>UPASS has been monitoring for potential uploads of your assignment, {assignment}.  The following has been detected:</p>
                <p><b>Potential uploads</b><br>
                These are websites which are <u>not</u> known for contract cheating.  When UPASS detects a match for one of these websites, it is classified as a potential upload. These are probably not matches, but have been highlighted to you for your consideration.</p>
                {table}
                <p>UPASS will continue to monitor for uploads until {date}.</p>
                <p>Kind regards,<br>
                UPASS:  Upload and Plagarise Alert SyStem</p>
                <p>To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.</p>
                </body></html>
                """
        table_text = tabular_table
        table_html = table_text.get_html_string().replace('<table>', '<table border=1>')
        text = text.format(recipient=course_contact_name, assignment=assignment_title, table=table_text,
                               date=end_date)
        html = html.format(recipient=course_contact_name, assignment=assignment_title, table=table_html,
                               date=end_date)

    # Both cheating and non-cheating urls identified
    elif len(new_cheating_serp_urls) != 0 and len(new_non_cheating_serp_urls) != 0:
        # Create 2 tables for the email containing the domain, webpage name, and url for the cheating and non-cheating urls identified
        tabular_fields = ["Domain", "Webpage Name", "Link"]
        tabular1_table = PrettyTable()
        tabular1_table.field_names = tabular_fields
        for url in new_cheating_serp_urls:
            tsd, td, tsu = extract(url)
            domain = td + '.' + tsu
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            }
            try:
                html_page = requests.get(url, headers=headers).text
                soup = BeautifulSoup(html_page, "html.parser")
                title = soup.find('title').text
            except:
                title = 'Webpage name could not be found'
            tabular1_table.add_row([domain, title, url])
        tabular2_table = PrettyTable()
        tabular2_table.field_names = tabular_fields
        for url in new_non_cheating_serp_urls:
            tsd, td, tsu = extract(url)
            domain = td + '.' + tsu
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            }
            try:
                html_page = requests.get(url, headers=headers).text
                soup = BeautifulSoup(html_page, "html.parser")
                title = soup.find('title').text
            except:
                title = 'Webpage name could not be found'
            tabular2_table.add_row([domain, title, url])
        text = """
                Dear {recipient},

                    UPASS has been monitoring for potential uploads of your assignment, {assignment}.  The following has been detected:

                    Likely uploads
                    These are websites which are not known for contract cheating.  When UPASS detects a match for one of these websites, it is classified as a potential upload..

                    {table1}

                    Potential uploads
                    These are websites which are not known for contract cheating.  When UPASS detects a match for one of these websites, it is classified as a potential upload. These are probably not matches, but have been highlighted to you for your consideration.

                    {table2}

                    UPASS will continue to monitor for uploads until {date}.

                    Kind regards,
                    UPASS:  Upload and Plagarise Alert SyStem

                    To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.
                    """
        html = """
                <html><body><p>Dear {recipient},</p>
                <p>UPASS has been monitoring for potential uploads of your assignment, {assignment}.  The following has been detected:</p>
                <p><b>Likely uploads</b><br>
                These are websites which are known for contract cheating.  When UPASS detects a match for one of these websites, it is classified as a likely upload.</p>
                {table1}
                <br>
                <p><b>Potential uploads</b><br>
                These are websites which are <u>not</u> known for contract cheating.  When UPASS detects a match for one of these websites, it is classified as a potential upload. These are probably not matches, but have been highlighted to you for your consideration.</p>
                {table2}
                <p>UPASS will continue to monitor for uploads until {date}.</p>
                <p>Kind regards,<br>
                UPASS:  Upload and Plagarise Alert SyStem</p>
                <p>To UNSUBSCRIBE from this notification, reply to this email with UNSUBSCRIBE in the subject line.</p>
                </body></html>
                """
        table1_text = tabular1_table
        table1_html = table1_text.get_html_string().replace('<table>', '<table border=1>')
        table2_text = tabular2_table
        table2_html = table2_text.get_html_string().replace('<table>', '<table border=1>')
        text = text.format(recipient=course_contact_name, assignment=assignment_title, table1=table1_text,
                               table2=table2_text, date=end_date)
        html = html.format(recipient=course_contact_name, assignment=assignment_title, table1=table1_html,
                           table2=table2_html, date=end_date)

    # Construct the MIMEMultipart email
    message = MIMEMultipart("alternative", None, [MIMEText(text), MIMEText(html, 'html')])
    message['Subject'] = 'UPASS Notification - ' + assignment_title + ' - Potential uploaded detected'
    message['From'] = gmail_user
    message['To'] = ','.join(email_addresses)

    # Add removal of content instructions
    attachment_directory = path.join('bin/takedown-instructions/Removal of Content from Websites.pdf')
    with open(attachment_directory, "rb") as opened:
        opened_file = opened.read()
    attachedfile = MIMEApplication(opened_file, _subtype="pdf")
    attachedfile.add_header('content-disposition', 'attachment', filename='Removal of Content from Websites.pdf')
    message.attach(attachedfile)

    # Send new match notification email
    try:
        server = 'smtp.gmail.com:587'
        server = smtplib.SMTP(server)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, email_addresses, message.as_string())
        server.quit()
        print('New upload notification email sent for ' + assignment_title)
    except:
        print('Failed to send new upload notification email for ' + assignment_title)


def daily_check_on_backend_assignments(upass_overview_df):
    '''
    Performs the daily checks on the assignments in the UPASS backend.
    For assignments which have not reached their end date, new serp results are found and saved, and if required, nofitication emails
    are sent to their respective contacts.
        Parameters:
            upass_overview_df (pd.DataFrame):       Dataframe containing the backend details of each assignment in upass. Data columns are as follows:
            ============================================================================================================================
            Assignment Title (str):                 The title of the assignment
            Course Contact Name (str):              The name of the course contact for the assignment
            Email Addresses (list[str]):            The notification email addresses for the assignment, one address per list item
            End Date (str):                         String representation of the assignment end date in the form dd/mm/yyyy
            Search Terms (list[str]):               The search terms for the assignment, one serch term per list item
            ============================================================================================================================
    '''

    # Read over each assignment in the upass backend
    for index, row in upass_overview_df.iterrows():
        # Extract assignment details
        assignment_title = row['Assignment Title']
        course_contact_name = row['Course Contact Name']
        email_addresses = ast.literal_eval(row['Email Addresses'])
        end_date = row['End Date']
        search_terms = ast.literal_eval(row['Search Terms'])

        # Check whether the assignment has reached its end date
        if datetime.today().date() >= datetime.strptime(end_date, '%d/%m/%Y').date():
            print('End date reached for ' + assignment_title + '. It will no longer be checked by UPASS.')

        else:
            print('End date not reached for ' + assignment_title + '. Commencing UPASS checks.')

            # Read in previous serp results for the assignment
            previous_serp_urls = get_previous_serp_urls(assignment_title, search_terms)

            # Get new serp results and update serp result csv files
            new_serp_urls = get_new_serp_results(search_terms, assignment_title)

            # Find new cheating urls from known cheating website domains
            new_cheating_serp_urls = identify_new_cheating_urls(new_serp_urls, previous_serp_urls)

            # Find new non-cheating urls using upass algorithm
            new_non_cheating_serp_urls = identify_non_cheating_url_matches(new_serp_urls, previous_serp_urls)

            # Send notification email to assignment contact person
            send_new_match_notification_email(email_addresses, assignment_title, course_contact_name,
                                              new_cheating_serp_urls, new_non_cheating_serp_urls, end_date)


def main():
    # Read upass assignment search term submission google form data
    upass_forms_data_df = import_upass_form_data()

    # Read in the upass overview csv file
    upass_overview_df = import_upass_overview_csv()

    # Find all new assignments details
    all_new_assignments_df = find_new_assignment_details(upass_forms_data_df, upass_overview_df)

    # Upload new assignments to upass backend and notify course contacts via upload confirmation email
    upload_new_assignments_to_backend(all_new_assignments_df, upass_overview_df)

    # Perform the daily checks on assignments in the upass backend  and send notification emails as required
    daily_check_on_backend_assignments(upass_overview_df)


if __name__ == '__main__':
    main()