import RPi.GPIO as GPIO
import time

PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

print("waiting for edge...")

try:
    while True:
        channel = GPIO.wait_for_edge(PIN, GPIO.BOTH)
        if channel is None:
            continue

        if GPIO.input(PIN):
            print("CONNECTED")
        else:
            print("DISCONNECTED")

except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
