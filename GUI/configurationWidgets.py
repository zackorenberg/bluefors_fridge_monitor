from PyQt5 import QtCore, QtWidgets, QtGui
import os
import sys
import localvars

#### Utility classes
class _DirectoryBrowseWidget(QtWidgets.QWidget):
    def __init__(self, label):
        super().__init__()
        ml = QtWidgets.QHBoxLayout()
        self.le = QtWidgets.QLineEdit()
        self.le.setPlaceholderText(label)
        self.textChanged = self.le.textChanged
        self.btn = QtWidgets.QPushButton('Browse')
        self.btn.clicked.connect(self.browse)
        hb = QtWidgets.QHBoxLayout()
        hb.addWidget(self.le, 1)
        hb.addWidget(self.btn, 0)
        hb.setContentsMargins(0,0,0,0)
        self.setLayout(hb)

    def browse(self):
        options = QtWidgets.QFileDialog.Options()
        dir_name = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Log Directory",
            "",
            options=options
        )
        self.setValue(dir_name)

    def getValue(self):
        return self.le.text()
    def setValue(self, v):
        self.le.setText(str(v))
    def text(self): # This is to make compatible at the end
        return self.getValue()


class _EmailForm(QtWidgets.QWidget):
    textChanged = QtCore.pyqtSignal()
    def __init__(self, label='Recipients'):
        super().__init__()

        class EmailListModel(QtCore.QStringListModel):
            def setData(self, index, value, role=QtCore.Qt.EditRole):
                if role == QtCore.Qt.EditRole:
                    emails = self.stringList()
                    new_email = value.strip()
                    if '@' not in new_email or '.' not in new_email:
                        QtWidgets.QMessageBox.warning(None, 'Invalid Email', 'Please enter a valid email address.')
                        return False
                    if new_email in emails and emails[index.row()] != new_email:
                        QtWidgets.QMessageBox.warning(None, 'Duplicate Email',
                                                      'This email address is already in the list.')
                        return False
                return super().setData(index, value, role)

        self.email_input = QtWidgets.QLineEdit(self)
        self.email_input.setPlaceholderText(f'{label} email address')

        self.add_button = QtWidgets.QPushButton('Add', self)
        self.remove_button = QtWidgets.QPushButton('Remove', self)

        self.list_view = QtWidgets.QListView(self)
        self.model = EmailListModel()  # QtCore.QStringListModel()
        self.list_view.setModel(self.model)
        # Set up layouts
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.email_input)
        input_layout.addWidget(self.add_button)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.remove_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.list_view)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        main_layout.setContentsMargins(0,0,0,0)

        # Connect signals and slots
        self.add_button.clicked.connect(self.add_email)
        self.remove_button.clicked.connect(self.remove_email)
        # Do it in function instead self.email_input.returnPressed.connect(self.add_email)

    def add_email(self, email=None):
        if email is None:
            email = self.email_input.text()
        if email:
            if '@' in email and '.' in email:  # Simple email validation
                emails = self.model.stringList()
                if email not in emails:
                    emails.append(email)
                    self.model.setStringList(emails)
                    self.email_input.clear()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Email', 'This email address is already in the list.')
            else:
                QtWidgets.QMessageBox.warning(self, 'Invalid Email', 'Please enter a valid email address.')
        self.textChanged.emit()
        # else:
        #    QtWidgets.QMessageBox.warning(self, 'No Email', 'Please enter an email address.')

    def keyPressEvent(self, event):
        if (
                event.key() == QtCore.Qt.Key.Key_Delete or event.key() == QtCore.Qt.Key.Key_Backspace) and self.list_view.hasFocus():
            self.remove_email()
        elif (
                event.key() == QtCore.Qt.Key.Key_Return or event.key() == QtCore.Qt.Key.Key_Enter) and self.email_input.hasFocus():
            self.add_email()
        else:
            super().keyPressEvent(event)

    def remove_email(self):
        selected_indexes = self.list_view.selectedIndexes()
        if selected_indexes:
            index = selected_indexes[0]
            emails = self.model.stringList()
            del emails[index.row()]
            self.model.setStringList(emails)
        else:
            QtWidgets.QMessageBox.warning(self, 'No Selection', 'Please select an email address to remove.')
        self.textChanged.emit()

    def remove_emails(self):
        self.model.setStringList([])

    def get_emails(self):
        return self.model.stringList()

    def getValue(self):
        return self.get_emails()

    def setValue(self, values):
        # First remove all
        self.remove_emails()
        for email in values:
            self.add_email(email)

    def text(self):
        emails = self.get_emails()
        return emails if len(emails) > 0 else None

