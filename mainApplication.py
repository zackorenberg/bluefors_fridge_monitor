from PyQt5 import QtWidgets
from Core.fileManager import *



class MainWidget(QtWidgets.QWidget):
    def __init__(self, fileManager, parent=None):
        super().__init__(parent=None)

        self.mainLayout =

class MainApplication(QtWidgets.QMainWindow):
    changeSignal = QtCore.pyqtSignal(str)

    def __init__(self, log_path=LOG_PATH):

        self.fileManager = FileManager(log_path)
        self.mainWidget = MainWidget(self.fileManager)

