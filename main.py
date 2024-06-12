import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from localvars import *
from GUI.monitorWidget import *
from GUI.collapsibleBox import *
from fileMonitor import *
import queue

change_queue = queue.Queue()

def make_collapsibleBoxes(logChannels):
    collapsibles = {
        'thermometry':{
            'box':CollapsibleBox('Thermometry'),
            'channels':[],
            'layout':QtWidgets.QVBoxLayout(),
        },
        'valves':{
            'box':CollapsibleBox('Valves'),
            'channels':[],
            'layout':QtWidgets.QVBoxLayout(),
        },
        'status':{
            'box':CollapsibleBox('Status'),
            'channels':[],
            'layout':QtWidgets.QVBoxLayout(),
        },
    }
    for channel, logChannel in logChannels.items():
        if channel in THERMOMETRY_CHANNELS:
            print(logChannel.last_data)

# should run in a thread https://stackoverflow.com/questions/25108321/how-to-return-value-from-function-running-by-qthread-and-queue
class QueueLogFileWatchdog(LogFileWatchdog):
    def __init__(self, date, log_path=LOG_PATH, queue=change_queue):
        super().__init__(date, log_path=log_path)
        self.queue = queue

    def process_changes(self, channel, time, data):
        if time and data:
            self.queue.put({time:data})




if __name__ == "__main__":
    import sys
    import random

    current_date = datetime.now().strftime(DATE_FORMAT)
    overseer = Overseer(current_date)

    logChannels = overseer.logFileWatchdog.logChannels
    collapsibles = make_collapsibleBoxes(logChannels)

    exit(0)
    overseer.start()
    app = QtWidgets.QApplication(sys.argv)

    w = QtWidgets.QMainWindow()

    w.show()
    overseer.stop()
    overseer.terminate()
    sys.exit(app.exec_())