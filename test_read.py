import time
import serial
from pyvesc.interface import encode, decode
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

# =============================
# VESCから値を取得する関数
# =============================
def get_vesc_values():
    # 値取得コマンド送信
    ser.write(encode(GetValues()))
    time.sleep(0.05)  # VESCが応答するまで少し待つ

    # シリアル受信バッファを読み取り
    if ser.in_waiting:
        data = ser.read(ser.in_waiting)
        msg = decode(data)
        return msg
    return None

# =============================
# メインループ
# =============================
try:
    while True:
        values = get_vesc_values()
        if values is not None:
            print(f"ERPM: {values.rpm}, Motor Current[A]: {values.avg_motor_current}, Input Voltage[V]: {values.input_voltage}")
        else:
            print("No response from VESC")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program stopped.")
    ser.close()
