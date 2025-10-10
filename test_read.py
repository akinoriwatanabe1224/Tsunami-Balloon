import time
import serial
from pyvesc.interface import VESC
from pyvesc.messages import GetValues

# =============================
# 設定
# =============================
PORT = "/dev/serial0"
BAUDRATE = 115200

# =============================
# シリアルポート初期化
# =============================
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
vesc = VESC(serial_port=ser)  # ここで VESC に Serial オブジェクトを渡す

# =============================
# メインループ
# =============================
try:
    while True:
        values_msg = vesc.get_values()  # VESCから値を取得
        if values_msg is not None:
            print(f"ERPM: {values_msg.rpm}, Motor Current[A]: {values_msg.avg_motor_current}, Input Voltage[V]: {values_msg.input_voltage}")
        else:
            print("No response from VESC")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program stopped.")
    ser.close()
