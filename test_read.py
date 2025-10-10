import sys
sys.path.append('/home/pi/Tsunami-Balloon/PyVESC')  # PyVESCの親フォルダを追加

from pyvesc.VESC.VESC import VESC  # これで import 可能
import time



PORT = '/dev/serial0'
BAUDRATE = 115200

vesc = VESC(serial_port=PORT, baudrate=BAUDRATE)

try:
    while True:
        measurements = vesc.get_measurements()
        print(f"ERPM: {measurements.rpm:.1f}, Motor Current: {measurements.current_motor:.2f} A, Voltage: {measurements.v_in:.2f} V")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program stopped")
