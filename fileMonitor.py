from localvars import *

import os
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logger
logging = logger.Logger(__file__)

import time

from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QObject


from fileUtilities import *
from fileReader import *


class LogFileWatchdog(FileSystemEventHandler, QObject):
    changeSignal = pyqtSignal(str, str, str)
    def __init__(self):
        super().__init__()


    def on_created(self, event):
        fname = event.src_path.split(os.sep)[-1]
        channel = fname[:-len(SUFFIX_FORMAT)].strip(' _')
        date = fname[-len(SUFFIX_FORMAT):][:-4] # to get rid of the .log extension
        self.changeSignal.emit('created', channel, date)

    def on_modified(self, event):
        fname = event.src_path.split(os.sep)[-1]
        channel = fname[:-len(SUFFIX_FORMAT)].strip(' _')
        date = fname[-len(SUFFIX_FORMAT):][:-4]  # to get rid of the .log extension
        self.changeSignal.emit('modified', channel, date)



class Overseer(QThread):
    changeSignal = pyqtSignal(str, str, str)
    def __init__(self, log_path = LOG_PATH):
        super().__init__()
        self.date = datetime.now().strftime(DATE_FORMAT)
        self.date = '24-06-10'
        self.log_path = log_path
        self.logFileWatchdog = LogFileWatchdog()
        self.logFileWatchdog.changeSignal.connect(self.changeSignal)

        self.observer = Observer()
        self.schedule = None

    def run(self):
        if os.path.exists(os.path.join(self.log_path, self.date)):
            self.schedule = self.observer.schedule(self.logFileWatchdog, os.path.join(self.log_path, self.date), recursive=False)
            logging.debug(f"Schedule: {str(self.schedule)}")
        self.observer.start()
        while True:
            current_date = datetime.now().strftime(DATE_FORMAT)
            if current_date != self.date or self.schedule is None:
                if not os.path.exists(os.path.join(self.log_path, current_date)):
                    logging.warning(f"Date changed to {current_date} but folder does not exist yet, trying again later")
                    time.sleep(2)
                    continue
                logging.warning(f"Date changed to {current_date}")
                self.date = current_date
                self.observer.unschedule_all()
                self.schedule = self.observer.schedule(self.logFileWatchdog, os.path.join(self.log_path, self.date), recursive=False)

            time.sleep(1)

    def stop(self):
        self.observer.stop()
        self.observer.join()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QMainWindow, QTextEdit, QVBoxLayout, QWidget, QApplication
    import sys
    class MainThread(QThread):
        mainSignal = pyqtSignal(str, str, str)
        def __init__(self):
            super().__init__()
            self.overseer = Overseer(log_path='tests/test_logs')
            self.overseer.changeSignal.connect(self.callback)

        def run(self):
            self.overseer.run()

        def stop(self):
            self.overseer.stop()
            self.overseer.join()

        def callback(self, *args):
            print(args)
            self.mainSignal.emit(*args)

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

            self.file_watcher_thread = MainThread()
            self.file_watcher_thread.mainSignal.connect(self.on_file_changed)
            self.file_watcher_thread.start()

        def on_file_changed(self, change, channel, date):
            logging.debug(f"{change}, {channel}, {date}")
            self.text_edit.append(f"File {change}: {date} {channel}")

        def closeEvent(self, event):
            self.file_watcher_thread.stop()
            event.accept()


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":

    class MainThread(QThread):
        mainSignal = pyqtSignal(str, str, str)
        def __init__(self):
            super().__init__()
            self.overseer = Overseer(log_path='tests/test_logs')
            self.overseer.changeSignal.connect(self.callback)

        def run(self):
            self.overseer.run()

        def stop(self):
            self.overseer.stop()
            self.overseer.join()

        def callback(self, *args):
            print(args)
            self.mainSignal.emit(*args)

    def test(*args):
        print(args)

    mt = MainThread()
    mt.mainSignal.connect(test)
    mt.run()

    while True:
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            mt.stop()
            mt.join()
            break

    exit(0)

    print(load_all_possible_log_files())

    current_date = datetime.now().strftime(DATE_FORMAT)
    overseer = Overseer(log_path='tests/test_logs')
    overseer.run()

    while True:
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            overseer.stop()
            overseer.join()
            break
    exit(0)
    folders = load_calibration_dates()
    handler = LogFileWatchdog()
    observer = Observer()
    observer.schedule(handler, os.path.join(LOG_PATH, folders[-1]), recursive=False)
    observer.start()
    while True:
        time.sleep(1)
    print(folders)