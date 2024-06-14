from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
import time
import logger

logging = logger.Logger(__file__)

from Core.valueMonitors import *
from GUI.monitorWidget import MonitorWidgetSelect
from localvars import *

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


class ActiveMonitorEdit(QtWidgets.QDialog):
    def __init__(self, parent, monitor_obj):
        super().__init__(parent)
        self.monitor = monitor_obj


        self.variables_type = {}
        self.variables_text = {}

        self.setWindowTitle(f"Edit monitor {self.monitor['monitor']}")
        self.layout = QtWidgets.QVBoxLayout(self)

        self.form_layout = QtWidgets.QFormLayout()
        self.active_checkbox = QtWidgets.QCheckBox()
        self.active_checkbox.setCheckState(self.monitor['active'])
        self.monitor_combobox = QtWidgets.QComboBox(self)

        self.monitor_combobox.addItem('Select Monitor Type')
        self.monitor_combobox.setPlaceholderText('Select Monitor Type')
        self.monitor_combobox.addItems(MONITORS.keys())
        self.monitor_combobox.setCurrentText(self.monitor['name'])

        self.form_layout.addRow("Active", self.active_checkbox)
        self.form_layout.addRow("Monitor", self.monitor_combobox)
        # Populate combobox and variables
        self.monitorTypeChanged(self.monitor['name'])  # Make it draw the text boxes
        for varname, value in self.monitor['variables'].items():  # Now add the items
            self.variables_text[varname].setText(str(value))

        self.monitor_combobox.currentTextChanged.connect(self.monitorTypeChanged)

        self.layout.addLayout(self.form_layout)

        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.layout.addWidget(self.buttons)


    def getModifiedData(self):
        monitorName = self.monitor_combobox.currentText()
        ret = self.monitor.copy()
        if monitorName not in MONITORS:
            ret['active'] = False # We want to disable it if invalid
            return ret
        ret['active'] = self.active_checkbox.isChecked()
        ret['name'] = self.monitor_combobox.currentText()
        ret['type'] = MONITORS[monitorName]['type']
        ret['values'] = MONITORS[monitorName]['values']
        ret['variables'] = {}
        for varname, type in MONITORS[monitorName]['variables'].items():
            try:
                ret['variables'][varname] = type(self.variables_text[varname].text())
            except ValueError:
                ret['variables'][varname] = None
        return ret

    def monitorTypeChanged(self, event):
        for _, w in self.variables_text.items():
            self.form_layout.removeRow(w)
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
                # self.main_layout.addWidget(QtWidgets.QLabel(varname), 0, col)
                self.form_layout.addRow(varname, self.variables_text[varname])
                col += 1

