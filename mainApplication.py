from PyQt5 import QtWidgets

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QAction # This changes in PyQt6 so import individually

import localvars
from Core.configurationManager import ConfigurationManager, does_config_file_exist, refresh_all_modules
from itertools import zip_longest

if not does_config_file_exist():
    # No configuration file!!! Do something
    from GUI.configurationWidgets import NewConfigurationDialogue
    import sys

    app = QtWidgets.QApplication(sys.argv)
    ncd = NewConfigurationDialogue()
    ncd.setWindowTitle("Configuration")
    ncd.setWindowIcon(QtGui.QIcon(localvars.ICON_PATH))
    while True:
        if (ncd_code := ncd.exec()) == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                values = ncd.getValues()
            except ValueError as e:
                QtWidgets.QMessageBox.warning(
                    ncd,
                    "Invalid values",
                    f"The following error(s) occured:\n {str(e)}"
                )
                continue
        elif ncd_code == QtWidgets.QDialog.DialogCode.Rejected:
            sys.exit(0)
        else:
            continue
        break # We got the values
    del app # This was entirely standalone
    config = ConfigurationManager()
    config.set_config_value(**values)
    config.write_config_file()

config = ConfigurationManager()
config.read_config_file()
config.update_localvars()

from Core.fileManager import *
from Core.mailer import Mailer
from Core.fileManager import FileManager
from Core.monitorManager import MonitorManager

from GUI.collapsibleBox import CollapsibleBox
from GUI.monitorWidget import MonitorWidget
from GUI.monitorsWidget import MonitorsWidget
from GUI.activeMonitorsWidget import ActiveMonitorsWidget

from GUI.consoleWidget import Printerceptor, ConsoleWidget
import sys
import json
sys.stdout = stdout = Printerceptor()
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('bluefors.monitor.app.1')
import logger

RESTART_EXIT_CODE = 12 # Should not be used

logging = logger.Logger(__file__)

import traceback


