import time
import csv
import os
from datetime import datetime
import serial
from pyvesc.messages.setters import SetDutyCycle
from pyvesc.messages import GetValues
from pyvesc.interface import encode, decode

# =============================
# 設定
# =============================
PORT = "/dev/serial0"   # UART接続
BAUDRATE = 115200
SAVE_DIR = "/home/pi/vesc_logs"
USE_ABSOLUTE_TIME = True

os.makedirs(SAVE_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = os.path.join(SAVE_DIR, f"vesc_data_{timestamp}.csv")

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
# VESCから値を取得
# =============================
def get_values():
    ser.write(encode(GetValues()))
    start = time.time()
    while True:
        if ser.in_waiting:
            msg = decode(ser.read(ser.in_waiting))
            if msg is not None and msg.__class__.__name__ == "Values":
                return {
                    "rpm": msg.rpm,
                    "avg_motor_current": msg.avg_motor_current,
                    "input_voltage": msg.input_voltage
                }
        # タイムアウト 0.5秒
        if time.time() - start > 0.5:
            return None

# =============================
# CSV初期化
# =============================
with open(csv_filename, mode='w', newline='') as f:
    writer = csv.writer(f)
    if USE_ABSOLUTE_TIME:
        writer.writerow(["Time", "Duty", "ERPM", "Current[A]", "Voltage[V]"])
    else:
        writer.writerow(["ElapsedTime[s]", "Duty", "ERPM", "Current[A]", "Voltage[V]"])

# =============================
# メインループ
# =============================
max_duty = 10
start_time = time.time()

try:
    while True:
        for duty_seq in (
            [i/max_duty for i in range(max_duty+1)],       # 0 -> max
            [i/max_duty for i in range(max_duty,-max_duty-1,-1)],  # max -> -max
            [i/max_duty for i in range(-max_duty,1)]      # -max -> 0
        ):
            for d in duty_seq:
                set_duty(d * max_duty)
                values = get_values()
                t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time() - start_time, 2)
                if values:
                    with open(csv_filename, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([t, d * max_duty, values["rpm"], values["avg_motor_current"], values["input_voltage"]])
                print(d * max_duty, values)
                time.sleep(0.05)

except KeyboardInterrupt:
    set_duty(0)
    ser.close()
    print(f"Program stopped, CSV saved at: {csv_filename}")
