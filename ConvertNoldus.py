from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askdirectory
import os
import pandas as pd
import numpy as np


def pandas_import_csv(csv_name):
    # READ HEADER:
    h = pd.read_csv(csv_name, sep=',', header=0, quoting=2, na_values='-', nrows=1, encoding='utf16')
    number_of_header_lines = int(h.keys()[1])
    header = pd.read_csv(csv_name, sep=',', header=0, quoting=2, na_values='-', nrows=number_of_header_lines-3
                         , encoding='utf16')
    skip = list(np.arange(0, number_of_header_lines-2))
    skip.append(number_of_header_lines-1)
    cf = pd.read_csv(csv_name, sep=',', header=0, skiprows=skip, quoting=2, na_values='-', encoding='utf16')
    return cf, header


def pandas_import_protocol(csv_name):
    skip = list(np.arange(0, 34))
    skip.append(35)
    cf = pd.read_csv(csv_name, sep=',', header=0, skiprows=skip, quoting=2, na_values='-', encoding='utf16')
    return cf


def compute_distance_moved(x, y):
    # input: two lists of Y and Y coordinates per sample point
    d_moved = np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2)
    return d_moved


def open_data():
    global protocol
    global data_set

    app_label.configure(text='Importing Data ... Please Wait ...')

    # BROWSE DIRECTORY
    dir_path = askdirectory()

    raw_data_path = f'{dir_path}/'

    filenames = next(os.walk(raw_data_path), (None, None, []))[2]  # [] if no file
    # Validation (is input valid?)
    if not filenames:
        print('ERROR')
        messagebox.showerror(
            title='ERROR',
            message='Could not find any files! Make sure to select the correct directory.'
        )
        app_label.configure(text='Please Open some data ...')
        protocol = None
        data_set = None
        return
    # get data files (txt files that start with 'Track')
    data_files_names = [i for i in filenames if i.startswith('Track')]
    # Get protocol file (We will take just the first one since all are the same)
    p_dummy = [i for i in filenames if i.startswith('Trial')]

    # Validation (is input valid?)
    if not data_files_names or not p_dummy:
        messagebox.showerror(
            title='ERROR',
            message='Could not find any text files! Make sure that text files start with "Track" and "Trial"'
        )
        app_label.configure(text='Please Open some data ...')
        protocol = None
        data_set = None
        return
    protocol_file_name = p_dummy[0]

    # Open CSV data files
    data_set = {}  # dict of all panda data frames

    for count, val in enumerate(data_files_names):
        well_nr = val[-16:-14]  # This the number of the specific well (exp. 'D4')
        csv_path = f'{raw_data_path}{data_files_names[count]}'
        data_set[well_nr], _ = pandas_import_csv(csv_path)

    # Open Protocol CSV file
    protocol_path = f'{raw_data_path}{protocol_file_name}'
    protocol = pandas_import_protocol(protocol_path)

    # Change Text to show that data has been loaded
    app_label.configure(text='Data has been successfully loaded!')

    # Configure the Button to trigger a new event
    main_btn.configure(text='CONVERT DATA', command=convert_txt)
    re_ope_btn = Button(app, text='Open new data', width=12, command=open_data)
    re_ope_btn.grid(row=1, column=1, pady=20)


