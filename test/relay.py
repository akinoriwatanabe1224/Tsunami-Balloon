from gpiozero import DigitalInputDevice
from signal import pause

PIN = 17

dev = DigitalInputDevice(PIN, pull_up=False)

def on_active():
    print("CONNECTED")

def on_inactive():
    print("DISCONNECTED")

dev.when_activated = on_active
dev.when_deactivated = on_inactive

print("waiting for edge (gpiozero)...")
pause()
