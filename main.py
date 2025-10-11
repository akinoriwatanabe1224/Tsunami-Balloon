# main.py
# vesc/reader.py と vesc/duty.py を組み合わせて実行するエントリ
import serial
import time
import sys
from vesc.reader import VESCReader
from vesc.duty import VESCDutyController

PORT = "/dev/serial0"
BAUDRATE = 115200

def main():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)
        time.sleep(0.1)
        print(f"Opened serial {PORT} @ {BAUDRATE}")
    except Exception as e:
        print(f"シリアルポートを開けませんでした: {e}")
        sys.exit(1)

    reader = VESCReader(ser, interval=0.05)
    duty = VESCDutyController(ser, max_duty=10, step_delay=0.05)

    try:
        # スレッド開始
        reader.start()
        duty.start_waveform()
        print("reader と duty のスレッドを開始しました。CTRL-Cで停止します。")
        # メインスレッドは待機（Ctrl-C で中断）
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\n停止要求を受け取りました。")
    finally:
        # 停止処理
        print("Stopping duty and reader...")
        duty.stop()
        reader.stop()
        try:
            ser.close()
        except Exception:
            pass
        print("終了。")

if __name__ == "__main__":
    main()
