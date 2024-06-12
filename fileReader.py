# Similar to log file reader program, but with more specific use cases
from localvars import *
import os
from datetime import datetime

class LogFile:
    def __init__(self, channel, date, data, labels, log_path = LOG_PATH):
        if channel in CHANNELS_WITH_UNDERSCORE:
            self.fname = f'{channel}_{date}.log'
        else:
            self.fname = f'{channel} {date}.log'

        self.data = data
        self.labels = labels
        print(self.data)
        self.times = list(sorted(self.data.keys()))

        self.log_path = log_path

    @classmethod
    def FromFile(cls, channel, date, log_path = LOG_PATH):
        data, labels = read_log_file(channel, date, log_path=log_path)
        return cls(channel, date, data, labels, log_path=log_path)

    def getLastLine(self):
        if len(self.times) > 0:
            return {self.times[-1]:self.data[self.times[-1]]}, self.labels




def process_log_file_lines(lines, channel, date):
    """
    process raw lines from the file into an array with a time stamp and converted values (int/float/etc)

    :param lines: array of lines read directly from file
    :param channel: log file channel
    :param date: date
    :return: array of lines in proper formats
    """
    processed = []
    for line in lines:
        try:
            t = datetime.strptime(f'{line[0]} {line[1]}', '%d-%m-%y %H:%M:%S').timestamp()
            values = [t]
            for val in line[2:]:
                try:
                    try:
                        values.append(int(val))
                    except ValueError:
                        values.append(float(val))
                except ValueError:
                    values.append(val)
            processed.append(values)
        except ValueError as e:
            print(f"Read error {date}/{channel}: {str(e)}")
    return processed

def process_log_file_rows(processed, channel, date):
    """

    :param channel: log file channel
    :param processed: processed lines of the file
    :return: {} processed rows
    """
    data = {}
    labels = []
    if channel in MAXIGAUGE_CHANNEL:
        for row in processed:
            # each channel has 6 columns, 2 are strings describing the channel/gauge and 4 are values and status
            # data[row[0]] = {(a + b).strip(' '): [c, d, e, f] for a, b, c, d, e, f in zip(*[row[(i + 1)::6] for i in range(6)])} <= dont need status just value
            data[row[0]] = {(a + b).strip(' '): d for a, b, _, d, _, _ in zip(*[row[(i + 1)::6] for i in range(6)])}
        labels = list(data[row[0]].keys())

    elif channel in ERROR_CHANNEL:
        for row in processed:
            time_dt = datetime.fromtimestamp(row[0])
            time_str = time_dt.strftime('%d-%m-%y,%H:%M:%S')
            if time_str in ",".join(row[1:]):  # We have two errors
                errors = [x.strip(',').split(",") for x in (",".join(row[1:])).split(time_str)]
                data[row[0]] = [{error[0]:error[1:]} for error in errors]
            else:
                data[row[0]] = [{row[1]: row[2:]}]

    elif channel in KV_CHANNELS:
        for row in processed:
            data[row[0]] = {k: v for k, v in zip(row[1::2], row[2::2])}
        labels = list(data[row[0]].keys())

    elif channel in VALVECONTROL_CHANNEL: # has weird first entry which I have no idea what it represents
        for row in processed:
            data[row[0]] = {k: v for k, v in zip(row[2::2], row[3::2])}
            data[row[0]]['void'] = row[1] # Phantom value
        labels = list(data[row[0]].keys())


    else: # Just a normal log file with a date and a value
        for row in processed:
            data[row[0]] = row[1]
            if len(row) > 2:
                print(f"Warning, extra value found in {date}/{channel}, omitting")
            labels = ['value']

    return data, labels



def read_log_file(channel, date, log_path = LOG_PATH):
    suffix = f'{date}.log'

    if channel in CHANNELS_WITH_UNDERSCORE:
        fname = f'{channel}_{date}.log'
    else:
        fname = f'{channel} {date}.log'


    with open(os.path.join(log_path, date, fname), 'r') as f:
        flines = [l.strip(' \t\r\n').split(',') for l in f.readlines() if l[-1] == '\n']

    processed = process_log_file_lines(flines, channel=channel, date=date)


    # We need to check what type of file it is
    return process_log_file_rows(processed, channel=channel, date=date)

def get_last_entry(data, labels):
    """
    Determines last entry from data/labels format
    """
    times = sorted(data.keys())
    if len(times) > 0:
        return times[-1], data[times[-1]]

if __name__ == "__main__":
    from tabulate import tabulate
    data, labels = read_log_file('Channels', '24-06-03')
    lf = LogFile.FromFile('Channels', '24-06-03')
    #data, label = lf.getLastLine()
    array = [[k] + list(v.values()) for k,v in data.items()]

    print(tabulate(array, headers=['time']+labels))

    print([v['void'] for k,v in data.items()])
