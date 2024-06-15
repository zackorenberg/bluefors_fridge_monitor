"""
Class that deals with log data
"""
from Core.fileMonitor import *

from PyQt5 import QtCore

class LogChannel:
    def __init__(self, channel, log_path=LOG_PATH):
        self.fd = None
        self.fname = None
        self.date = None
        self.channel = channel

        self.labels = []
        self.data = []
        self.last_data = {}
        self.last_time = None

        self.log_path = log_path



    def update_path_information(self, date = None):
        if date:
            self.date = date
        if self.channel in CHANNELS_WITH_UNDERSCORE:
            self.fname = f'{self.channel}_{self.date}.log'
        else:
            self.fname = f'{self.channel} {self.date}.log'


        return self.fname

    def open(self, date = None):
        if date:
            self.date = date
        self.close()
        self.date = self.date
        self.update_path_information(self.date)
        self.fd = open(os.path.join(self.log_path, self.date, self.fname), 'r')


    def update(self):
        if not self.fd:
            return None, None
        flines = [l.strip(' \t\r\n').split(',') for l in self.fd.readlines()]# if l[-1] == '\n']

        if len(flines) == 0:
            return None, None
        processed = process_log_file_lines(flines, channel=self.channel, date=self.date)
        data, labels = process_log_file_rows(processed, channel=self.channel, date=self.date)
        self.labels = labels
        self.data += (list(data.items()))
        if len(self.data) > MAXIMUM_DATAPOINT_HISTORY:
            self.data = self.data[-MAXIMUM_DATAPOINT_HISTORY:]

        last_time, last_data = get_last_entry(data, labels)

        self.last_time = last_time
        self.last_data = last_data
        return self.last_time, self.last_data

    def close(self):
        if self.fd:
            self.fd.close()
            self.fd = None

    def __del__(self):
        self.close()


class FileManager(QThread):
    processedChanges = QtCore.pyqtSignal(dict)
    allData = QtCore.pyqtSignal(dict)
    def __init__(self, log_path=LOG_PATH):
        super().__init__()
        self.logChannels = {}
        self.overseer = Overseer()
        self.overseer.changeSignal.connect(self.changeDetected)
        self.latest_log_files = load_all_possible_log_files(log_path)
        for channel, date in self.latest_log_files.items():
            #print(channel, date)
            if channel in CHANNEL_BLACKLIST:
                continue
            self.logChannels[channel] = LogChannel(channel, log_path)
            self.logChannels[channel].open(date)
            self.logChannels[channel].update()
            self.logChannels[channel].close()

        self.last_emitted_changes = {}
        self.most_recent_changes = {}

        self.changes_read = {}

    def emitData(self):
        self.allData.emit(self.dumpData())

    def dumpData(self):
        return {ch:lc.data for ch,lc in self.logChannels.items()}
    def run(self):
        self.overseer.start()
        while True:
            logging.debug("Looping")
            if len(self.changes_read.keys()) > 0:
                logging.debug("Pending changes emitting")
                self.last_emitted_changes = self.changes_read
                self.changes_read = {}
                self.processedChanges.emit(self.last_emitted_changes)
                self.most_recent_changes.update(self.last_emitted_changes)
            time.sleep(CHANGE_PROCESS_CHECK)

    def stop(self):
        self.overseer.stop()
        self.overseer.join()

    def __del__(self):
        for channel, logChannel in self.logChannels.items():
            logChannel.close()

    def changeDetected(self, change, channel, date):
        logging.debug("Change detected")
        if channel not in self.logChannels:
            logging.error(f"Channel {channel} not found in log channels")
            return
        if self.logChannels[channel].date != date:
            self.logChannels[channel].update_path_information(date)
        if not self.logChannels[channel].fd:
            self.logChannels[channel].open()
        time, data = self.logChannels[channel].update()
        if channel not in self.changes_read:
            self.changes_read[channel] = {}
        self.changes_read[channel].update({time:data})

    def currentStatus(self):
        return {ch: (lc.last_time, lc.last_data) for ch, lc in self.logChannels.items()}

    def mostRecentChanges(self):
        return self.most_recent_changes


if __name__ == "__main__":
    from PyQt5.QtWidgets import QMainWindow, QTextEdit, QVBoxLayout, QWidget, QApplication
    import sys


    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Watchdog and PyQt5 Integration")
            self.resize(800, 600)

            self.text_edit = QTextEdit()
            layout = QVBoxLayout()
            layout.addWidget(self.text_edit)

            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

            self.file_watcher_thread = FileManager()
            self.file_watcher_thread.processedChanges.connect(self.on_processed_changed)
            self.file_watcher_thread.start()

            self.data = (self.file_watcher_thread.dumpData())

        def on_processed_changed(self, change_dict):
            #print(change_dict)
            self.text_edit.append(str(change_dict))

        def closeEvent(self, event):
            self.file_watcher_thread.stop()
            self.file_watcher_thread.join()
            event.accept()


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())