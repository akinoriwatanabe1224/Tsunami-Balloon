from pyvesc.VESC import VESC
import serial
import time

PORT = "/dev/serial0"
BAUDRATE = 115200

# シリアル初期化
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
vesc = VESC(serial_port=PORT, timeout=0.1)

try:
    while True:
        values = vesc.get_values()
        if values:
            print(f"ERPM: {values.rpm:.1f}, Motor Current: {values.avg_motor_current:.2f} A, Voltage: {values.input_voltage:.2f} V")
        else:
            print("No response from VESC")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Program stopped, serial closed")
