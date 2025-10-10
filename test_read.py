# test_duty.py
import time
from pyvesc.VESC import VESC

PORT = "/dev/serial0"
BAUDRATE = 115200

with VESC(serial_port=PORT, baudrate=BAUDRATE) as vesc:
    try:
        duty = 0.1  # 10% duty cycle
        vesc.set_duty_cycle(duty)
        print(f"Set duty cycle: {duty}")

        for _ in range(10):
            measurements = vesc.get_measurements()
            if measurements:
                print(f"ERPM: {measurements.rpm:.1f}, Motor Current: {measurements.current_motor:.2f} A, Voltage: {measurements.v_in:.2f} V")
            else:
                print("No measurements received")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("Stopped")
