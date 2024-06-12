import os
import threading
from datetime import datetime
import random
import time
import localvars

mutex = threading.Lock()

def add_row_to_log(log_file, row_values):
    with open(log_file, 'a') as f:
        f.write("%s\n" % (",".join([str(x) for x in row_values])))

def generate_logs(name, log_path, row_function):
    while True:
        now = datetime.now()
        date_str = now.strftime("%d-%m-%y")
        file_date_str = now.strftime("%y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        date_dir = os.path.join(log_path, file_date_str)
        with mutex:
            if not os.path.exists(date_dir):
                os.makedirs(date_dir)

        if name in localvars.CHANNELS_WITH_UNDERSCORE:
            log_file = os.path.join(date_dir, f"{name}_{file_date_str}.log")
        else:
            log_file = os.path.join(date_dir, f"{name} {file_date_str}.log")


        row_values = row_function(date_str, time_str)
        add_row_to_log(log_file, row_values)
        #with open(log_file, 'a') as f:
        #    f.write("%s\n"%(",".join([str(x) for x in row_values])))

        time.sleep(random.randint(3,10))

def generate_multiple_logs(names, log_path, row_function):
    while True:
        now = datetime.now()
        date_str = now.strftime("%d-%m-%y")
        file_date_str = now.strftime("%y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        date_dir = os.path.join(log_path, file_date_str)
        with mutex:
            if not os.path.exists(date_dir):
                os.makedirs(date_dir)
        for name in names:
            if name in localvars.CHANNELS_WITH_UNDERSCORE:
                log_file = os.path.join(date_dir, f"{name}_{file_date_str}.log")
            else:
                log_file = os.path.join(date_dir, f"{name} {file_date_str}.log")

            row_values = row_function(date_str, time_str)
            add_row_to_log(log_file, row_values)

        time.sleep(random.randint(3,10))

def single_channel(date_str, time_str):
    return [date_str, time_str, random.random()*1000]

def kv_channel(date_str, time_str, keys=['one', 'two', 'three', 'four']):
    return [date_str, time_str] + sum([[k, random.random()*10] for k in keys],[])

def channel_channel(date_str, time_str, keys=['one', 'two', 'three']):
    return [date_str, time_str, 1] + sum([[k, random.random()*10] for k in keys],[])

LOG_PATH = 'test_logs'
logging_threads = []
#logging_threads.append(threading.Thread(target=generate_logs, args=('CH1 T',LOG_PATH,single_channel)))
#logging_threads.append(threading.Thread(target=generate_logs, args=('CH1 P',LOG_PATH,single_channel)))
#logging_threads.append(threading.Thread(target=generate_logs, args=('CH1 R',LOG_PATH,single_channel)))
logging_threads.append(threading.Thread(target=generate_multiple_logs, args=(['CH1 R','CH1 T','CH1 P'],LOG_PATH,single_channel)))
logging_threads.append(threading.Thread(target=generate_logs, args=('Flowmeter',LOG_PATH,single_channel)))
logging_threads.append(threading.Thread(target=generate_logs, args=('Channels',LOG_PATH,channel_channel)))
logging_threads.append(threading.Thread(target=generate_logs, args=('Status',LOG_PATH,kv_channel)))

for thread in logging_threads:
    thread.daemon = True
    thread.start()

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("Program terminated.")