class _BlockedChannels(QtWidgets.QWidget):
    """
        ListView widget, data MUST have type!

        must have getValue and setValue and save and changeConfigFile attributes!
        """

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent=parent, **kwargs)

        self.all_channels = sum([v for k,v in localvars.MONITOR_CHANNELS.items()],[])
        self.options = sorted(self.all_channels)
        self.values = []

        # listview stuff for widgets
        self.listview = QtWidgets.QListView(self)
        self.model = QtGui.QStandardItemModel()
        self.listview.setModel(self.model)


        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.listview)
        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

    def refresh_listview(self):
        self.model.clear()
        for option in self.options:
            item = QtGui.QStandardItem(option)
            item.setData(option)
            item.setCheckable(True)
            item.setEditable(False)
            check = (QtCore.Qt.Checked \
                         if option in self.values \
                         else QtCore.Qt.Unchecked
                     )  # for no partials!
            item.setCheckState(check)
            self.model.appendRow(item)

    def setOptions(self, options):
        if type(options) != list:
            options = list(options)
        self.options = sorted(options)
        self.refresh_listview()

    def setValue(self, value):
        if type(value) != list:
            value = list(value)
        self.values = value
        new_options = [v for v in value if v not in self.options]
        if len(new_options) > 0:
            self.options = sorted(self.options + new_options)

        self.refresh_listview()

    def getValue(self):
        selected_channels = []
        for i in range(self.model.rowCount()):
            item = self.model.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                selected_channels.append(item.data())
        return selected_channels


# Very simple form that has required values only
class NewConfigurationWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.fields = localvars.CONFIG_MANDATORY_FIELDS
        self.labels = {f:" ".join(f.split("_")).title() for f in self.fields}
        self.types = {f:type(getattr(localvars, f)) for f in self.fields}
        self.widgets = {}
        self.main_layout = QtWidgets.QFormLayout()

        for field in self.fields:
            if field in localvars.CONFIG_MANDATORY_FIELDS:
                if field in localvars.CONFIGTYPE_FIELDS_DIRECTORY:
                    self.widgets[field] = _DirectoryBrowseWidget(self.labels[field])
                elif field in localvars.CONFIGTYPE_FIELDS_EMAIL:
                    self.widgets[field] = _EmailForm(self.labels[field])
                else:
                    self.widgets[field] = QtWidgets.QLineEdit()
                    self.widgets[field].setPlaceholderText(self.labels[field])
                self.main_layout.addRow(
                    self.labels[field],
                    self.widgets[field],
                )
        self.setLayout(self.main_layout)

    def getValues(self):
        ret = {}
        errors = []
        for field in self.fields:
            try:
                ret[field] = self.types[field](self.widgets[field].text())
            except ValueError as e:
                errors.append(f"{self.labels[field]} must be of type {str(self.types[field])}: {str(e)}")
        if len(errors) > 0:
            raise ValueError("\n".join(errors))
        return ret

    def checkValidity(self):
        for field in self.fields:
            if self.widgets[field].text() == '' or self.widgets[field].text() is None:
                return False
        return True


class NewConfigurationDialogue(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.newConfigurationWidget = NewConfigurationWidget(self)
        for widget in self.newConfigurationWidget.widgets.values():

            widget.textChanged.connect(self.checkValidity)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.newConfigurationWidget)
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("Save")
        self.button_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("Quit")


        self.main_layout.addWidget(self.button_box)
        self.setLayout(self.main_layout)

    def getValues(self):
        return self.newConfigurationWidget.getValues()

    def checkValidity(self):
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.newConfigurationWidget.checkValidity())

class ConfigurationWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.mandatory_fields = localvars.CONFIG_MANDATORY_FIELDS
        self.optional_fields = localvars.CONFIG_OPTIONAL_FIELDS
        self.fields = self.mandatory_fields + self.optional_fields

        self.labels = {f: " ".join(f.split("_")).title() for f in self.fields}
        self.types = {f: type(getattr(localvars, f)) for f in self.fields}
        self.widgets = {}

        self.main_layout = QtWidgets.QVBoxLayout()
        self.mandatory_layout = QtWidgets.QFormLayout()
        self.optional_layout = QtWidgets.QFormLayout()

        for field in self.mandatory_fields:
            if field in localvars.CONFIGTYPE_FIELDS_DIRECTORY:
                self.widgets[field] = _DirectoryBrowseWidget(self.labels[field])
            elif field in localvars.CONFIGTYPE_FIELDS_EMAIL:
                self.widgets[field] = _EmailForm(self.labels[field])
            else:
                self.widgets[field] = QtWidgets.QLineEdit()
                self.widgets[field].setPlaceholderText(self.labels[field])
            self.mandatory_layout.addRow(
                self.labels[field],
                self.widgets[field],
            )

        for field in self.optional_fields:
            if field in localvars.CONFIGTYPE_FIELDS_DIRECTORY:
                self.widgets[field] = _DirectoryBrowseWidget(self.labels[field])
            elif field in localvars.CONFIGTYPE_FIELDS_EMAIL:
                self.widgets[field] = _EmailForm(self.labels[field])
            elif type(getattr(localvars, field)) == list:
                self.widgets[field] = _BlockedChannels(self)
                self.widgets[field].setValue(getattr(localvars,field))
            elif type(getattr(localvars, field)) == bool:
                self.widgets[field] = QtWidgets.QCheckBox()
                self.widgets[field].setChecked(getattr(localvars, field))
            else:
                self.widgets[field] = QtWidgets.QLineEdit()
                self.widgets[field].setPlaceholderText(self.labels[field])
            self.optional_layout.addRow(
                self.labels[field],
                self.widgets[field],
            )
        #self.setLayout(self.optional_layout)
        mandatory_widget = QtWidgets.QGroupBox("Configuration")
        mandatory_widget.setLayout(self.mandatory_layout)
        optional_widget = QtWidgets.QGroupBox("Settings")
        optional_widget.setLayout(self.optional_layout)
        self.main_layout.addWidget(mandatory_widget)
        self.main_layout.addWidget(optional_widget)
        self.setLayout(self.main_layout)

    def getValues(self):
        ret = {}
        errors = []
        for field in self.fields:
            try:
                if type(self.widgets[field]) == QtWidgets.QCheckBox:
                    ret[field] = self.widgets[field].isChecked()
                elif hasattr(self.widgets[field], 'getValue'):
                    ret[field] = self.types[field](self.widgets[field].getValue())
                else:
                    ret[field] = self.types[field](self.widgets[field].text())
            except ValueError as e:
                errors.append(f"{self.labels[field]} must be of type {str(self.types[field])}: {str(e)}")
        if len(errors) > 0:
            raise ValueError("\n".join(errors))
        return ret

    def setValues(self, values):
        for field, value in values.items():
            if field not in self.widgets:
                print(f"Invalid field {field}")
            if hasattr(self.widgets[field], 'setValue'):
                self.widgets[field].setValue(value)
            elif type(self.widgets[field]) == QtWidgets.QLineEdit:
                self.widgets[field].setText(str(value))
            elif type(self.widgets[field]) == QtWidgets.QCheckBox:
                if type(value) != bool:
                    print(f"Invalid checkbox field {field} {value}")
                self.widgets[field].setChecked(value)
            else:
                print(f"Dont know what to do with {field} {value}")

