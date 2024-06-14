import logging as loglib
import inspect

import sys

#loglib.basicConfig(format='%(asctime)s - %(filename)s:%(lineno)s - %(module)s.%(funcName)s() - %(levelname)s: %(message)s', datefmt='%Y-%m-%d,%H:%M:%S')

class CallStackFormatter(loglib.Formatter):

    def formatStack(self, _ = None) -> str:
        stack = inspect.stack()[::-1]
        stack_names = (inspect.getmodulename(stack[0].filename),
                       *(f"{frame.function}"
                         for frame
                         in stack[1:-9]))
        return '->'.join(stack_names)

    def format(self, record):
        record.message = record.getMessage()
        record.stack_info = self.formatStack()
        record.stack = record.stack_info
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        return s

class Logger:
    def __init__(self, name):
        self.name = name
        self.logger = loglib.getLogger(name)
        # DO formatting
        self.handler_stderr = loglib.StreamHandler(sys.stderr)
        self.handler_stdout = loglib.StreamHandler(sys.stdout)
        self.handler_stderr.setLevel(loglib.INFO) # TODO: Move this to localvars somehow
        self.handler_stdout.setLevel(loglib.ERROR) # TODO: Move this to localvars somehow


        #formatter = CallStackFormatter('%(asctime)s - %(filename)s:%(lineno)s - %(module)s.%(funcName)s() - %(levelname)s: %(message)s')
        self.formatter_full = CallStackFormatter('%(asctime)s - %(filename)s:%(lineno)s - %(stack)s() - %(levelname)s:\n\t%(message)s', datefmt='%Y-%m-%d,%H:%M:%S')
        self.formatter_abridged = CallStackFormatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d,%H:%M:%S')


        self.handler_stderr.setFormatter(self.formatter_full)
        self.handler_stdout.setFormatter(self.formatter_abridged)

        self.logger.addHandler(self.handler_stderr)
        self.logger.addHandler(self.handler_stdout)

    def __getattr__(self, item):
        try:
            return getattr(self.logger, item)
        except:
            return getattr(loglib, item)
