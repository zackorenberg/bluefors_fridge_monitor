import localvars
import os
import sys
import importlib
import logger
import traceback
logging = logger.Logger(__file__)

def does_config_file_exist(config_file = localvars.CONFIG_FILE):
    return os.path.exists(config_file)


def refresh_all_modules():
    loaded_modules = list(sys.modules.items())
    for k,module in loaded_modules:
        if k[0] == '_' or any([s[0] == '_' for s in k.split('.')]): # iPython fix?
            continue
        try:
            importlib.reload(module)
        except Exception as e:
            logging.debug(f"importlib.reload({k}) error: {str(e)}")
            logging.debug(traceback.format_exc())


class ConfigurationManager:
    def __init__(self, config_file = localvars.CONFIG_FILE):
        self.config_file = config_file

        self.mandatory_fields = localvars.CONFIG_MANDATORY_FIELDS
        self.optional_fields = localvars.CONFIG_OPTIONAL_FIELDS

        self.used_fields = self.mandatory_fields.copy()

        self.values = {} # Values for config file
        self.types = {}

    def read_config_file(self, config_file = None):
        if config_file is None:
            config_file = self.config_file

        assert(does_config_file_exist(config_file))

        with open(config_file, 'r') as f:
            lines = f.readlines()

        # Remove lines with comments
        lines = [l.strip(' \n\t') for l in lines if l[0] != ';']
        # Remove empty lines
        lines = [l for l in lines if l != '']

        for field in self.mandatory_fields: # Go through mandatory fields, if they are not present raise an error
            try:
                value = ([l for l in lines if field in l][0].split(field)[1]).strip('= ')
            except IndexError as e:
                raise ValueError(f"Field {field} not present in config file")
            # Get type from localvars
            try:
                field_type = type(getattr(localvars, field))
                if field_type == list:
                    value = [v.strip(' ') for v in value.split(',')]
                if field_type == bool:
                    value = value.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']
                field_value = field_type(value)
            except Exception as e:
                print("Unknown error happened in configmanager:", e)

            self.values[field] = field_value
            self.types[field] = field_type

        for field in self.optional_fields:
            try:
                value = ([l for l in lines if field in l][0].split(field)[1]).strip('= ')
            except IndexError as e:
                try:
                    field_value = getattr(localvars, field)
                    field_type = type(field_value)
                except Exception as e:
                    print("Unknown error happened in configmanager:", str(e))
            else:
                try:
                    field_type = type(getattr(localvars, field))
                    if field_type == list:
                        value = [v.strip(' ') for v in value.split(',')]
                    if field_type == bool:
                        value = value.lower() in ['true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'certainly', 'uh-huh']
                    field_value = field_type(value)
                    self.used_fields.append(field) # So we know what to save
                except Exception as e:
                    print("Unknown error happened in configmanager:", e)

            self.values[field] = field_value
            self.types[field] = field_type

    def write_config_file(self, config_file = None):
        if config_file is None:
            config_file = self.config_file

        with open(config_file, 'w') as f:
            f.write("; Mandatory Fields\n")
            for field in self.mandatory_fields:
                value = self.values[field]
                if self.types[field] == list:
                    value = ",".join([str(v) for v in self.values[field]])
                f.write(f"{field}={str(value)}\n")
            f.write("; Optional Fields\n")
            for field in self.used_fields:
                if field in self.mandatory_fields: # Already written, continue
                    continue
                value = self.values[field]
                if self.types[field] == list:
                    value = ",".join([str(v) for v in self.values[field]])
                f.write(f"{field}={str(value)}\n")

    def set_config_value(self, **values):
        for k,v in values.items():
            if k not in self.mandatory_fields and k not in self.optional_fields:
                logging.warning(f"There is no configuration field {k}")
                continue
            if not hasattr(localvars, k):
                logging.error(f"localvars has no value {k}")
                continue
            if type(v) != type(getattr(localvars, k)):
                logging.warning(f"Config value {k} has different type {type(v)} than {type(getattr(localvars,k))}")

            # setattr(localvars, k, v) we set this later
            self.values[k] = v
            self.types[k] = type(v)
            if k not in self.used_fields:
                self.used_fields.append(k)

    def write_config_file_with_defaults(self, config_file = 'test.config'):
        if config_file is None:
            config_file = self.config_file

        with open(config_file, 'w') as f:
            f.write("; Mandatory Fields\n")
            for field in self.mandatory_fields:
                value = self.values[field]
                if self.types[field] == list:
                    value = ",".join([str(v) for v in self.values[field]])
                f.write(f"{field}={str(value)}\n")
            f.write("; Optional Fields\n")
            for field in self.optional_fields:
                value = self.values[field]
                if self.types[field] == list:
                    value = ",".join([str(v) for v in self.values[field]])
                f.write(f"{field}={str(value)}\n")

    def update_localvars(self):
        for field, value in self.values.items():
            setattr(localvars, field, value)



if __name__ == "__main__":
    os.chdir(localvars.ROOT_DIR)

    cm = ConfigurationManager()
    cm.read_config_file()
    cm.update_localvars()
    print(localvars.LOG_PATH)
    cm.write_config_file(config_file='test.config')
    cm.write_config_file_with_defaults(config_file='testdefault.config')
