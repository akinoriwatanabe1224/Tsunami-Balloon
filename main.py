# main.py (最終版 - 全対策統合)
import serial
import time
import threading
from src.duty_forward_revers import VESCDutyController
from src.relay import RelayController
from src.reader import VESCReader

# ===== 設定 =====
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 115200

MAX_DUTY = 10
STEP_DELAY = 0.05
RUN_TIME_SEC = 5
COOLDOWN_SEC = 10  # 4秒 → 10秒に延長（より安全に）

LOG_INTERVAL = 0.05
CSV_FILE = "log/0g.csv"

# GPIO設定
GPIO_DEBOUNCE_TIME = 0.3  # 0.2秒 → 0.3秒に延長
GPIO_LOCKOUT_TIME = 20.0  # 15秒 → 20秒に延長（より確実に）
# =================

busy = False
busy_lock = threading.Lock()


def with_lock(func):
    def wrapper():
        global busy
        with busy_lock:
            if busy:
                print("IGNORED (already busy)")
                return
            busy = True

        try:
            func()
        finally:
            def release():
                global busy
                time.sleep(COOLDOWN_SEC)
                with busy_lock:
                    busy = False
                print("READY")

            threading.Thread(target=release, daemon=True).start()

    return wrapper


def main():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    
    # シリアルバッファを初期化時にクリア
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    print("Serial buffers cleared")

    # ログ取得
    reader = VESCReader(
        ser,
        interval=LOG_INTERVAL,
        csv_filename=CSV_FILE
    )

    duty = VESCDutyController(
        ser,
        max_duty=MAX_DUTY,
        step_delay=STEP_DELAY
    )

    # RelayControllerにロックアウト時間を設定
    relay = RelayController(
        pin_forward=17, 
        pin_reverse=27,
        debounce_time=GPIO_DEBOUNCE_TIME,
        lockout_time=GPIO_LOCKOUT_TIME
    )

    @with_lock
    def forward():
        print("=" * 50)
        print("FORWARD START")
        print("=" * 50)
        
        # モーター動作中はreaderを一時停止（通信の競合を防ぐ）
        reader.pause()
        time.sleep(0.2)
        
        # モーター制御実行
        duty.ramp_and_hold(+MAX_DUTY, RUN_TIME_SEC)
        
        # 追加の安全待機時間
        time.sleep(2.0)
        print("Additional safety wait completed")
        
        # readerを再開
        reader.resume()
        
        print("=" * 50)
        print("FORWARD COMPLETED")
        print("=" * 50)

    @with_lock
    def reverse():
        print("=" * 50)
        print("REVERSE START")
        print("=" * 50)
        
        # モーター動作中はreaderを一時停止
        reader.pause()
        time.sleep(0.2)
        
        # モーター制御実行
        duty.ramp_and_hold(-MAX_DUTY, RUN_TIME_SEC)
        
        # 追加の安全待機時間
        time.sleep(2.0)
        print("Additional safety wait completed")
        
        # readerを再開
        reader.resume()
        
        print("=" * 50)
        print("REVERSE COMPLETED")
        print("=" * 50)

    relay.on_forward = forward
    relay.on_reverse = reverse

    try:
        print("=" * 50)
        print("SYSTEM READY")
        print(f"GPIO debounce time: {GPIO_DEBOUNCE_TIME}s")
        print(f"GPIO lockout time: {GPIO_LOCKOUT_TIME}s")
        print(f"Cooldown time: {COOLDOWN_SEC}s")
        print("=" * 50)
        reader.start()
        relay.wait()
    finally:
        print("SYSTEM STOP")
        reader.stop()
        duty.emergency_stop()
        ser.close()


if __name__ == "__main__":
    main()