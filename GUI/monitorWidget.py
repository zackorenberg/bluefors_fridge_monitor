from PyQt5 import QtCore, QtWidgets, Qt
from datetime import datetime
import localvars
import logger

logging = logger.Logger(__file__)

from Core.valueMonitors import *


class MonitorWidgetSelect(QtWidgets.QWidget):
    uiChanged = QtCore.pyqtSignal()
    monitorStatusChange = QtCore.pyqtSignal(bool)
    def __init__(self, parent=None):
        self.parent = parent
        super().__init__()

        #self.main_layout = QtWidgets.QGridLayout()
        self.main_layout = QtWidgets.QHBoxLayout()

        self.monitorStatusChange.connect(self.monitorStatusChangeCallback)

        self.monitor_checkbox = QtWidgets.QComboBox()
        self.monitor_checkbox.addItem('Select Monitor Type')
        self.monitor_checkbox.addItems(MONITORS.keys())
        self.monitor_checkbox.setPlaceholderText('Select Monitor Type')
        cb_width = self.monitor_checkbox.sizeHint().width()
        self.monitor_checkbox.setFixedWidth(cb_width)
        self.monitor_checkbox.currentTextChanged.connect(self.monitorTypeChanged)
        #self.monitor_checkbox.setStyleSheet("padding: 0")
        #self.main_layout.addWidget(self.monitor_checkbox, 0, 0, QtCore.Qt.AlignLeft)
        self.main_layout.addWidget(self.monitor_checkbox, QtCore.Qt.AlignLeft)

        #self.main_layout.addWidget(self.monitor_checkbox, 0, QtCore.Qt.AlignLeft)
        #self.main_layout.addWidget(self.value_widget)

        #self.setContentsMargins(0,0,0,0)
        self.main_layout.setContentsMargins(0,0,0,0)
        #self.setStyleSheet("padding: 0")

        self.variables_type = {}
        self.variables_text = {}

        self.current_monitor = None

        self.setLayout(self.main_layout)

        # TODO: You can add extra stuff from monitor edit here, simply need to make a new function to getComments() or something (that returns nothing by default), then have it emit with changes in MonitorWidget with the rest by calling the function

    def monitorTypeChanged(self, event):
        for _, w in self.variables_text.items():
            self.main_layout.removeWidget(w)
        self.current_monitor = None
        self.variables_type = {}
        self.variables_text = {}
        if event in MONITORS:
            self.current_monitor = event
            obj = MONITORS[event]
            col = 1
            for varname, type in obj['variables'].items():
                self.variables_type[varname] = type
                self.variables_text[varname] = QtWidgets.QLineEdit()
                self.variables_text[varname].setPlaceholderText(varname)
                #self.main_layout.addWidget(QtWidgets.QLabel(varname), 0, col)
                #self.main_layout.addWidget(self.variables_text[varname], 0, col)
                self.main_layout.addWidget(self.variables_text[varname])
                col += 1
        #self.main_layout.update()
        #self.adjustSize()
        self.uiChanged.emit()

    def monitorStatusChangeCallback(self, status):
        self.monitor_checkbox.setEnabled(not status)
        for varname, line in self.variables_text.items():
            line.setEnabled(not status)

    def getType(self):
        text = self.monitor_checkbox.currentText()
        if text in MONITORS:
            return MONITORS[text]['type']

    def getMonitorType(self):
        return self.current_monitor

    def getVariableValues(self):
        text = self.monitor_checkbox.currentText()
        ret = {}
        if text in MONITORS:
            for varname, type in MONITORS[text]['variables'].items():
                try:
                    ret[varname] = type(self.variables_text[varname].text())
                except ValueError:
                    ret[varname] = None
        return ret



    def sizeHint(self):
        self.main_layout.update()
        self.updateGeometry()
        return self.main_layout.totalSizeHint()
        return self.main_layout.sizeHint()


    def monitorChange(self, obj):
        if obj['name'] != self.monitor_checkbox.currentText():
            self.monitor_checkbox.setCurrentText(obj['name'])
            # Should automatically generate whats needed by calling the state change
            # Force it just in case
            self.monitorTypeChanged(obj['name'])
            for varname, lineedit in self.variables_text.items():
                try:
                    lineedit.setText(str(obj['variables'][varname]))
                except Exception as e:
                    logging.error(f"{obj['name']}: Cannot change {varname} value: {str(e)}")

    """
    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)

        self.adjustSize()
    """



