from PyQt5 import QtCore, QtWidgets, Qt

from localvars import *
from mailer import Mailer
from fileManager import FileManager
from monitorManager import MonitorManager

from GUI.collapsibleBox import CollapsibleBox
from GUI.monitorWidget import MonitorWidget
import logging

import traceback

class BlueforsMonitor(QtWidgets.QWidget):
    monitorSignal = QtCore.pyqtSignal(dict)
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


    def init_ui(self):

        justify = 0

        for ch_type, channels in MONITOR_CHANNELS.items():
            for channel in channels:
                t, value = sorted(self.values[channel], key=lambda x: x[0])[-1]
                if type(value) == dict:
                    justify = max(justify, max([len(f"{channel}:{ch}") for ch in value.keys()]))
                else:
                    justify = max(justify, len(channel))
        #justify += 1

        for ch_type, channels in MONITOR_CHANNELS.items():
            self.collapsableBoxes[ch_type] = CollapsibleBox(ch_type)

            layout = QtWidgets.QVBoxLayout()
            for channel in channels:
                self.allMonitors[channel] = {} # Can be overwritten
                #print(self.values.keys())
                t, value = sorted(self.values[channel], key=lambda x:x[0])[-1]
                if type(value) == dict:
                    channels = [f"{channel}:{ch}" for ch in value.keys()]
                    values = list(value.values())
                    for ch, v, subchannel in zip(channels, values, value.keys()):
                        mw = MonitorWidget(
                            name=ch,
                            channel=channel,
                            subchannel=subchannel,
                            parent=self,
                            justify=justify
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
                        justify=justify
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
                            self.allMonitors[channel][subchannel].changeValue(time, value)
                    else:
                        self.allMonitors[channel].changeValue(time, values)
        except Exception as e:
            logging.error(f"While processing changes: {str(e)}")
            traceback.format_exc()
        try:
            self.checkMonitors(obj)
        except Exception as e:
            logging.error(f"While checking monitors: {str(e)}")
            print(traceback.format_exc())
            #raise e

    def checkMonitors(self, obj):
        vals = self.monitorManager.checkMonitors(obj)

        triggered = (self.monitorManager.WhatMonitorsTriggered(vals))
        #print(vals)
        triggered_data = self.monitorManager.triggeredMonitorInfo(obj, triggered)
        if len(vals.items()) and len(triggered):
            logging.warning(f"Alerts triggered: {', '.join([':'.join(x) if type(x) != str else x for x in triggered])}")
        #if len(vals.items()):
        #    print(vals)
        if len(triggered) > 0:
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
        else:
            self.monitorManager.removeMonitor(channel=obj['channel'], subchannel=obj['subchannel'])
            logging.info(f"Monitor {obj['monitor']} deactivated, (channel={obj['channel']}, subchannel={obj['subchannel']}, type={obj['type']}, values={obj['values']}, variables={obj['variables']})")


if __name__ == "__main__":
    import sys
    import random
    MONITOR_CHANNELS['Thermometry'] = ['CH1 P', 'CH1 R', 'CH1 T']
    MONITOR_CHANNELS['Valve'] = ['Channels', 'Flowmeter']
    app = QtWidgets.QApplication(sys.argv)
    bm = BlueforsMonitor('tests/test_logs')
    bm.init_ui()
    bm.init_threads()
    bm.show()
    sys.exit(app.exec_())

