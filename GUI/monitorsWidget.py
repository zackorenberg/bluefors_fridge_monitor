# This has all monitors in it
from PyQt5 import QtCore, QtWidgets

from localvars import *

from GUI.collapsibleBox import CollapsibleBox
from GUI.monitorWidget import MonitorWidget

import sys
import logger
import traceback

logging = logger.Logger(__file__)



class MonitorsWidget(QtWidgets.QWidget):
    monitorSignal = QtCore.pyqtSignal(dict)  # OUTGOING - This is when a new monitor is added or removed from this widget
    monitorChange = QtCore.pyqtSignal(dict)  # INCOMING - This is when a monitor is edited or loaded externally
    widgetResize = QtCore.pyqtSignal()
    processedChanges = QtCore.pyqtSignal(dict) # Signals changes from fileManager in parent
    def __init__(self):
        super().__init__()
        self.collapsableBoxes = {}
        self.allMonitors = {}
        self.processedChanges.connect(self.processChangesCallback)
        self.values = None

    def init_ui(self, values):
        self.values = values
        justify = {ch_type: 0 for ch_type in MONITOR_CHANNELS.keys()}
        for ch_type, channels in MONITOR_CHANNELS.items():
            for channel in channels:
                if channel in CHANNEL_BLACKLIST:
                    continue
                try:
                    t, value = sorted(self.values[channel], key=lambda x: x[0])[-1]
                except Exception as e:
                    logging.error(f"Encountered an error while trying to find last values: {str(e)}")
                    t, value = 0, None
                if type(value) == dict:
                    justify[ch_type] = max(justify[ch_type], max([len(f"{channel}:{ch}") for ch in value.keys()]))
                else:
                    justify[ch_type] = max(justify[ch_type], len(channel))

        for ch_type, channels in MONITOR_CHANNELS.items():
            self.collapsableBoxes[ch_type] = CollapsibleBox(ch_type)
            self.collapsableBoxes[ch_type].collapseChangeState.connect(self.collapsibleWidgetCallback)
            self.collapsableBoxes[ch_type].collapseChangeState.connect(self.widgetResize)
            layout = QtWidgets.QVBoxLayout()
            for channel in channels:
                if channel in CHANNEL_BLACKLIST:
                    continue
                self.allMonitors[channel] = {}  # Can be overwritten
                # print(self.values.keys())
                try:
                    t, value = sorted(self.values[channel], key=lambda x: x[0])[-1]
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
                        self.monitorChange.connect(mw.monitorChange)
                        mw.uiChanged.connect(self.monitorWidgetUIChangedCallback)
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
                    self.monitorChange.connect(mw.monitorChange)
                    mw.uiChanged.connect(self.monitorWidgetUIChangedCallback)
                    mw.changeValue(t, value)
                    layout.addWidget(mw)
                    self.allMonitors[channel] = mw

            self.collapsableBoxes[ch_type].setContentLayout(layout)

        self.main_layout = QtWidgets.QVBoxLayout()
        for cb_name, cb_widget in self.collapsableBoxes.items():
            self.main_layout.addWidget(cb_widget)
        self.main_layout.addStretch()
        self.setLayout(self.main_layout)

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
                        if type(self.allMonitors[channel]) == dict:
                            logging.error(f"Invalid value for channel {channel}: {values}")
                        else:
                            try:
                                self.allMonitors[channel].changeValue(time, values)
                            except Exception as e:
                                logging.error(f"Could not change value of {channel} to {values} at {time}: {str(e)}")

        except Exception as e:
            logging.error(f"While processing changes: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")

    def collapsibleWidgetCallback(self):
        """
        Occurs when collapsibleBox collapses or expands.
        Reset geometry so theres no extra stuff
        """
        self.updateGeometry()
        self.resize(self.main_layout.sizeHint())
        #self.resize(self.main_layout.minimumSize())
        #self.adjustSize()
        self.widgetResize.emit()

    def monitorWidgetUIChangedCallback(self):
        #self.updateGeometry()
        #for ch_type, box in self.collapsableBoxes.items():
        #    box.setMinimumWidth(box.layout().maximumSize().width() + box.content_area.verticalScrollBar().sizeHint().width())
        pass