class ConfigurationDialogue(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.configurationWidget = ConfigurationWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.configurationWidget)
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("Save")

        self.main_layout.addWidget(self.button_box)
        self.setLayout(self.main_layout)

    def setValues(self, values):
        self.configurationWidget.setValues(values)

    def getValues(self):
        return self.configurationWidget.getValues()

    def checkValidity(self):
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.configurationWidget.checkValidity())


class EmailConfigurationWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.fields = localvars.CONFIG_MAILER_FIELDS
        self.labels = {f:" ".join(f.split("_")).title() for f in self.fields}
        self.types = {f:type(getattr(localvars, f)) for f in self.fields}
        self.widgets = {}
        self.main_layout = QtWidgets.QFormLayout()

        for field in self.fields:
            if field in localvars.CONFIGTYPE_FIELDS_DIRECTORY: # None right now but may add feature to save email locally
                self.widgets[field] = _DirectoryBrowseWidget(self.labels[field])
            elif field in localvars.CONFIGTYPE_FIELDS_EMAIL:
                self.widgets[field] = _EmailForm(self.labels[field])
            else:
                self.widgets[field] = QtWidgets.QLineEdit()
                self.widgets[field].setPlaceholderText(self.labels[field])
            self.main_layout.addRow(
                self.labels[field],
                self.widgets[field],
            )
        self.setLayout(self.main_layout)

    def getValues(self):
        ret = {}
        errors = []
        for field in self.fields:
            try:
                ret[field] = self.types[field](self.widgets[field].text())
            except ValueError as e:
                errors.append(f"{self.labels[field]} must be of type {str(self.types[field])}: {str(e)}")
        if len(errors) > 0:
            raise ValueError("\n".join(errors))
        return ret

    def setValues(self, values):
        for field, value in values.items():
            if field not in self.widgets:
                print(f"Invalid field {field}")
            if hasattr(self.widgets[field], 'setValue'):
                self.widgets[field].setValue(value)
            elif type(self.widgets[field]) == QtWidgets.QLineEdit:
                self.widgets[field].setText(str(value))
            elif type(self.widgets[field]) == QtWidgets.QCheckBox:
                if type(value) != bool:
                    print(f"Invalid checkbox field {field} {value}")
                self.widgets[field].setChecked(value)
            else:
                print(f"Dont know what to do with {field} {value}")

    def checkValidity(self):
        for field in self.fields:
            if hasattr(self.widgets[field], 'text'):
                if self.widgets[field].text() == '' or self.widgets[field].text() is None:
                    return False
        return True


class EmailConfigurationDialogue(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.emailConfigurationWidget = EmailConfigurationWidget(self)
        for widget in self.emailConfigurationWidget.widgets.values():

            widget.textChanged.connect(self.checkValidity)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.emailConfigurationWidget)
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setText("Save")
        self.button_box.button(QtWidgets.QDialogButtonBox.Cancel).setText("Cancel")


        self.main_layout.addWidget(self.button_box)
        self.setLayout(self.main_layout)

    def getValues(self):
        return self.emailConfigurationWidget.getValues()

    def checkValidity(self):
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.emailConfigurationWidget.checkValidity())

    def setValues(self, values):
        self.emailConfigurationWidget.setValues(values)



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    #ncw = ConfigurationWidget()
    ncw = ConfigurationDialogue()
    #ncw.show()
    print(ncw.exec())
    app.exec()