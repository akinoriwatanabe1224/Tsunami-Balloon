import time
import csv
import os
from datetime import datetime
import serial
from pyvesc.VESC import VESC  # 最新版 PyVESC のインターフェース

# =============================
# 設定
# =============================
PORT = '/dev/serial0'  # 使用するシリアルポートに合わせて変更
BAUDRATE = 115200      # ボーレート
SAVE_DIR = "CSV"
USE_ABSOLUTE_TIME = True  # True: 現在時刻, False: 経過時間[s]

# =============================
# シリアルポート初期化
# =============================
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
vesc = VESC(serial_port=PORT, baudrate=BAUDRATE, timeout=0.1)

os.makedirs(SAVE_DIR, exist_ok=True)

# CSVファイル名に日付を付ける
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = os.path.join(SAVE_DIR, f"vesc_data_{timestamp}.csv")

# =============================
# Duty送信関数
# =============================
def set_duty(duty: float):
    duty = max(-100.0, min(100.0, duty))
    vesc.set_duty_cycle(duty / 100.0)  # 0～1.0 の範囲

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
            [i/max_duty for i in range(max_duty+1)],      # 0→max
            [i/max_duty for i in range(max_duty,-max_duty-1,-1)],  # max→-max
            [i/max_duty for i in range(-max_duty,1)]     # -max→0
        ):
            for d in duty_seq:
                set_duty(d*max_duty)
                values = vesc.get_values()
                if values:
                    with open(csv_filename, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time() - start_time, 2)
                        writer.writerow([t, d*max_duty, values['rpm'], values['avg_motor_current'], values['input_voltage']])
                print(d*max_duty, values)
                time.sleep(0.05)

except KeyboardInterrupt:
    set_duty(0)
    ser.close()
    print(f"Logging stopped.\nCSV saved at: {csv_filename}")
