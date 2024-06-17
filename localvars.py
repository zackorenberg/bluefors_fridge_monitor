CONFIG_FILE = 'config'
CONFIG_MANDATORY_FIELDS = ['LOG_PATH', 'RECIPIENTS', 'SENDER', 'PASSWORD', 'SMTP_SERVER', 'SMTP_PORT']
CONFIG_OPTIONAL_FIELDS = ['CHANNEL_BLACKLIST', 'VERBOSE', 'DEBUG_MODE']

LOG_PATH = ''
CALIBRATION_PATH = None
RECIPIENTS = []
SENDER = ''
PASSWORD = ''
SMTP_SERVER = ''
SMTP_PORT = -1

# TODO: turn this into a class so can be dynamically changed with gui

import os
ROOT_DIR = os.path.dirname(__file__)
"""
with open(os.path.join(ROOT_DIR, CONFIG_FILE), 'r') as f:
    lines = f.readlines()
    lines = [l for l in lines if l[0] != ';'] # Those are comments!
    # Set LOG_PATH
    try:
        LOG_PATH = [l.strip(' \n\t') for l in lines if 'LOG_PATH' in l][0].split('LOG_PATH=')[1]
        RECIPIENTS = [l.strip(' \n\t') for l in lines if 'RECIPIENTS' in l][0].split('RECIPIENTS=')[1].split(',')
        SENDER = [l.strip(' \n\t') for l in lines if 'SENDER' in l][0].split('SENDER=')[1]
        PASSWORD = [l.strip(' \n\t') for l in lines if 'PASSWORD' in l][0].split('PASSWORD=')[1]
        SMTP_SERVER = [l.strip(' \n\t') for l in lines if 'SMTP_SERVER' in l][0].split('SMTP_SERVER=')[1]
        SMTP_PORT = int([l.strip(' \n\t') for l in lines if 'SMTP_PORT' in l][0].split('SMTP_PORT=')[1])
    except KeyError:
        print("Invalid configuration file")
        exit(0)
"""



VERBOSE = True  # TODO: implement this stuff
DEBUG_MODE = False

SUBCHANNEL_DELIMITER = ':'

KV_CHANNELS = ['heaters', 'Status']
ERROR_CHANNEL = ['Errors']
MAXIGAUGE_CHANNEL = ['maxigauge']
VALVECONTROL_CHANNEL = ['Channels']

CHANNELS_WITH_UNDERSCORE = ['heaters', 'Status']

CHANNEL_BLACKLIST = [f'CH{d+1} T' for d in range(7,16)] + [f'CH{d+1} R' for d in range(7,16)] +[f'CH{d+1} P' for d in range(7,16)]


SUFFIX_FORMAT = "%y-%m-%d.log"
DATE_FORMAT = "%y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

THERMOMETRY_CHANNELS = [f'CH{d+1} T' for d in range(7)] + [f'CH{d+1} R' for d in range(7)] +[f'CH{d+1} P' for d in range(7)]

VALVE_CHANNELS = ['Channels']
PRESSURE_CHANNELS = ['Flowmeter', 'maxigauge']
STATUS_CHANNELS = ['Status', 'Errors']
HEATER_CHANNELS = ['heaters']

MONITOR_CHANNELS = {
    'Thermometry':THERMOMETRY_CHANNELS,
    'Valves':VALVE_CHANNELS,
    'Pressure and Flow':PRESSURE_CHANNELS,
    'Status':STATUS_CHANNELS,
    'Heaters':HEATER_CHANNELS,
}


TABULATE_TABLE_FMT = 'fancy_grid'  # See here for options: https://pypi.org/project/tabulate/
INDENT_EMAIL_INFORMATION = False

MAXIMUM_DATAPOINT_HISTORY = 300
MAX_COLLAPSEABLE_HEIGHT = 400

FIX_CONSOLE_HEIGHT = True
FIX_ACTIVE_WIDTH = True

SEND_TEST_EMAIL_ON_LAUNCH = False

SPLIT_MONITOR_WIDGETS = True # This will make it so monitor selector is left, active monitors are right, and console is full bottom
# If false, monitor will be top left, console will be bottom left, and active monitor will be entirely right

CHANGE_PROCESS_CHECK = 1 # Number of seconds between checking for changes (We do this instead of immediate processing because many files sometimes get modified concurrently and we want as accurate a result as possible when a monitor goes off