class MainApplication(QtWidgets.QMainWindow):
    monitorSignal = QtCore.pyqtSignal(dict)
    monitorChange = QtCore.pyqtSignal(dict)
    widgetResize = QtCore.pyqtSignal()
    app = None # Where QApplication instance goes
    def __init__(self, log_path=localvars.LOG_PATH):
        super().__init__()
        # Initialize the console widget and connect stdout to console to capture init prints
        self.consoleWidget = ConsoleWidget()
        stdout.printToConsole.connect(self.consoleWidget.printToConsole)
        self.fileManager = FileManager(log_path)
        self.monitorsWidget = MonitorsWidget()
        self.monitorManager = MonitorManager(self)
        self.activeMonitorWidget = ActiveMonitorsWidget()


        self.mailer = Mailer(localvars.RECIPIENTS)
        self.values = self.fileManager.dumpData()


        if localvars.SEND_TEST_EMAIL_ON_LAUNCH:
            self.mailer.send_test(self.fileManager.currentStatus())

        self.monitorsWidget.init_ui(self.values)

        # connect file manager so we can process changes in monitorsWidget and check for alerts
        self.fileManager.processedChanges.connect(self.monitorsWidget.processChangesCallback)
        self.fileManager.processedChanges.connect(self.checkMonitors)
        # TODO: if adding plotting widget, make sure it sends changes there too

        # Connect monitorsWidget to activeMonitorsWidget
        self.monitorsWidget.monitorSignal.connect(self.monitorSignal)
        self.monitorSignal.connect(self.activeMonitorWidget.monitorSignal)
        self.monitorChange.connect(self.monitorsWidget.monitorChange)
        # Connect activeMonitorsWidget to monitorsWidget
        self.activeMonitorWidget.monitorChange.connect(self.monitorsWidget.monitorChange)

        # Connect monitorsWidget to here so we can actually set up monitors
        self.monitorSignal.connect(self.monitorSignalCallback)


        # Add icon
        self.setWindowIcon(QtGui.QIcon(localvars.ICON_PATH))
        self.setWindowTitle("Bluefors Fridge Monitor")
        if localvars.DEBUG_MODE:
            self.setWindowTitle("Bluefors Fridge Monitor (DEBUG)")

        # TODO: Add resizing event captures!
        self.monitorsWidget.widgetResize.connect(self.widgetResize)
        self.activeMonitorWidget.widgetResize.connect(self.widgetResize)
        self.consoleWidget.widgetResize.connect(self.widgetResize)

        self.widgetResize.connect(self.resizeWidgets)

        self.init_menubar()



    def load_monitors(self, fname='history.monitor'):
        if os.path.exists(fname):
            with open(fname, 'r') as f:
                try:
                    monitorHistory = json.load(f)
                    self.activeMonitorWidget.importMonitors(monitorHistory)
                except Exception as e:
                    logging.warning(f"Cannot load monitor history: {str(e)}")

    def export_monitors(self, fname='history.monitor'):
        with open(fname, 'w') as f:
            monitorHistory = self.activeMonitorWidget.exportMonitors()
            if len(monitorHistory.keys()) > 0:
                json.dump(monitorHistory, f)

    def init_ui(self):
        ########### Create docks
        # monitorsWidget
        self.dock_monitorsWidget = QtWidgets.QDockWidget('Monitors')
        self.dock_monitorsWidget.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                 QtWidgets.QDockWidget.DockWidgetMovable)
        self.dock_monitorsWidget.setWidget(self.monitorsWidget)
        self.dock_monitorsWidget.setContentsMargins(0,0,0,0)


        # consoleWidget
        self.dock_consoleWidget = QtWidgets.QDockWidget('Console')
        self.dock_consoleWidget.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                 QtWidgets.QDockWidget.DockWidgetMovable)
        self.dock_consoleWidget.setWidget(self.consoleWidget)
        self.dock_consoleWidget.setContentsMargins(0,0,0,0)

        # activeMonitorsWidget
        self.dock_activeMonitorWidget = QtWidgets.QDockWidget('Active Monitors')
        self.dock_activeMonitorWidget.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable |
                 QtWidgets.QDockWidget.DockWidgetMovable)
        self.dock_activeMonitorWidget.setWidget(self.activeMonitorWidget)
        self.dock_activeMonitorWidget.setContentsMargins(0,0,0,0)


        # Add docks to main window
        if localvars.SPLIT_MONITOR_WIDGETS:
            # Monitor top left, Active monitor top right, Console bottom
            self.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, self.dock_monitorsWidget)
            self.addDockWidget(QtCore.Qt.DockWidgetArea.TopDockWidgetArea, self.dock_activeMonitorWidget)

            self.splitDockWidget(self.dock_monitorsWidget, self.dock_activeMonitorWidget, QtCore.Qt.Orientation.Horizontal)
            self.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_consoleWidget)
        else:
            # Monitor bottom left, Active monitor right, Console bottom left
            self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_monitorsWidget)
            self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dock_activeMonitorWidget)
            self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_consoleWidget)
            self.splitDockWidget(self.dock_monitorsWidget, self.dock_activeMonitorWidget, QtCore.Qt.Orientation.Horizontal)

            self.splitDockWidget(self.dock_monitorsWidget, self.dock_consoleWidget, QtCore.Qt.Orientation.Vertical)

        # deal with sizing:
        if localvars.FIX_CONSOLE_HEIGHT:
            size = self.consoleWidget.sizeHint() # fix it? idr why I had this
            self.consoleWidget.consoleTextEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            self.consoleWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            self.dock_consoleWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        if localvars.FIX_ACTIVE_WIDTH:
            self.activeMonitorWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)



    def init_threads(self):
        self.fileManager.start()

    def close_threads(self):
        self.fileManager.stop()
        self.fileManager.wait()

    def checkMonitors(self, obj):
        try:
            vals = self.monitorManager.checkMonitors(obj)
            triggered = (self.monitorManager.WhatMonitorsTriggered(vals))
            triggered_data = self.monitorManager.triggeredMonitorInfo(obj, triggered)
            if len(vals.items()) and len(triggered):
                logging.info(f"Alerts triggered: {', '.join([':'.join(x) if type(x) != str else x for x in triggered])}")
            # if len(vals.items()):
            #    print(vals)
            if len(triggered) > 0:
                print(f"Alerts triggered: {', '.join([':'.join(x) if type(x) != str else x for x in triggered])}")
                # print(triggered_data)
                self.mailer.send_alert(triggered_data, self.fileManager.currentStatus())
        except Exception as e:
            logging.error(f"An error occured while checking monitors: {str(e)}")
            print(f"{str(e)}:{traceback.format_exc()}")
        # print(self.fileManager.mostRecentChanges())
        # print(self.fileManager.currentStatus())

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


    def resizeWidgets(self):
        #print("resizeWidgets")
        #self.monitorsWidget.adjustSize()
        #self.activeMonitorWidget.adjustSize()
        self.adjustSize()

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)
        #self.monitorsWidget.adjustSize()

    ### Add menubars with actions ###
    def init_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('File')
        edit_menu = menubar.addMenu('Edit')
        tools_menu = menubar.addMenu('Tools')

        load_monitors = QAction(
            "Load monitors",
            self
        )
        load_monitors.setIcon(self.style().standardIcon(
            #QtWidgets.QStyle.StandardPixmap.SP_DialogOpenButton
            QtWidgets.QStyle.StandardPixmap.SP_DirOpenIcon
        ))
        load_monitors.triggered.connect(self.action_loadmonitors)
        save_monitors = QAction(
            "Save monitors",
            self
        )
        save_monitors.setIcon(self.style().standardIcon(
            #QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton
            QtWidgets.QStyle.StandardPixmap.SP_DialogSaveButton
        ))
        save_monitors.triggered.connect(self.action_savemonitors)
        quit_action = QAction(
            "Quit",
            self
        )
        quit_action.triggered.connect(self.action_quit)
        edit_configuration = QAction(
            "Edit configuration",
            self
        )
        edit_configuration.triggered.connect(self.action_editconfig)
        edit_email_settings = QAction(
            "Email Settings",
            self
        )
        edit_email_settings.triggered.connect(self.action_editmailerconfig)
        send_test_email = QAction(
            "Send Test Email",
            self
        )
        restart_app = QAction(
            "Restart Application",
            self
        )
        restart_app.triggered.connect(self.action_restartapplication)
        send_test_email.triggered.connect(self.action_sendtestemail)
        file_menu.addAction(save_monitors)
        file_menu.addAction(load_monitors)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        edit_menu.addAction(edit_configuration)
        edit_menu.addSeparator()
        edit_menu.addAction(edit_email_settings)
        tools_menu.addAction(send_test_email)
        tools_menu.addSeparator()
        tools_menu.addAction(restart_app)

    def action_loadmonitors(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Monitor File",
            "",
            "Monitor Files (*.monitor);;All Files (*)",
            options=options
        )

        try:
            self.load_monitors(fname = file_name)
        except Exception as e:
            logging.error(f"Could not load monitor file {file_name}: {str(e)}")
        else:
            logging.info(f"Monitors loaded from {file_name}")
            print(f"Monitors loaded from {file_name}")

    def action_savemonitors(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Monitor",
            "",
            "Monitor Files (*.monitor);;All Files (*)",
            options=options
        )

        try:
            self.export_monitors(fname=file_name)
        except Exception as e:
            logging.error(f"Could not save monitor file {file_name}: {str(e)}")
        else:
            logging.info(f"Current monitors saved to {file_name}")
            print(f"Current monitors saved to {file_name}")

    def action_editconfig(self):
        from GUI.configurationWidgets import ConfigurationDialogue

        cw = ConfigurationDialogue()
        cw.setValues(
            config.read_localvars()
        )
        cw.setWindowTitle("Edit Configuration")
        cw.setWindowIcon(QtGui.QIcon(localvars.ICON_PATH))
        changes = {}
        while cw.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                values = cw.getValues()
            except ValueError as e:
                QtWidgets.QMessageBox.warning(
                    ncd,
                    "Invalid values",
                    f"The following error(s) occured:\n {str(e)}"
                )
                continue

            # Now get all the values
            try:
                changes = {}
                for k,v in values.items():
                    existing_value = getattr(localvars, k)
                    if type(existing_value) != type(v):
                        print(f"Error: {k} does not have the right type")
                    if type(v) == list:
                        is_same = all([a==b for a,b in zip_longest(sorted(existing_value),sorted(v),fillvalue=float('nan'))])
                    else:
                        is_same = (existing_value == v)
                    if not is_same: # this is a new change
                        changes[k] = v
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    ncd,
                    "Unknown error",
                    f"The following error occured:\n {str(e)}"
                )
                continue
            break
        if len(changes.items()) > 0:
            logging.info(f"Saving the following configuration changes: {', '.join([f'{k}={v}' for k,v in changes.items()])}")
            config.set_config_value(**changes)
            config.update_localvars()
            config.write_config_file()
            QtWidgets.QMessageBox.information(
                self,
                "Configuration Saved",
                "Configuration changes have been saved. Restarting now",
            )
            self.action_restartapplication()

    def action_editmailerconfig(self):
        from GUI.configurationWidgets import EmailConfigurationDialogue

        cw = EmailConfigurationDialogue()
        cw.setValues(
            config.read_localvars_fields(localvars.CONFIG_MAILER_FIELDS)
        )
        cw.setWindowTitle("Email Settings")
        cw.setWindowIcon(QtGui.QIcon(localvars.ICON_PATH))
        changes = {}
        while cw.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            try:
                values = cw.getValues()
            except ValueError as e:
                QtWidgets.QMessageBox.warning(
                    ncd,
                    "Invalid values",
                    f"The following error(s) occured:\n {str(e)}"
                )
                continue

            # Now get all the values
            try:
                changes = {}
                for k,v in values.items():
                    existing_value = getattr(localvars, k)
                    if type(existing_value) != type(v):
                        print(f"Error: {k} does not have the right type")
                    if type(v) == list:
                        is_same = all([a==b for a,b in zip_longest(sorted(existing_value),sorted(v),fillvalue=float('nan'))])
                    else:
                        is_same = (existing_value == v)
                    if not is_same: # this is a new change
                        changes[k] = v
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    ncd,
                    "Unknown error",
                    f"The following error occured:\n {str(e)}"
                )
                continue
            break
        if len(changes.items()) > 0:
            logging.info(f"Saving the following mailer changes: {', '.join([f'{k}={v}' for k,v in changes.items()])}")
            config.set_config_value(**changes)
            config.update_localvars()
            config.write_config_file()
            # Now we update the mailer
            for k,v in changes.items():
                if not hasattr(self.mailer, k.lower()):
                    logging.error(f"Mailer does not have attribute {k.lower()}")
                else:
                    setattr(self.mailer, k.lower(), v)
            send_test_email = QtWidgets.QMessageBox.question(
                self,
                "Email Settings Saved",
                "Email settings have been saved. Would you like to send a test email?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if send_test_email == QtWidgets.QMessageBox.StandardButton.Yes:
                self.action_sendtestemail()

    def action_sendtestemail(self):
        self.mailer.send_test(self.fileManager.currentStatus())
        logging.info(f"Test message sent to {', '.join(self.mailer.recipients)}")
        print("Test email sent!")


    def action_restartapplication(self):
        if self.app:
            self.close()
            self.app.exit(RESTART_EXIT_CODE)
        else:
            self.close()
            QtWidgets.QApplication.exit(RESTART_EXIT_CODE)

    def closeEvent(self, a0: QtGui.QCloseEvent = None) -> None:
        reply = QtWidgets.QMessageBox.question(self, 'Quit',
                                           "Are you sure you want to quit?", QtWidgets.QMessageBox.Yes,
                                           QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            a0.accept()

    def quit(self, exit_code=0):
        if self.app:
            self.close()
            self.app.exit(exit_code)
        else:
            self.close()
            QtWidgets.QApplication.exit(exit_code)

    def action_quit(self):
        reply = QtWidgets.QMessageBox.question(self, 'Quit',
                                               "Are you sure you want to quit?", QtWidgets.QMessageBox.Yes,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.closeEvent = super().closeEvent
            self.quit()




if __name__ == "__main__":
    exitcode = RESTART_EXIT_CODE
    app = QtWidgets.QApplication(sys.argv)
    MainApplication.app = app
    while exitcode == RESTART_EXIT_CODE:
        w = MainApplication(log_path=localvars.LOG_PATH)
        #w.app = app
        w.init_ui()
        w.init_threads()
        w.load_monitors(fname='history.monitor')
        w.show()
        exitcode = w.app.exec()
        w.export_monitors(fname='history.monitor')
        w.close_threads()
        if exitcode == RESTART_EXIT_CODE:
            refresh_all_modules()
            config.read_config_file()
            config.update_localvars()
    sys.exit(exitcode)