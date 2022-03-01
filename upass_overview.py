import tkinter as tk
from tkinter import ttk
import pandas as pd
import ctypes
from os import path
from datetime import datetime
import ast


def main():
    '''
    Displays a Tkinter window containing the details of all the assignments in the UPASS backend
    '''
    # Create tkinter GUI
    window = tk.Tk()

    # Set window title
    window.title('Assignment Upload Overview')

    # Set window size & position
    user32 = ctypes.windll.user32
    screen_width = user32.GetSystemMetrics(0)
    screen_height = user32.GetSystemMetrics(1)
    window_width = int(screen_width / 1.1)
    window_height = int(screen_height / 1.5)
    window.geometry(str(window_width) + 'x' + str(window_height))
    window.geometry('%dx%d+%d+%d' % (window_width, window_height, 0, 0))

    def load_excel_data():
        '''
        Loads the data from the overview.csv file into a treeview widget
        '''
        overview_filepath = path.join('bin/upass-overview/overview.csv')
        overview = pd.read_csv(overview_filepath)
        tv["column"] = list(overview.columns)
        tv["show"] = "headings"
        for column in tv["columns"]:
            tv.heading(column, text=column)
        overview_rows = overview.to_numpy().tolist()
        for row in overview_rows:
            tv.insert("", "end", values=row)
        return None

    def num_assignments():
        '''
        Returns the number of active assignments in the UPASS backend and the total number of search terms for these
        '''
        overview_filepath = path.join('bin/upass-overview/overview.csv')
        overview_df = pd.read_csv(overview_filepath)
        num_current_assignments = 0
        all_search_terms = []
        for index, row in overview_df.iterrows():
            end_date = row['End Date']
            search_terms = ast.literal_eval(row['Search Terms'])
            if not datetime.today().date() >= datetime.strptime(end_date, '%d/%m/%Y').date():
                num_current_assignments += 1
                all_search_terms += search_terms
        return num_current_assignments, len(all_search_terms)

    # Frame for TreeView
    num_current_assignments, num_all_search_terms = num_assignments()
    frame = tk.LabelFrame(window, text="There are " + str(num_current_assignments) + " assignments in UPASS "
        "which have not reached their end date for a total of " + str(num_all_search_terms) + " search terms",
        font=('Helvetica', 13))
    frame.place(height=window_height, width=window_width, )

    ## Treeview Widget
    tv = ttk.Treeview(frame)
    tv.place(relheight=1, relwidth=1)

    treescrolly = tk.Scrollbar(frame, orient="vertical", command=tv.yview)
    treescrollx = tk.Scrollbar(frame, orient="horizontal", command=tv.xview)
    tv.configure(xscrollcommand=treescrollx.set, yscrollcommand=treescrolly.set)
    treescrollx.pack(side="bottom", fill="x")
    treescrolly.pack(side="right", fill="y")

    load_excel_data()
    window.mainloop()

if __name__ == '__main__':
    main()