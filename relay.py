import RPi.GPIO as GPIO
import time


class Relay(object):
    ON='on'
    OFF='off'
    
    def __init__(self, pin=None):
        if pin is None:
            pin = 23
        #p4 on breakoutboard
        self.pin = pin
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        self.state = Relay.OFF
# endless loop, on/off for 6 seconds

    def turn_on(self):
        GPIO.output(self.pin,False)
        self.state = Relay.ON

    def turn_off(self):
        GPIO.output(self.pin, True)
        self.state = Relay.OFF
