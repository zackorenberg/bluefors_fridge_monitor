import logger

logging = logger.Logger(__file__)


class MonitorManager():
    def __init__(self, parent):
        self.parent = parent
        self.monitors = {}
        self.values = {} # monitor values saved

    def addMonitor(self, channel, subchannel, type, values, variables):
        if channel in self.monitors and subchannel in self.monitors[channel]:
            self.removeMonitor(channel, subchannel) # Just in case
        if channel not in self.monitors:
            self.monitors[channel] = {}
        if subchannel not in self.monitors[channel]:
            self.monitors[channel][subchannel] = type(**values, **variables)

            # None works as an iterable^
            return
        logging.error("Cannot add monitor channel {channel} subchannel {subchannel} because it already exists")

        """ not safe because sometimes no channel
        if channel not in self.monitors:
            self.monitors[channel] = {}
            if subchannel:
                self.monitors[channel][subchannel] = type(**values, **variables)
            else:
                self.monitors[channel] = type(**values, **variables)
        """
    def removeMonitor(self, channel, subchannel):
        if channel in self.monitors:
            if subchannel is None:  # no subchannel, remove whole thing
                monitor = self.monitors.pop(channel)
                del monitor
                return
            if subchannel in self.monitors[channel]:
                monitor = self.monitors[channel].pop(subchannel)
                del monitor
                return
        logging.warning(f"Cannot remove monitor of channel {channel} subchannel {subchannel} because it does not exist")
        """
        if subchannel:
            if channel in self.monitors:
                if subchannel in self.monitors[channel]:
                    monitor = self.monitors[channel].pop(subchannel)
                    del monitor
        elif channel in self.monitors:
            monitor = self.monitors.pop(channel)
            del monitor
        """

    def checkMonitors(self, signaledValues):
        ret = {}
        for channel, data in signaledValues.items():
            if channel in self.monitors:
                ret[channel] = {}
                for time, v in data.items():
                    if time is None:
                        logging.warning(f"{channel} had a change but did not read correctly")
                        continue
                    if type(v) == dict:
                        for subchannel, value in v.items():
                            if subchannel in self.monitors[channel]:
                                monitorValue = self.monitors[channel][subchannel].checkValue(value)
                                if channel in ret and subchannel in ret[channel]:
                                    ret[channel][subchannel] = ret[channel][subchannel] or monitorValue
                                else:
                                    ret[channel][subchannel] = monitorValue
                    else:
                        if None in self.monitors[channel]:
                            monitorValue = self.monitors[channel][None].checkValue(v)
                            if channel in ret:
                                ret[channel] = ret[channel] or monitorValue
                            else:
                                ret[channel] = monitorValue
                        else:
                            logging.error(f"{channel} with subchannels had an invalid read")
        return ret

        """
        ret = {}
        for channel, data in signaledValues.items():
            if channel in self.monitors:
                ret[channel] = {}
                if type(data) == dict:
                    for subchannel, value in data.items():
                        if subchannel in self.monitors[channel]:
                            ret[channel][subchannel] = self.monitors[channel][subchannel].checkValue(value)
                else:
                    ret[channel] = self.monitors[channel].checkValue(value)
        return ret
        """

    def triggeredMonitorInfo(self, signaledValues, triggeredMonitors):
        ret = {}
        for tup in triggeredMonitors:
            if type(tup) != tuple:
                tup = (tup, None)
            channel, subchannel = tup
            if channel not in signaledValues:
                logging.error(f"Monitor {channel if subchannel is None else channel+':'+subchannel} was triggered but can not find it in signaled values")
                continue
            if channel not in ret:
                ret[channel] = {}
            if subchannel:
                ret[channel][subchannel] = {
                    'currentValue':{t:v[subchannel] for t,v in signaledValues[channel].items() if (t and v and subchannel in v)},
                    'monitor':str(self.monitors[channel][subchannel]), # TODO: make extra safe?
                }
            else:
                ret[channel] = {
                    'currentValue':list(signaledValues[channel].items()), # To differentiate it from one with subchannels
                    'monitor':str(self.monitors[channel][subchannel]),
                }
        return ret



    @staticmethod
    def WhatMonitorsTriggered(monitorCheckRet):
        triggered = []
        for channel, data in monitorCheckRet.items():
            if type(data) == dict:
                for subchannel, value in data.items():
                    if value:
                        triggered.append((channel, subchannel))
            else:
                if data:
                    triggered.append(channel) # No need for none or tuple, only monitorManager class uses None as dictionary key
        return triggered