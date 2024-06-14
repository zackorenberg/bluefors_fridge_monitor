from PyQt5 import QtCore, QtWidgets

from localvars import *
from Core.mailer import Mailer
from Core.fileManager import FileManager
from Core.monitorManager import MonitorManager

from GUI.collapsibleBox import CollapsibleBox
from GUI.monitorWidget import MonitorWidget

from GUI.consoleWidget import Printerceptor, ConsoleWidget
import sys
sys.stdout = stdout = Printerceptor()
import logger

logging = logger.Logger(__file__)

import traceback

class BlueforsMonitor(QtWidgets.QWidget):
    monitorSignal = QtCore.pyqtSignal(dict)
    widgetResize = QtCore.pyqtSignal()
    def __init__(self, log_path = LOG_PATH):
        super().__init__()
        self.fileManager = FileManager(log_path)
        self.fileManager.processedChanges.connect(self.processChangesCallback)
        self.monitorManager = MonitorManager(self)
        self.monitorSignal.connect(self.monitorSignalCallback) # When a monitor is toggled
        self.mailer = Mailer(RECIPIENTS)
        self.values = self.fileManager.dumpData()

        self.collapsableBoxes = {}
        self.allMonitors = {}


        """
        self.scroll_widget = QtWidgets.QScrollArea()
        self.scroll_widget.setWidgetResizable(True)
        self.scroll_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #self.scroll_layout = QtWidgets.QLayout()
        #self.scroll_layout.addWidget(self.main_widget)
        #self.setLayout(self.scroll_layout)
        self.setMaximumSize(400, 800)
        self.scroll_widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_layout = QtWidgets.QVBoxLayout()
        self.scroll_layout.addWidget(self.scroll_widget)
        self.setLayout(self.scroll_layout)
        """
    def init_ui(self):

        justify = {ch_type:0 for ch_type in MONITOR_CHANNELS.keys()}

        for ch_type, channels in MONITOR_CHANNELS.items():
            for channel in channels:
                try:
                    t, value = sorted(self.values[channel], key=lambda x: x[0])[-1]
                except Exception as e:
                    logging.error(f"Encountered an error while trying to find last values: {str(e)}")
                    t, value = 0, None
                if type(value) == dict:
                    justify[ch_type] = max(justify[ch_type], max([len(f"{channel}:{ch}") for ch in value.keys()]))
                else:
                    justify[ch_type] = max(justify[ch_type], len(channel))
        #justify += 1

        for ch_type, channels in MONITOR_CHANNELS.items():
            self.collapsableBoxes[ch_type] = CollapsibleBox(ch_type)
            self.collapsableBoxes[ch_type].collapseChangeState.connect(self.collapsibleWidgetCallback)
            self.collapsableBoxes[ch_type].collapseChangeState.connect(self.widgetResize)
            layout = QtWidgets.QVBoxLayout()
            for channel in channels:
                self.allMonitors[channel] = {} # Can be overwritten
                #print(self.values.keys())
                try:
                    t, value = sorted(self.values[channel], key=lambda x:x[0])[-1]
                except Exception as e:
                    logging.error(f"Encountered an error while trying to find last values: {str(e)}")
                    t, value = 0, None
                if type(value) == dict:
                    channels = [f"{channel}:{ch}" for ch in value.keys()]
                    values = list(value.values())
                    for ch, v, subchannel in zip(channels, values, value.keys()):
                        mw = MonitorWidget(
                            name=ch,
                            channel=channel,
                            subchannel=subchannel,
                            parent=self,
                            justify=justify[ch_type]
                        )
                        mw.monitorSignal.connect(self.monitorSignal)
                        mw.changeValue(t, v)
                        layout.addWidget(mw)
                        self.allMonitors[channel][subchannel] = mw
                else:
                    mw = MonitorWidget(
                        name=channel,
                        channel=channel,
                        subchannel=None,
                        parent=self,
                        justify=justify[ch_type]
                    )
                    mw.monitorSignal.connect(self.monitorSignal)
                    mw.changeValue(t, value)
                    layout.addWidget(mw)
                    self.allMonitors[channel] = mw

            self.collapsableBoxes[ch_type].setContentLayout(layout)

        self.main_layout = QtWidgets.QVBoxLayout()
        for cb_name,cb_widget in self.collapsableBoxes.items():
            self.main_layout.addWidget(cb_widget)
        self.main_layout.addStretch()
        self.setLayout(self.main_layout)
        #self.scroll_widget.setMinimumSize(self.main_layout.sizeHint())
        #self.scroll_widget.setLayout(self.main_layout)

    def init_threads(self):
        self.fileManager.start()

    def processChangesCallback(self, obj):
        """
        This occurs when fileManager processes a change
        :param obj: change object
        :return: None
        """
        if all([all([k is None and v is None for k,v in vals.items()]) for keys, vals in obj.items()]):
            logging.warning(f"All None object emitted by fileManager: {str(obj)}")
            return
        try:
            for channel, values_object in obj.items():
                if channel not in self.allMonitors:
                    logging.error(f"Invalid channel found: {channel}")
                    continue
                for time, values in values_object.items():
                    if type(values) == dict:
                        for subchannel, value in values.items():
                            if subchannel not in self.allMonitors[channel]:
                                logging.error(f"Invalid subchannel found: {channel}:{subchannel}")
                                continue
                            try:
                                self.allMonitors[channel][subchannel].changeValue(time, value)
                            except Exception as e:
                                logging.error(f"Could not change value of {channel}:{subchannel} to {value} at {time}: {str(e)}")
                    else:
                        try:
                            self.allMonitors[channel].changeValue(time, values)
                        except Exception as e:
                            logging.error(f"Could not change value of {channel} to {value} at {time}: {str(e)}")

        except Exception as e:
            logging.error(f"While processing changes: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
        try:
            self.checkMonitors(obj)
        except Exception as e:
            logging.error(f"While checking monitors: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")

    def checkMonitors(self, obj):
        vals = self.monitorManager.checkMonitors(obj)
        triggered = (self.monitorManager.WhatMonitorsTriggered(vals))
        triggered_data = self.monitorManager.triggeredMonitorInfo(obj, triggered)
        if len(vals.items()) and len(triggered):
            logging.info(f"Alerts triggered: {', '.join([':'.join(x) if type(x) != str else x for x in triggered])}")
        #if len(vals.items()):
        #    print(vals)
        if len(triggered) > 0:
            print(f"Alerts triggered: {', '.join([':'.join(x) if type(x) != str else x for x in triggered])}")
            #print(triggered_data)
            self.mailer.send_alert(triggered_data, self.fileManager.currentStatus())

        #print(self.fileManager.mostRecentChanges())
        #print(self.fileManager.currentStatus())

    def monitorSignalCallback(self, obj):
        """
        This occurs when one of the monitor checkboxes are toggled
        :param obj: monitor object
        :return: None
        """

        if obj['active']:
            self.monitorManager.addMonitor(channel=obj['channel'], subchannel=obj['subchannel'], type=obj['type'], values=obj['values'], variables=obj['variables'])
            logging.info(f"Monitor {obj['monitor']} activated, (channel={obj['channel']}, subchannel={obj['subchannel']}, type={obj['type']}, values={obj['values']}, variables={obj['variables']})")
            print(f"Monitor {obj['monitor']} activated")
        else:
            self.monitorManager.removeMonitor(channel=obj['channel'], subchannel=obj['subchannel'])
            logging.info(f"Monitor {obj['monitor']} deactivated, (channel={obj['channel']}, subchannel={obj['subchannel']}, type={obj['type']}, values={obj['values']}, variables={obj['variables']})")
            print(f"Monitor {obj['monitor']} deactivated")

    def collapsibleWidgetCallback(self):
        """
        Occurs when collapsibleBox collapses or expands.
        Reset geometry so theres no extra stuff
        """
        self.updateGeometry()
        self.resize(self.main_layout.sizeHint())
        self.adjustSize()
if __name__ == "__main__":
    import sys

    logging.setLevel(logging.DEBUG)
    if DEBUG_MODE: # This is only when using the test log makers
        MONITOR_CHANNELS['Thermometry'] = ['CH1 P', 'CH1 R', 'CH1 T']
        MONITOR_CHANNELS['Valve'] = ['Channels', 'Flowmeter']
    app = QtWidgets.QApplication(sys.argv)
    w = QtWidgets.QMainWindow()
    w.setWindowTitle("Bluefors Fridge Monitor")
    if DEBUG_MODE:
        w.setWindowTitle("Bluefors Fridge Monitor (DEBUG)")
    dock_widget = QtWidgets.QDockWidget('Monitors')
    dock_widget.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                 QtWidgets.QDockWidget.DockWidgetMovable)
    if DEBUG_MODE:
        bm = BlueforsMonitor('tests/test_logs')
    else:
        bm = BlueforsMonitor()

    dock_widget.setWidget(bm)
    dock_widget.setContentsMargins(0,0,0,0)
    ############## Console Widget
    console_dock_widget = QtWidgets.QDockWidget('Console')
    console_dock_widget.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                 QtWidgets.QDockWidget.DockWidgetMovable)


    cw = ConsoleWidget()
    stdout.printToConsole.connect(cw.printToConsole)

    console_dock_widget.setWidget(cw)
    console_dock_widget.setContentsMargins(0,0,0,0)

    if FIX_CONSOLE_HEIGHT:
        size = cw.sizeHint()
        cw.consoleTextEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        cw.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        console_dock_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    ######### Active monitors
    monitors_dock_widget = QtWidgets.QDockWidget('Active Monitors')
    monitors_dock_widget.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                 QtWidgets.QDockWidget.DockWidgetMovable)

    from GUI.activeMonitorsWidget import ActiveMonitorsWidget
    amw = ActiveMonitorsWidget()

    bm.monitorSignal.connect(amw.monitorSignal)
    amw.monitorEdited.connect(bm.monitorSignal)

    monitors_dock_widget.setWidget(amw)
    monitors_dock_widget.setContentsMargins(0,0,0,0)

    bm.widgetResize.connect(dock_widget.adjustSize)

    def resizeEvent(x):
        super(type(dock_widget), dock_widget).resizeEvent(x)
        amw.resize(amw.width(), bm.height())
        bm.adjustSize()
        #w.adjustSize()
    def activeMonitorResizeEvent():
        dock_widget.adjustSize()
        bm.adjustSize()
        monitors_dock_widget.adjustSize()
        amw.adjustSize()
        w.adjustSize()
    dock_widget.resizeEvent = resizeEvent

    amw.widgetResize.connect(activeMonitorResizeEvent)

    w.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dock_widget)
    w.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, monitors_dock_widget)
    w.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, console_dock_widget)
    #dock_widget.show()
    bm.init_ui()
    bm.init_threads()
    #bm.show()
    w.show()
    sys.exit(app.exec_())

