from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from datetime import datetime
import localvars
import time
import logger
logging = logger.Logger(__file__)

from valueMonitor import *

# To format properly
def getMonitorString(mtype, mvalues, mvariables):
    temp = mtype(**mvalues, **mvariables)
    return str(temp)

class MonitorTable(QtCore.QAbstractTableModel):
    def __init__(self, data = [], columns=['channel', 'monitor']):
        super().__init__()
        self.minColumns = len(columns)
        self._data = data
        self._columns = columns
        self._indexes = {}
        self._monitors = {}

    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role: int = ...):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            # return f"Column {section + 1}"
            try:
                return self._columns[section]
            except:
                return 'NaN'
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return f"{section + 1}"

    def data(self, index, role):
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._data[index.row()][index.column()]
        return None

    def rowCount(self, index = QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, index = QtCore.QModelIndex()):
        return max(self.minColumns, len(self._data[0]) if len(self._data) else 0)
        return len(self._data[0]) if len(self._data) else 0

    def addRow(self, row_data):
        idx = self.rowCount(QtCore.QModelIndex())
        self.beginInsertRows(QtCore.QModelIndex(), idx, idx)
        self._data.append(row_data)
        self.endInsertRows()
        return idx

    def removeRow(self, row_index):
        self.beginRemoveRows(QtCore.QModelIndex(), row_index, row_index)
        self._data.pop(row_index)
        self.endRemoveRows()

    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled #| Qt.ItemIsEditable

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            self._data[index.row()][index.column()] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def addMonitor(self, obj):
        row = [obj['monitor'], getMonitorString(obj['type'], obj['values'], obj['variables'])]
        if obj['monitor'] in self._monitors:
            self.removeMonitor(obj)
        idx = self.addRow(row)
        self._indexes[obj['monitor']] = idx
        self._monitors[obj['monitor']] = obj

    def removeMonitor(self, obj):
        if obj['monitor'] in self._monitors.keys():
            self._monitors.pop(obj['monitor'])
            self.removeRow(self._indexes[obj['monitor']])
            self.resetMonitorIndexes()
        else:
            logging.error("Cannot remove monitor {obj['monitor']} because it is not registered as in.")

    def getMonitor(self, index):
        try:
            monitorName = self._data[index.row()][0]
            if monitorName in self._monitors:
                return self._monitors[monitorName]
        except KeyError:
            logging.error(f"Cannot get monitor with index ({index.row()},{index.column()})")

    def resetMonitorIndexes(self):
        wildcards = [r[0] for r in self._data if r[0] not in self._monitors.keys()]
        if len(wildcards) > 0:
            logging.warning(f"Following monitors were not found in rows: {', '.join(wildcards)}")
        self._indexes = {r[0]:d for d,r in enumerate(self._data) if len(r) and r[0] in self._monitors.keys()}


class ActiveMonitorEdit(QtWidgets.QWidget):
    pass


class ActiveMonitorsWidget(QtWidgets.QWidget):
    monitorSignal = QtCore.pyqtSignal(dict)
    monitorEdited = QtCore.pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        self.active_monitors = {}
        self.monitorSignal.connect(self.monitorSignalCallback)

        self.layout = QtWidgets.QVBoxLayout()
        self.table = MonitorTable([])
        self.table_view = QtWidgets.QTableView()
        self.table_view.setModel(self.table)
        self.table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.doubleClicked.connect(self.on_double_click)
        self.resizeTableSections()

        self.edit_btn = QtWidgets.QPushButton('Edit Monitor')
        self.remove_btn = QtWidgets.QPushButton('Remove Monitor')
        self.remove_btn.clicked.connect(self.removeBtnCallback)
        self.layout.addWidget(self.table_view)
        self.layout.addWidget(self.edit_btn)
        self.layout.addWidget(self.remove_btn)
        self.setLayout(self.layout)

        # TODO: Implement this properly
        self.edit_btn.setEnabled(False)
        self.remove_btn.setEnabled(False)

    def resizeTableSections(self):
        if self.table.columnCount(QtCore.QModelIndex()) > 0:
            self.table_view.horizontalHeader().setSectionResizeMode(0,
                                                                    QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            self.table_view.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)

    def monitorSignalCallback(self, obj):
        try:
            if obj['active']:
                self.table.addMonitor(obj)
            else:
                # obj is not active, we now want to remove!
                self.table.removeMonitor(obj)
            self.resizeTableSections()
        except Exception as e:
            print(str(e))
        self.table_view.update()

    def removeBtnCallback(self, event):
        indexes = self.table_view.selectionModel().selectedRows()
        for index in sorted(indexes, reverse=True):
            model = (self.table.data(index, Qt.DisplayRole))
            logging.warning(f"Cannot remove {model} from here, that is currently unsupported.")

    def editBtnCallback(self, event):
        indexes = self.table_view.selectionModel().selectedRows()
        for index in sorted(indexes, reverse=True):
            model = (self.table.data(index, Qt.DisplayRole))
            logging.warning(f"Cannot edit {model} from here, that is currently unsupported.")

    def on_double_click(self, index):
        monitor = self.table.getMonitor(index)
        if monitor:
            logging.debug(f"Double clicked monitor {monitor['monitor']}")

if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    monitor_dicts = [
        {'monitor': 'Channels:one', 'channel': 'Channels', 'subchannel': 'one', 'active': True, 'type':MONITORS['InRangeMonitor']['type'], 'name': 'InRangeMonitor' , 'variables': {'minimum': None, 'maximum': None}, 'values': {'inclusive': False}},
        {'monitor': 'CH1 P', 'channel': 'CH1 P', 'subchannel': None, 'active': True, 'type':MONITORS['InRangeMonitor']['type'], 'name': 'InRangeMonitor', 'variables': {'minimum': None, 'maximum': None}, 'values': {'inclusive': False}},
        {'monitor': 'CH1 P', 'channel': 'CH1 P', 'subchannel': None, 'active': False, 'type':MONITORS['InRangeMonitor']['type'], 'name': 'InRangeMonitor', 'variables': {'minimum': None, 'maximum': None}, 'values': {'inclusive': False}},
    ]
    amw = ActiveMonitorsWidget()
    amw.show()

    class make_thread(QtCore.QThread):
        monitorSignal = QtCore.pyqtSignal(dict)
        def __init__(self):
            super().__init__()

        def run(self):
            monitor_dicts = [
                {'monitor': 'Channels:one', 'channel': 'Channels', 'subchannel': 'one', 'active': True,
                 'type': MONITORS['InRangeMonitor']['type'], 'name': 'InRangeMonitor',
                 'variables': {'minimum': None, 'maximum': None}, 'values': {'inclusive': False}},
                {'monitor': 'CH1 P', 'channel': 'CH1 P', 'subchannel': None, 'active': True,
                 'type': MONITORS['InRangeMonitor']['type'], 'name': 'InRangeMonitor',
                 'variables': {'minimum': None, 'maximum': None}, 'values': {'inclusive': False}},
                {'monitor': 'CH1 P', 'channel': 'CH1 P', 'subchannel': None, 'active': False,
                 'type': MONITORS['InRangeMonitor']['type'], 'name': 'InRangeMonitor',
                 'variables': {'minimum': None, 'maximum': None}, 'values': {'inclusive': False}},
            ]
            import random
            while True:
                try:
                    monitor = random.choice(monitor_dicts)
                    self.monitorSignal.emit(monitor)
                    time.sleep(random.randint(1,3))
                except Exception as e:
                    print(e)


    q_thread = make_thread()
    q_thread.monitorSignal.connect(amw.monitorSignal)
    q_thread.start()
    sys.exit(app.exec_())