class MonitorWidget(QtWidgets.QWidget):
    monitorSignal = QtCore.pyqtSignal(dict)  # OUTGOING - When changes occur internally
    monitorChange = QtCore.pyqtSignal(dict)  # INCOMING - When changes occur externally
    uiChanged = QtCore.pyqtSignal()
    def __init__(self, name, channel, subchannel = None, parent = None, parse_function = lambda x: str(x), justify=None):
        super().__init__()
        self.name = name
        self.channel = channel
        self.subchannel = subchannel
        self.parent = parent
        self.parse_function = parse_function
        self.checkbox = QtWidgets.QCheckBox()

        self.monitor_label = QtWidgets.QLabel()
        self.monitor_change = QtWidgets.QLabel()
        self.monitor_value = QtWidgets.QLabel()
        self.monitor_label.setText(name)

        self.monitorChange.connect(self.monitorChangeCallback)

        self.monitor_type = MonitorWidgetSelect(self)
        self.monitor_type.uiChanged.connect(self.uiChangedCallback)
        self.monitor_type.uiChanged.connect(self.uiChanged)

        if justify:
            self.monitor_label.setFixedWidth(6 * justify)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.checkbox, 0, QtCore.Qt.AlignLeft)
        self.mainLayout.addWidget(self.monitor_label, 0, QtCore.Qt.AlignLeft)
        self.mainLayout.addWidget(self.monitor_change, 0, QtCore.Qt.AlignLeft)
        self.mainLayout.addWidget(self.monitor_value, 0, QtCore.Qt.AlignLeft)
        self.mainLayout.addWidget(self.monitor_type, 0, QtCore.Qt.AlignLeft)

        self.mainLayout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding))
        self.mainLayout.setContentsMargins(0,0,0,0)
        #self.mainLayout.setStretch(4, Qt.QSizePolicy.Expanding)

        self.setLayout(self.mainLayout)
        self.adjustSize()

        self.checkbox.stateChanged.connect(self.onCheckBoxToggle)

    def onCheckBoxToggle(self, event):
        if self.monitor_type.getMonitorType() not in MONITORS:
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(False)
            self.checkbox.setCheckState(QtCore.Qt.CheckState.Unchecked)
            self.checkbox.blockSignals(False)
            return
        checked = self.checkbox.isChecked()
        self.monitor_type.monitorStatusChange.emit(checked)
        change = {
            'monitor':self.name,
            'channel':self.channel,
            'subchannel':self.subchannel,
            'active':checked,
            'type':self.monitor_type.getType(), # 'range' or 'fixed'
            'name':self.monitor_type.getMonitorType(),
            'variables':self.monitor_type.getVariableValues(), # tuple for range, value for fixed
            'values':MONITORS[self.monitor_type.getMonitorType()]['values']
        }

        self.monitorSignal.emit(change)
        #if hasattr(self.parent, 'monitorSignal'):
        #    self.parent.monitorSignal.emit(change) bad practice
        #else:
        #    logging.error("No parent signal detected, monitor will not do anything")

    def changeValue(self, time, value):
        if time is None or value is None:
            logging.warning(f'Invalid time or value for channel {self.channel + (":"+self.subchannel if self.subchannel else "")}: {time}, {value}')

        dt = datetime.fromtimestamp(time)
        time_str = dt.strftime(f"{localvars.DATE_FORMAT}, {localvars.TIME_FORMAT}:")
        self.monitor_change.setText(str(time_str))
        self.monitor_value.setText(self.parse_function(value))
        self.resetSize()

    def resetSize(self):
        self.mainLayout.update()
        w = self.mainLayout.sizeHint().width()
        self.setMinimumWidth(w) #this actually would work if the collapsableBox would resize as well!
        #self.setMaximumWidth(w)

    def uiChangedCallback(self):
        #self.monitor_label.setText(self.monitor_label.text())
        #self.monitor_change.setText(self.monitor_change.text())
        #self.monitor_value.setText(self.monitor_value.text())
        #self.parent.main_layout.addStretch()
        self.resetSize()
        self.adjustSize()

    def monitorChangeCallback(self, obj):
        if not all([
            obj['monitor'] == self.name,
            obj['channel'] == self.channel,
            (obj['subchannel'] == self.subchannel) or (obj['subchannel'] is None and self.subchannel is None),
        ]):
            # This monitor wasnt changed
            return
        #print("Working")
        # We need to apply changes
        if obj['active'] != self.checkbox.checkState():
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(obj['active'])
            self.checkbox.setCheckState(
                QtCore.Qt.CheckState.Checked if obj['active'] else QtCore.Qt.CheckState.Unchecked
            )
            self.checkbox.blockSignals(False)

        self.monitor_type.monitorStatusChange.emit(obj['active'])
        self.monitor_type.monitorChange(obj)
        change = {
            'monitor': self.name,
            'channel': self.channel,
            'subchannel': self.subchannel,
            'active': obj['active'],
            'type': self.monitor_type.getType(),  # 'range' or 'fixed'
            'name': self.monitor_type.getMonitorType(),
            'variables': self.monitor_type.getVariableValues(),  # tuple for range, value for fixed
            'values': MONITORS[self.monitor_type.getMonitorType()]['values'],
        }
        #print("Working", change)
        self.monitorSignal.emit(change)

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    monitor = MonitorWidget('compressor', 'compressor')
    monitor.changeValue('On')
    monitor.show()

    sys.exit(app.exec_())
