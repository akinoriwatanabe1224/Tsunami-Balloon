import RPi.GPIO as GPIO
import time

PIN = 17

def callback(channel):
    if GPIO.input(PIN):
        print("CONNECTED")
    else:
        print("DISCONNECTED")

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(PIN, GPIO.BOTH, callback=callback, bouncetime=50)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
