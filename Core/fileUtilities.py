import os
from localvars import *
from datetime import datetime

def load_calibration_dates(log_path = LOG_PATH, omit_empty_directories=True):
    dircontents = os.listdir(log_path)
    folders = []
    for file in dircontents:
        if os.path.isdir(os.path.join(log_path, file)):
            try:
                datetime.strptime(file, '%y-%m-%d')
                folders.append(file)
            except ValueError:
                continue
    folders = [f for f in folders if len(os.listdir(os.path.join(log_path, f))) or not omit_empty_directories]
    return folders

def load_all_possible_log_files(log_path = LOG_PATH):
    folders = load_calibration_dates(log_path=log_path)
    unique_files = []
    last_logs = {}
    for folder in folders:
        suffix = f"{folder}.log"
        files = [f for f in os.listdir(os.path.join(log_path, folder)) if f[-len(suffix):] == suffix]
        files = [f[:-len(suffix)].strip('_ ') for f in files]
        last_logs.update({f:folder for f in files})# if f in unique_files}) # add most recent ones to last logs dictionary
        unique_files += [f for f in files if f not in unique_files]

    return dict(sorted(last_logs.items(), key=lambda x:x[0]))