class ActiveMonitorsWidget(QtWidgets.QWidget):
    monitorSignal = QtCore.pyqtSignal(dict)
    monitorChange = QtCore.pyqtSignal(dict)
    widgetResize = QtCore.pyqtSignal()
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
        #self.table_view.setSizeAdjustPolicy(QtWidgets.QTableView.SizeAdjustPolicy.AdjustToContents)
        self.resizeTableSections()

        self.edit_btn = QtWidgets.QPushButton('Edit Monitor')
        self.remove_btn = QtWidgets.QPushButton('Remove Monitor')
        self.edit_btn.clicked.connect(self.editBtnCallback)
        self.remove_btn.clicked.connect(self.removeBtnCallback)
        self.layout.addWidget(self.table_view)
        self.layout.addWidget(self.edit_btn)
        self.layout.addWidget(self.remove_btn)
        self.setLayout(self.layout)

        self.edit_btn.setEnabled(True)
        self.remove_btn.setEnabled(True)

        #self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)


    def resizeTableSections(self):
        """
        self.table_view.resizeColumnsToContents()
        ## Try doing more sresizing
        total_width = self.table_view.verticalHeader().width() + 2  # Add 2 for border
        for column in range(self.table.columnCount(QtCore.QModelIndex())):
            total_width += self.table_view.columnWidth(column)
        """
        self.table_view.resizeColumnsToContents()# Set a min width
        total_width = self.table_view.verticalHeader().width() + 20  # Add 2 for border
        if self.table_view.verticalScrollBar().isVisible():
            total_width += self.table_view.verticalScrollBar().width()
        #print(total_width)
        for column in range(self.table.columnCount(QtCore.QModelIndex())):
            total_width += self.table_view.columnWidth(column)
        #print(total_width, self.table_view.width())
        self.table_view.setMinimumWidth(total_width)
        self.table_view.resize(total_width, self.table_view.height())
        self.table_view.adjustSize()

        if self.table.columnCount(QtCore.QModelIndex()) > 0:
            self.table_view.horizontalHeader().setSectionResizeMode(0,
                                                                    QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
            self.table_view.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)



        self.adjustSize()
        self.widgetResize.emit()
        """
        self.table_view.resize(max(self.table_view.width(), total_width), self.table_view.height())
        self.adjustSize()
        """


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
            #model = (self.table.data(index, Qt.DisplayRole))
            #logging.warning(f"Cannot remove {model} from here, that is currently unsupported.")
            #obj = self.table._monitors[model]
            obj = self.table.getMonitor(index)
            obj['active'] = False
            self.monitorChange.emit(obj)


    def editBtnCallback(self, event):
        indexes = self.table_view.selectionModel().selectedRows()
        for index in sorted(indexes, reverse=True):
            #model = (self.table.data(index, Qt.DisplayRole))
            #logging.warning(f"Cannot edit {model} from here, that is currently unsupported.")
            #obj = self.table._monitors[model]
            obj = self.table.getMonitor(index)
            dialog = ActiveMonitorEdit(self, obj)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                modified_obj = dialog.getModifiedData()
                self.monitorChange.emit(modified_obj)


    def on_double_click(self, index):
        monitor = self.table.getMonitor(index)
        if monitor:
            logging.debug(f"Double clicked monitor {monitor['monitor']}")
            obj = self.table.getMonitor(index)
            dialog = ActiveMonitorEdit(self, obj)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                modified_obj = dialog.getModifiedData()
                self.monitorChange.emit(modified_obj)
        else:
            logging.warning(f"Cannot find monitor at double click index {index.row()}, {index.column()}")
        if DEBUG_MODE:
            print(self.exportMonitors())


    def exportMonitors(self):
        monitors = self.table._monitors
        ret = {}
        for name, obj in monitors.items():
            if not obj['active']:
                logging.error("Attempted to export inactive monitor that should not have been in activeMonitorWidget: {name}")
                continue
            ret[name] = {
                k:obj[k] for k in ['monitor', 'channel', 'subchannel', 'name', 'variables']
            }
        return ret

    def importMonitors(self, monitor_infos):
        """
        imports monitors

        :param monitor_infos: barebones like those generated from exportMonitor
        :return:
        """
        monitors = []
        for name, info in monitor_infos.items():
            monitors.append({
                'monitor': info['monitor'],
                'channel': info['channel'],
                'subchannel': info['subchannel'],
                'active': True,
                'type': MONITORS[info['name']]['type'],  # 'range' or 'fixed'
                'name': info['name'],
                'variables': info['variables'],  # tuple for range, value for fixed
                'values': MONITORS[info['name']]['values'],
            })
        for monitor in monitors:
            self.monitorChange.emit(monitor)



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
    monitor_imports = {
        'Channels:one':{'monitor': 'Channels:one', 'channel': 'Channels', 'subchannel': 'one',
         'name': 'InRangeMonitor',
         'variables': {'minimum': 0.1, 'maximum': 2}},
         'CH1 P':{'monitor': 'CH1 P', 'channel': 'CH1 P', 'subchannel': None,
          'name': 'InRangeMonitor',
          'variables': {'minimum': 0.1, 'maximum': 2}},
          'CH1 T':{'monitor': 'CH1 T', 'channel': 'CH1 T', 'subchannel': None,
         'name': 'WhenOn',
         'variables': {}},
    }
    amw.importMonitors(monitor_imports)

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
