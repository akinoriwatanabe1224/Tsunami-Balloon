import time
import serial
from pyvesc.messages.getters import GetValues
from pyvesc.interface import encode, decode

# =============================
# 設定
# =============================
PORT = "/dev/serial0"  # UART接続
BAUDRATE = 115200
TIMEOUT = 0.1

# =============================
# シリアルポート初期化
# =============================
ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)

# =============================
# VESCの値を取得する関数
# =============================
def read_vesc():
    # VESCにGetValuesコマンド送信
    ser.write(encode(GetValues()))
    
    # 応答が返るまで待機
    start_time = time.time()
    while True:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            msg = decode(data)
            if msg:
                return msg
        if time.time() - start_time > 0.5:  # タイムアウト0.5秒
            return None

# =============================
# メインループ
# =============================
try:
    while True:
        values = read_vesc()
        if values:
            print(f"ERPM: {values.rpm}, Motor Current[A]: {values.avg_motor_current}, Input Voltage[V]: {values.input_voltage}")
        else:
            print("No response from VESC")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Program stopped, serial port closed.")
