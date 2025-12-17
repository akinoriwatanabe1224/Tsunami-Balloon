import time
import serial
from pyvesc.messages.setters import SetDutyCycle
from pyvesc.interface import encode

# =============================
# 設定
# =============================
PORT = "/dev/serial0"   # 使用するシリアルポート
BAUDRATE = 115200        # ボーレート

# =============================
# シリアルポート初期化
# =============================
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

# =============================
# Duty送信関数
# =============================
def set_duty(duty: float):
    duty = max(-100.0, min(100.0, duty))
    duty_int = int(duty * 1000)  # 0～1000 に変換
    msg = SetDutyCycle(duty_int)
    ser.write(encode(msg))

# =============================
# メインループ
# =============================
max_duty = 10

try:
    while True:
        # Duty上昇 0 -> max
        for d in [i / max_duty for i in range(max_duty + 1)]:
            set_duty(d * max_duty)
            print(d * max_duty)
            time.sleep(0.05)

        # Duty下降 max -> -max
        for d in [i / max_duty for i in range(max_duty, -max_duty - 1, -1)]:
            set_duty(d * max_duty)
            print(d * max_duty)
            time.sleep(0.05)

        # Duty負 -> 0
        for d in [i / max_duty for i in range(-max_duty, 1)]:
            set_duty(d * max_duty)
            print(d * max_duty)
            time.sleep(0.05)

except KeyboardInterrupt:
    # 停止時にDutyを0にしてシリアルを閉じる
    set_duty(0)
    ser.close()
    print("Program stopped, serial port closed.")
