# main.py
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
COOLDOWN_SEC = 4

LOG_INTERVAL = 0.05
CSV_FILE = "log/0g.csv"

# GPIO設定
GPIO_DEBOUNCE_TIME = 0.2  # チャタリング防止時間（秒）
GPIO_LOCKOUT_TIME = 15.0  # 1回実行後、次の入力を受け付けない時間（秒）
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
        print("FORWARD START")
        duty.ramp_and_hold(+MAX_DUTY, RUN_TIME_SEC)

    @with_lock
    def reverse():
        print("REVERSE START")
        duty.ramp_and_hold(-MAX_DUTY, RUN_TIME_SEC)

    relay.on_forward = forward
    relay.on_reverse = reverse

    try:
        print("SYSTEM READY")
        print(f"GPIO lockout time: {GPIO_LOCKOUT_TIME}s")
        reader.start()
        relay.wait()
    finally:
        print("SYSTEM STOP")
        reader.stop()
        duty.emergency_stop()
        ser.close()


if __name__ == "__main__":
    main()