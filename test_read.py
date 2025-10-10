import serial
import time
from pyvesc.messages.getters import GetValues
from pyvesc.interface import encode, decode

# =============================
# 設定
# =============================
PORT = "/dev/serial0"  # UART接続ポート
BAUDRATE = 115200
TIMEOUT = 0.1  # シリアルタイムアウト[s]

# =============================
# シリアル初期化
# =============================
ser = serial.Serial(PORT, BAUDRATE, timeout=TIMEOUT)

# =============================
# VESCから値を取得する関数
# =============================
def read_vesc_values():
    # GetValuesメッセージを送信
    ser.write(encode(GetValues()))
    
    # 応答を受信
    start_time = time.time()
    while True:
        if ser.in_waiting:
            data = ser.read(ser.in_waiting)
            try:
                msg = decode(data)
                return msg
            except Exception:
                return None
        # タイムアウト1秒
        if time.time() - start_time > 1.0:
            return None

# =============================
# メインループ
# =============================
try:
    while True:
        values = read_vesc_values()
        if values:
            # RPM, モーター電流, 入力電圧などを表示
            print(f"ERPM: {values.rpm:.1f}, Motor Current: {values.avg_motor_current:.2f} A, Voltage: {values.input_voltage:.2f} V")
        else:
            print("No response from VESC")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Program stopped, serial closed")
