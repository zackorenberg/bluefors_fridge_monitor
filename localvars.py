CONFIG_FILE = 'config'

LOG_PATH = None
CALIBRATION_PATH = None
RECIPIENTS = None
SENDER = None
PASSWORD = None

# TODO: turn this into a class so can be dynamically changed with gui
import os
dir = os.path.dirname(__file__)
with open(os.path.join(dir, CONFIG_FILE), 'r') as f:
    lines = f.readlines()
    # Set LOG_PATH
    try:
        LOG_PATH = [l.strip(' \n\t') for l in lines if 'LOG_PATH' in l][0].split('LOG_PATH=')[1]
        RECIPIENTS = [l.strip(' \n\t') for l in lines if 'RECIPIENTS' in l][0].split('RECIPIENTS=')[1].split(',')
        SENDER = [l.strip(' \n\t') for l in lines if 'SENDER' in l][0].split('SENDER=')[1]
        PASSWORD = [l.strip(' \n\t') for l in lines if 'PASSWORD' in l][0].split('PASSWORD=')[1]
    except KeyError:
        print("Invalid configuration file")
        exit(0)




VERBOSE = True  # TODO: implement this stuff
DEBUG_MODE = True

SUBCHANNEL_DELIMITER = ':'

KV_CHANNELS = ['heaters', 'Status']
ERROR_CHANNEL = ['Error']
MAXIGAUGE_CHANNEL = ['maxigauge']
VALVECONTROL_CHANNEL = ['Channels']

CHANNELS_WITH_UNDERSCORE = ['heaters', 'Status']

CHANNEL_BLACKLIST = [f'CH{d+1} T' for d in range(7,16)] + [f'CH{d+1} R' for d in range(7,16)] +[f'CH{d+1} P' for d in range(7,16)]


SUFFIX_FORMAT = "%y-%m-%d.log"
DATE_FORMAT = "%y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

THERMOMETRY_CHANNELS = [f'CH{d+1} T' for d in range(7)] + [f'CH{d+1} R' for d in range(7)] +[f'CH{d+1} P' for d in range(7)]

VALVE_CHANNELS = ['Flowmeter', 'maxigauge', 'Channels']
STATUS_CHANNELS = ['Status', 'heaters']

MONITOR_CHANNELS = {
    'Thermometry':THERMOMETRY_CHANNELS,
    'Valve':VALVE_CHANNELS,
    'Status':STATUS_CHANNELS
}


TABULATE_TABLE_FMT = 'fancy_grid'  # See here for options: https://pypi.org/project/tabulate/
INDENT_EMAIL_INFORMATION = False

MAXIMUM_DATAPOINT_HISTORY = 300
MAX_COLLAPSEABLE_HEIGHT = 400


CHANGE_PROCESS_CHECK = 1 # Number of seconds between checking for changes (We do this instead of immediate processing because many files sometimes get modified concurrently and we want as accurate a result as possible when a monitor goes off