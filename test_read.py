import time
import serial
from pyvesc.interface import encode, decode
from pyvesc.messages import VESCMessage

PORT = "/dev/serial0"
BAUDRATE = 115200

ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

# VESCにGetValuesコマンドを送信してデコード
def get_vesc_values():
    # GetValuesのパケットは「0x04」を送信するだけでOK
    ser.write(b'\x04')  
    time.sleep(0.05)

    if ser.in_waiting:
        data = ser.read(ser.in_waiting)
        try:
            msg = decode(data)
            return msg
        except Exception:
            return None
    return None

try:
    while True:
        values = get_vesc_values()
        if values is not None:
            # 電流・RPM・電圧を表示
            print(f"ERPM: {getattr(values, 'rpm', None)}, Motor Current[A]: {getattr(values, 'avg_motor_current', None)}, Input Voltage[V]: {getattr(values, 'input_voltage', None)}")
        else:
            print("No response from VESC")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program stopped.")
    ser.close()
