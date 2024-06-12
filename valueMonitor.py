"""
# This is where all monitors are stored and values are checked
"""

class AbstractMonitor:

    def checkValue(self, value):
        """
        checks value.
            If value check falls into monitor, return True (this will trigger alert)
            Else: return False (this will not trigger an alert)

        :param value: current value to check
        :return: boolean
        """
        pass

    def __str__(self):
        """
        This will appear in the alert string, in the form of:

        Channel[:subchannel] is {Monitor.__str__()}

        :return: string to attach with alert
        """

class InRangeMonitor: # Single monitor
    def __init__(self, minimum, maximum, inclusive=True):
        self.minimum = minimum
        self.maximum = maximum
        self.inclusive=inclusive


    def checkValue(self, value):
        if self.inclusive:
            if self.minimum and self.maximum:
                return (self.minimum <= value and value <= self.maximum)
            elif self.minimum:
                return self.minimum <= value
            elif self.maximum:
                return value <= self.maximum
        else:
            if self.minimum and self.maximum:
                return (self.minimum < value and value < self.maximum)
            elif self.minimum:
                return self.minimum < value
            elif self.maximum:
                return value < self.maximum
        return False

    def __str__(self):
        operator = "<=" if self.inclusive else "<"
        minimum = self.minimum if self.minimum else "-inf"
        maximum = self.maximum if self.maximum else "inf"

        return f"in range {minimum} {operator} value {operator} {maximum}"

class OutRangeMonitor: # Single monitor
    def __init__(self, minimum, maximum, inclusive=True):
        self.minimum = minimum
        self.maximum = maximum
        self.inclusive=inclusive

    def checkValue(self, value):
        if self.inclusive:
            if self.minimum and self.maximum:
                return not (self.minimum <= value and value <= self.maximum)
            elif self.minimum:
                return not self.minimum <= value
            elif self.maximum:
                return not value <= self.maximum
        else:
            if self.minimum and self.maximum:
                return not (self.minimum < value and value < self.maximum)
            elif self.minimum:
                return not self.minimum < value
            elif self.maximum:
                return not value < self.maximum
        return True

    def __str__(self):
        operator = "<=" if self.inclusive else "<"
        minimum = self.minimum if self.minimum else "-inf"
        maximum = self.maximum if self.maximum else "inf"

        return f"out of range {minimum} {operator} value {operator} {maximum}"


class EqualMonitor:
    def __init__(self, value):
        self.value = value

    def checkValue(self, value):
        return value == self.value

    def __str__(self):
        return f"equal to {self.value}"

class NotEqualMonitor:
    def __init__(self, value):
        self.value = value

    def checkValue(self, value):
        return not (value == self.value)

    def __str__(self):
        return f"not equal to {self.value}"

class NullMonitor:
    def __init__(self, value):
        pass

    def checkValue(self, value):
        return False

    def __str__(self):
        return "Null Monitor"


class OnMonitor:
    def __init__(self):
        pass

    def checkValue(self, value):
        return bool(value) == True

    def __str__(self):
        return f"on"

class OffMonitor:
    def __init__(self):
        pass

    def checkValue(self, value):
        return bool(value) == False

    def __str__(self):
        return f"off"

MONITORS = {
    'InRangeMonitor': {
        'type':InRangeMonitor,
        'variables':{'minimum':float, 'maximum':float},
        'values':{'inclusive':False},
    },
    'InRangeMonitorInclusive': {
        'type':InRangeMonitor,
        'variables':{'minimum':float, 'maximum':float},
        'values':{'inclusive':True},
    },
    'OutRangeMonitor': {
        'type':OutRangeMonitor,
        'variables':{'minimum':float, 'maximum':float},
        'values':{'inclusive':False},
    },
    'OutRangeMonitorInclusive': {
        'type':OutRangeMonitor,
        'variables':{'minimum':float, 'maximum':float},
        'values':{'inclusive':True},
    },
    'EqualNumber': {
        'type':EqualMonitor,
        'variables':{'value':float},
        'values':{},
    },
    'EqualStr': {
        'type':EqualMonitor,
        'variables':{'value':str},
        'values':{},
    },
    'NotEqualNumber': {
        'type':NotEqualMonitor,
        'variables':{'value':float},
        'values':{},
    },
    'NotEqualStr': {
        'type':NotEqualMonitor,
        'variables':{'value':str},
        'values':{},
    },
    'WhenOn':{
        'type':OnMonitor,
        'variables':{},
        'values':{},
    },
    'WhenOff':{
        'type':OffMonitor,
        'variables':{},
        'values':{},
    }
}


class Monitor:
    def __init__(self, channel, subchannel=None, monitorType=NullMonitor, values={}, variables={}):

        self.monitor = monitorType(**values, **variables)
        self.channel = channel
        self.subchannel = subchannel

    def checkMonitor(self, signaledValues):
        if self.channel in signaledValues:
            if type(signaledValues[self.channel]) != dict and self.subchannel is None:
                return self.monitor.checkValue(signaledValues[self.channel])
            else:
                return self.monitor.checkValue(signaledValues[self.channel][self.subchannel])
