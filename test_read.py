import time
from pyvesc.VESC import VESC

# =============================
# 設定
# =============================
PORT = "/dev/serial0"
BAUDRATE = 115200

# =============================
# VESC初期化
# =============================
vesc = VESC(port=PORT, baudrate=BAUDRATE, timeout=0.1)

# =============================
# メインループ
# =============================
try:
    while True:
        values = vesc.get_values()  # ここで辞書形式で取得
        if values:
            print(f"ERPM: {values['rpm']}, Motor Current[A]: {values['avg_motor_current']}, Input Voltage[V]: {values['input_voltage']}")
        else:
            print("No response from VESC")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program stopped.")
