# test_read.py
import time
from pyvesc.VESC import VESC    # pipで入れたpyvescならこれでOK

PORT = "/dev/serial0"  # あるいは /dev/ttyAMA0, /dev/ttyS0 等
BAUDRATE = 115200

with VESC(serial_port=PORT, baudrate=BAUDRATE) as vesc:
    try:
        while True:
            measurements = vesc.get_measurements()
            print(f"ERPM: {measurements.rpm:.1f}, Motor Current: {measurements.current_motor:.2f} A, Voltage: {measurements.v_in:.2f} V")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopped")
