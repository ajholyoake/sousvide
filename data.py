import datetime
import subprocess
import os
import glob
import time
import datetime
from collections import namedtuple
import logging

FORMAT = '%(asctime)-15s %(name)-10s %(message)s'
logging.basicConfig(filename='{}_{}.log'.format('sousvide', datetime.datetime.now().isoformat()), format=FORMAT)

def get_logger(name):
    logger = logging.getLogger(name)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)
    return logger

Temperature = namedtuple('Temperature',['time','temp'])

class TemperatureProbe(object):
    VALID_LOW = 10.
    VALID_HIGH = 80.

    def __init__(self, serial_number,name=None, pin=20., history = False):
        self.name = name
        self.pin = pin
        self.serial_number = serial_number
        self.file = '/sys/bus/w1/devices/{}/w1_slave'.format(serial_number)
        self.store_history = history
        self.logger = get_logger('TA{}'.format(self.name))
        self.history = []
        
    def read_temp_raw(self):
        try:
            with open(self.file,'r') as f:
                lines = f.readlines()
            return lines
        except IOError:
            return ['Device Disappeared']

    # def read_temp_raw(self):
    #     catdata = subprocess.Popen(['cat',self.file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     out,err = catdata.communicate()
    #     out_decode = out.decode('utf-8')
    #     lines = out_decode.split('\n')
    #     # self.logger.debug('{}, {}'.format(self.serial_number, lines))
    #     return lines

    def extract_temp(self, lines):
        
        now = datetime.datetime.now()
        if lines[0].strip()[-3:] != 'YES':
            self.logger.info('Not good {}, YES'.format(lines))
            return False
        
        equals_pos = lines[1].find('t=')
        if equals_pos == -1:
            self.logger.info('Not good {}, c='.format(lines))
            return False

        equals_pos = lines[1].find('t=')
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        if self.VALID_HIGH > temp_c > self.VALID_LOW:
            self.logger.info('Good {}, {}'.format(self.name, temp_c))
            return Temperature(now, temp_c)

        self.logger.info('Not good - temp?')

    def temperature(self):
        lines = self.read_temp_raw()
        now = datetime.datetime.now()
        
        t = self.extract_temp(lines)

        if t:
            if self.store_history:
                self.history.append(t)
            else:
                self.history = [t]
            return t
        
        else:
            if self.pin:
                if self.history:
                    t = self.history[-1]
                    if now - t.time < datetime.timedelta(seconds=self.pin):
                        return t 
            return None


class TemperatureArray(object):

    DEFAULT_NAME_MAP = {'28-0214635b85ff':'1',
                        '28-0214630a84ff':'2',
                        '28-02146329feff':'3'}

    def __init__(self, name_dir=None, pin=20):
        if name_dir is None:
            name_dir = TemperatureArray.DEFAULT_NAME_MAP
        self.name_dir = name_dir
        self.pin = pin
        self.logger = get_logger(self.__class__.__name__)
        self.sensors = {}
        self.connect_sensors()

    def connect_sensors(self):
        ids = TemperatureArray.connected_sensors()
        for i in ids:
            name = self.name_dir.get(i,i)
            if name not in self.sensors:
                self.logger.info('Found sensor {}, {}'.format(name, i))
                self.sensors[name] = TemperatureProbe(i,name=name, pin=self.pin)

    def get_temperatures(self):
        self.connect_sensors()
        for k,v in self.sensors.iteritems():
            t = v.temperature()
            if t is None:
                continue
            yield {k:t}

    def log(self):
            msgs = ['{}: {}'.format(k, v.temperature().temperature) for k,v in self.sensors.iteritems()]
            print ','.join(msgs)

    @staticmethod
    def connected_sensors():
        dirs = glob.glob('/sys/bus/w1/devices/28-*')
        return [d.split('/')[-1] for d in dirs]

