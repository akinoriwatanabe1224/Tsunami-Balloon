import time
import csv
import os
from datetime import datetime
import serial
from pyvesc.interface import encode, decode
from pyvesc.messages.setters import SetDutyCycle

# =============================
# 設定
# =============================
PORT = "/dev/serial0"   # UARTポート
BAUDRATE = 115200       # ボーレート
SAVE_DIR = "CSV"
USE_ABSOLUTE_TIME = True  # True: 現在時刻, False: 経過時間[s]

# =============================
# シリアル初期化
# =============================
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
os.makedirs(SAVE_DIR, exist_ok=True)

# CSVファイル名
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = os.path.join(SAVE_DIR, f"vesc_data_{timestamp}.csv")

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
# Duty送信関数
# =============================
def set_duty(duty: float):
    duty = max(-100.0, min(100.0, duty))
    duty_int = int(duty * 1000)  # 0～1000に変換
    ser.write(encode(SetDutyCycle(duty_int)))

# =============================
# VESC値取得関数
# =============================
def get_values(timeout=0.5):
    """VESCからrpm,電流,電圧を取得"""
    # COMM_GET_VALUESコマンドを送信
    ser.write(b'\x02\x04\x00\x00\x03')
    start = time.time()
    buffer = b""
    while True:
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting)
            try:
                msg = decode(buffer)
                if msg and msg.__class__.__name__ == "Values":
                    return {
                        "rpm": msg.rpm,
                        "avg_motor_current": msg.avg_motor_current,
                        "input_voltage": msg.input_voltage
                    }
            except Exception:
                pass  # デコード失敗は無視
        if time.time() - start > timeout:
            return None
        time.sleep(0.01)

# =============================
# メインループ
# =============================
max_duty = 10
start_time = time.time()

try:
    while True:
        # Duty上昇 0 -> max
        for d in [i / max_duty for i in range(max_duty + 1)]:
            set_duty(d * max_duty)
            values = get_values()
            t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time() - start_time, 2)
            with open(csv_filename, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    t,
                    d * max_duty,
                    values["rpm"] if values else None,
                    values["avg_motor_current"] if values else None,
                    values["input_voltage"] if values else None
                ])
            print(d * max_duty, values)
            time.sleep(0.05)

        # Duty下降 max -> -max
        for d in [i / max_duty for i in range(max_duty, -max_duty - 1, -1)]:
            set_duty(d * max_duty)
            values = get_values()
            t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time() - start_time, 2)
            with open(csv_filename, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    t,
                    d * max_duty,
                    values["rpm"] if values else None,
                    values["avg_motor_current"] if values else None,
                    values["input_voltage"] if values else None
                ])
            print(d * max_duty, values)
            time.sleep(0.05)

        # Duty負 -> 0
        for d in [i / max_duty for i in range(-max_duty, 1)]:
            set_duty(d * max_duty)
            values = get_values()
            t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time() - start_time, 2)
            with open(csv_filename, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    t,
                    d * max_duty,
                    values["rpm"] if values else None,
                    values["avg_motor_current"] if values else None,
                    values["input_voltage"] if values else None
                ])
            print(d * max_duty, values)
            time.sleep(0.05)

except KeyboardInterrupt:
    set_duty(0)
    ser.close()
    print(f"Program stopped, CSV saved at: {csv_filename}")
