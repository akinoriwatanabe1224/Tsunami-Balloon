import time
import csv
import os
import serial
from datetime import datetime
from pyvesc.messages.setters import SetDutyCycle
from pyvesc.messages.getters import GetValues
from pyvesc.interface import encode, decode

# =============================
# 設定
# =============================
PORT = "/dev/serial0"
BAUDRATE = 115200
SAVE_DIR = "CSV"  # CSV保存先
USE_ABSOLUTE_TIME = True         # True: 時刻, False: 経過時間[s]

# =============================
# 初期化
# =============================
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
os.makedirs(SAVE_DIR, exist_ok=True)

# CSVファイル名に日付を付ける
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = os.path.join(SAVE_DIR, f"vesc_data_{timestamp}.csv")

# =============================
# Duty送信関数（変更なし）
# =============================
def set_duty(duty: float):
    duty = max(-100.0, min(100.0, duty))
    duty_int = int(duty * 1000)
    msg = SetDutyCycle(duty_int)
    ser.write(encode(msg))

# =============================
# VESCから値を取得（安全版）
# =============================
def get_values():
    try:
        ser.write(encode(GetValues()))
        time.sleep(0.02)
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            msg, _ = decode(response)
            # 必要な値のみ取得、存在しない属性は0で補完
            if hasattr(msg, "rpm"):
                return {
                    "erpm": getattr(msg, "rpm", 0),
                    "current_motor": getattr(msg, "avg_motor_current", 0),
                    "v_in": getattr(msg, "input_voltage", 0)
                }
    except Exception as e:
        # temp_mos1 など存在しない属性によるエラーを無視
        pass
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
        # --- Duty上昇 ---
        for d in [i/max_duty for i in range(max_duty+1)]:
            set_duty(d*max_duty)
            values = get_values()
            if values:
                with open(csv_filename, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time() - start_time, 2)
                    writer.writerow([t, d*max_duty, values["erpm"], values["current_motor"], values["v_in"]])
            print(d*max_duty, values)
            time.sleep(0.05)

        # --- Duty下降 ---
        for d in [i/max_duty for i in range(max_duty,-max_duty-1,-1)]:
            set_duty(d*max_duty)
            values = get_values()
            if values:
                with open(csv_filename, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time() - start_time, 2)
                    writer.writerow([t, d*max_duty, values["erpm"], values["current_motor"], values["v_in"]])
            print(d*max_duty, values)
            time.sleep(0.05)

        # --- Duty負→0 ---
        for d in [i/max_duty for i in range(-max_duty, 1)]:
            set_duty(d*max_duty)
            values = get_values()
            if values:
                with open(csv_filename, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time() - start_time, 2)
                    writer.writerow([t, d*max_duty, values["erpm"], values["current_motor"], values["v_in"]])
            print(d*max_duty, values)
            time.sleep(0.05)

except KeyboardInterrupt:
    set_duty(0)
    ser.close()
    print(f"Logging stopped.\nCSV saved at: {csv_filename}")
