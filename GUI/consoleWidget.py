### This widget makes a copy of whats printed to standard output to a glorified text edit
from PyQt5 import QtCore, QtWidgets, QtGui
import sys



class Printerceptor(QtCore.QObject): # Basically tee but emits a signal instead
    printToConsole = QtCore.pyqtSignal(str)

    def __init__(self, output_file = None):
        super().__init__()
        self.old_stdout = sys.stdout
        self.fname = output_file

    def __del__(self): # Restore stdout
        sys.stdout = sys.__stdout__

    def write(self, string):
        # Write to output
        self.old_stdout.write(string)
        # Write to possible log file
        if self.fname:
            with open(self.fname, 'a') as f:
                f.write(string)
        # Emit signal
        self.printToConsole.emit(string)

    def flush(self):
        self.old_stdout.flush()


class ConsoleWidget(QtWidgets.QWidget):
    printToConsole = QtCore.pyqtSignal(str)
    widgetResize = QtCore.pyqtSignal()
    def __init__(self):
        super().__init__()
        self.printToConsole.connect(self.consoleText)

        self.consoleTextEdit = QtWidgets.QTextEdit()
        self.consoleTextEdit.setReadOnly(True)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.addWidget(self.consoleTextEdit)
        self.setLayout(self.verticalLayout)


    def consoleText(self, string = None):
        """ get/set function of console box """
        if string is None:
            return str(self.consoleTextEdit.toPlainText())
        else:
            self.consoleTextEdit.setPlainText(self.consoleText() + str(string))
            self.automaticScroll()

    def automaticScroll(self):
        """ automatically scrolls so latest message is present """
        sb = self.consoleTextEdit.verticalScrollBar()
        sb.setValue(sb.maximum())

    #def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
    #    super().resizeEvent(a0)
    #    self.widgetResize.emit()