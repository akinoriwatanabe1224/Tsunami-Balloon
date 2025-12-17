# relay.py
from gpiozero import DigitalInputDevice
from signal import pause

class RelayController:
    def __init__(self, pin_forward=17, pin_reverse=27):
        self.forward = DigitalInputDevice(pin_forward, pull_up=False)
        self.reverse = DigitalInputDevice(pin_reverse, pull_up=False)

        self.on_forward = None
        self.on_reverse = None

        self.forward.when_activated = self._forward_trigger
        self.reverse.when_activated = self._reverse_trigger

    def _forward_trigger(self):
        print("GPIO17 CONNECTED (FORWARD)")
        if self.on_forward:
            self.on_forward()

    def _reverse_trigger(self):
        print("GPIO27 CONNECTED (REVERSE)")
        if self.on_reverse:
            self.on_reverse()

    def wait(self):
        print("waiting for GPIO events...")
        pause()
