from multiprocessing import Process, Queue, Event
from relay import Relay
from data import TemperatureArray, get_logger
import time
import datetime
import logging

def read_temperatures(ta, q, ev, timeout):
    while True:
        for t in ta.get_temperatures():
            if isinstance(t, dict):
                q.put(t)
        while not ev.wait(timeout=timeout):
            break
        if ev.is_set():
            return


class DeliciousFoods(object):
    def __init__(self, target=68, relay_pin = None):
        self.stop_event = Event()
        self.temperature_queue = Queue()
        self.relay = Relay(relay_pin) 
        self.temperature_array = TemperatureArray()
        self.temperature_process = Process(name='temperature',
                target=read_temperatures, args=(self.temperature_array,
                    self.temperature_queue, 
                    self.stop_event,
                    1))
        self.history = []
        self.max_no_reading = 10
        self.target = target
        self.no_reading_count = 0
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info('Starting log for DeliciousFoods')
        self.current_temp = {}
        self.pin = datetime.timedelta(seconds=30)


    def start_temperature_thread(self):
        self.logger.info('Starting temperature thread')
        self.temperature_process.start()

    def stop_temperature_thread(self):
        self.logger.info('Stopping temperature thread')
        self.stop_event.set()
        self.temperature_process.join()

    def current_temperature(self):
        now = datetime.datetime.now()
        while not self.temperature_queue.empty():
            temp = self.temperature_queue.get()
            self.current_temp.update(temp)
            if temp != {}:
                self.no_reading_count = 0
            else:
                self.no_reading_count += 1


        self.current_temp = {k:v for k,v in self.current_temp.iteritems() if now - v.time < self.pin}
        self.logger.info(self.current_temp)
        temp = self.current_temp
        if self.no_reading_count > self.max_no_reading:
            self.logger.info('Too many invalid reading counts')
            return None
            #raise ValueError('Too many non-readings')
        elif not temp:
            self.logger.info('No valid temp sensor readings')
            return None
        else:
                
            #Prune out old ones
            self.history.append(temp)
            self.logger.info({k:v for k,v in temp.iteritems()})
            return temp

    def aggregate_temperature(self):
        curr_temp = self.current_temperature()
        if not curr_temp:
            return

        return max(v.temp for v in curr_temp.itervalues())


    def control_temperature(self):
        temp = self.aggregate_temperature()
        if temp is None:
            self.logger.info('Invalid temp')
            if self.relay.state == Relay.ON:
                self.logger.info('Turning relay off')
            self.relay.turn_off()
            return
        if temp > self.target - 1:
            if self.relay.state == Relay.ON:
                self.logger.info('Turning relay off')
            self.relay.turn_off()
        else:
            if self.relay.state == Relay.OFF:
                self.logger.info('Turning relay on')
            
            self.relay.turn_on()


    def run(self):
        self.start_temperature_thread()
        try:
            while True:
                self.control_temperature()
                time.sleep(10)
        finally:
            self.relay.turn_off()
            self.stop_temperature_thread()
            import pickle
            with open('delicious_food_{}.txt'.format(datetime.datetime.now().isoformat()), 'w') as f:
                pickle.dump(self.history, f)

        

if __name__=='__main__':
    t = DeliciousFoods(target=68)
    t.run()
