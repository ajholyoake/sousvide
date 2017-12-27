import datetime
import subprocess
import os
import glob
import time
from collections import namedtuple

Temperature = namedtuple('Temperature',['time','temperature'])

class TemperatureProbe(object):

    def __init__(self, serial_number,name=None, pin=True, history = False):
        self.name = name
        self.pin = pin
        self.serial_number = serial_number
        self.file = '/sys/bus/w1/devices/{}/w1_slave'.format(serial_number)
        self.store_history = history
        self.history = []

    def read_temp_raw(self):
        catdata = subprocess.Popen(['cat',self.file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = catdata.communicate()
        out_decode = out.decode('utf-8')
        lines = out_decode.split('\n')
        return lines

    def temperature(self):
        lines = self.read_temp_raw()
        if lines[0].strip()[-3:] != 'YES':
            if self.pin:
                if self.history:
                    return self.history[-1]
            return None

        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            now = datetime.datetime.now()
            t = Temperature(now, temp_c)
            if self.store_history:
                self.history.append(t)
            return t


class TemperatureArray(object):

    DEFAULT_NAME_MAP = {'28-0214635b85ff':'1',
                        '28-0214630a84ff':'2',
                        '28-02146329feff':'3'}

    def __init__(self, name_dir=None):
        if name_dir is None:
            name_dir = TemperatureArray.DEFAULT_NAME_MAP
        ids = TemperatureArray.connected_sensors()
        self.sensors = {}
        for i in ids:
            name = name_dir.get(i,i)
            self.sensors[name] = TemperatureProbe(i,name=name)

    def get_temperatures(self):
        ret = {}
        for k,v in self.sensors.iteritems():
            if v is  None:
                continue
            t = v.temperature()
            if t is None:
                continue
            ret[k] = t.temperature
        return ret

    def log(self):
            msgs = ['{}: {}'.format(k, v.temperature().temperature) for k,v in self.sensors.iteritems()]
            print ','.join(msgs)

    @staticmethod
    def connected_sensors():
        dirs = glob.glob('/sys/bus/w1/devices/28-*')
        return [d.split('/')[-1] for d in dirs]

if __name__=="__main__":
    ta = TemperatureArray()
    while True:
        ta.log()
