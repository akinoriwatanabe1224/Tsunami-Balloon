import sys
import time

# PyVESC の親フォルダを追加
sys.path.append('/home/pi/Tsunami-Balloon/PyVESC')

# VESC クラスをインポート
from pyvesc.VESC.VESC import VESC

# =============================
# UART 設定
# =============================
PORT = '/dev/serial0'  # UART ポート
BAUDRATE = 115200       # ボーレート

# VESC オブジェクト作成
vesc = VESC(serial_port=PORT, baudrate=BAUDRATE)

# =============================
# メインループ
# =============================
try:
    while True:
        measurements = vesc.get_measurements()
        print(
            f"ERPM: {measurements.rpm:.1f}, "
            f"Motor Current: {measurements.current_motor:.2f} A, "
            f"Input Voltage: {measurements.v_in:.2f} V"
        )
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program stopped")