def convert_txt():
    global protocol
    global data_set

    app_label.configure(text='Converting Data ... Please Wait ...')
    # Check if there is valid data available
    if protocol is None or data_set is None:
        messagebox.showerror(
            title='ERROR',
            message='Please open some data, first!'
        )
        app_label.configure(text='Please Open some data ...')
        return
    # Compute distance moved from the x and y coordinates
    distance_moved = {}
    for k in data_set:
        X = data_set[k]['X center']
        Y = data_set[k]['Y center']
        dummy = compute_distance_moved(X, Y)
        distance_moved[k] = np.insert(dummy, 0, 0)  # add a zero since there is no diff at the start

    # Find Stimulus Time Points
    idx_stimulus = protocol['Action'].notnull()
    stimuli_non_unique = pd.concat([protocol[idx_stimulus]['Recording time'], protocol[idx_stimulus]['Action']], axis=1)
    stimuli = stimuli_non_unique.drop_duplicates(subset='Recording time')

    # PUT ALL DATA INTO ONE EXCEL FILE
    # Time; Stimulus, Distance Moved (A1) ...

    data_wells = list(distance_moved.keys())
    rows = len(distance_moved[data_wells[0]])
    cols = len(data_wells)
    data_export = np.zeros([rows, cols])

    # Add Recording Time
    recording_time = data_set[data_wells[0]]['Recording time']
    # recording_time_df = pd.DataFrame(recording_time, columns=['Time'])

    # Add Stimulus onset times
    index_stimulus = []
    stimulus_col = [np.nan] * rows
    for i in stimuli['Recording time']:
        index_stimulus.append(np.where(recording_time == i))

    count2 = 0
    for i in stimuli['Action']:
        stimulus_col[index_stimulus[count2][0][0]] = i
        count2 += 1
    stimulus_col = pd.DataFrame(stimulus_col, columns=['Stimulus'])

    count = 0
    for k in distance_moved:
        data_export[:, count] = distance_moved.get(k)
        count += 1

    # Convert to Panda Data Frame
    # col_names = ['Time', 'Stimulus'] + data_wells
    data_frame = pd.DataFrame(data_export, columns=data_wells)
    data_frame = pd.concat([recording_time, stimulus_col, data_frame], axis=1)

    # Replace all NaN Values with Zero
    data_frame = data_frame.fillna(0)
    msg = messagebox.askyesno(title='Save', message='Save Data?')
    if msg:
        save_path = askdirectory()
        if save_path:
            # Store as csv files
            data_frame.to_csv(f'{save_path}/distance_moved.csv')
            protocol.to_csv(f'{save_path}/protocol.csv')
        else:
            protocol = None
            data_set = None
            app_label.configure(text='Please Open some data ...')
    app_label.configure(text='Please Open some data ...')
    protocol = None
    data_set = None


def about():
    messagebox.showinfo('Info', 'With this little tool you can convert NOLDUS text files containing coordinates into'
                                ' the distance moved (csv file) \n \n Author: Nils Brehm -- 2022')


# Global Variables
protocol = None
data_set = None

# Splash Screen
try:
    import pyi_splash
    # Update the text on the splash screen
    pyi_splash.update_text("Starting Program")
    # Close the splash screen. It does not matter when the call
    # to this function is made, the splash screen remains open until
    # this function is called or the Python program is terminated.
    pyi_splash.close()
except:
    pass

# Create a window object
app = Tk()
app.iconbitmap("icon.ico")

# Window Dimensions
w = 600  # width
h = 200  # height

# get screen width and height
ws = app.winfo_screenwidth()  # width of the screen
hs = app.winfo_screenheight()  # height of the screen

# calculate x and y coordinates for the Tk root window
x = (ws/2) - (w/2)
y = (hs/2) - (h/2)

# configure the grid
app.columnconfigure(0, weight=1)
app.columnconfigure(1, weight=1)

# Text
app_label = Label(app, text='Press Button to select and convert your data (folder with only txt files)',
                  font=('bold', 14), pady=20, padx=20)
app_label.grid(row=0, column=0, sticky=W)  # Align to left: W for West

# Buttons
main_btn = Button(app, text='OPEN', width=12, command=open_data)
main_btn.grid(row=1, column=0, pady=20)

# Menu
menu = Menu(app)
app.config(menu=menu)
file_menu = Menu(menu)
menu.add_cascade(label="Info", menu=file_menu)
file_menu.add_command(label="Info", command=about)
file_menu.add_command(label="Exit", command=app.quit)

app.title('Convert Noldus Raw Data')
# set the dimensions of the screen
# and where it is placed
app.geometry('%dx%d+%d+%d' % (w, h, x, y))

# Start program
app.mainloop()

