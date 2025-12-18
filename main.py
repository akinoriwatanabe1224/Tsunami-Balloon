# main.py (Reader完全起動停止方式)
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
COOLDOWN_SEC = 10

LOG_INTERVAL = 0.05
CSV_FILE = "log/0g.csv"

# GPIO設定
GPIO_DEBOUNCE_TIME = 0.3
GPIO_LOCKOUT_TIME = 20.0

# VESC安定化待機時間
VESC_STABILIZATION_TIME = 8.0
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
        
        # Reader作成・起動（モーター動作前）
        print("Starting reader for pre-motor data collection...")
        reader = VESCReader(ser, interval=LOG_INTERVAL, csv_filename=CSV_FILE)
        reader.start()
        time.sleep(0.5)  # 数サンプル取得
        
        # Reader完全停止
        print("Stopping reader before motor control...")
        reader.stop()
        time.sleep(0.5)
        
        # シリアルバッファをクリア
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("Serial buffers cleared")
        time.sleep(0.2)
        
        # モーター制御実行
        print("Starting motor control sequence...")
        duty.ramp_and_hold(+MAX_DUTY, RUN_TIME_SEC)
        print("Motor control sequence completed")
        
        # VESCの完全安定化を待つ
        print(f"Waiting {VESC_STABILIZATION_TIME}s for VESC to stabilize...")
        time.sleep(VESC_STABILIZATION_TIME)
        
        # シリアルバッファを再度クリア
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("Serial buffers cleared")
        time.sleep(0.5)
        
        # Reader再作成・起動（モーター動作後）
        print("Starting reader for post-motor data collection...")
        reader = VESCReader(ser, interval=LOG_INTERVAL, csv_filename=CSV_FILE)
        reader.start()
        time.sleep(2.0)  # しばらくデータ取得
        
        # Reader停止
        reader.stop()
        print("Reader stopped")
        
        print("=" * 50)
        print("FORWARD COMPLETED")
        print("=" * 50)

    @with_lock
    def reverse():
        print("=" * 50)
        print("REVERSE START")
        print("=" * 50)
        
        # Reader作成・起動（モーター動作前）
        print("Starting reader for pre-motor data collection...")
        reader = VESCReader(ser, interval=LOG_INTERVAL, csv_filename=CSV_FILE)
        reader.start()
        time.sleep(0.5)
        
        # Reader完全停止
        print("Stopping reader before motor control...")
        reader.stop()
        time.sleep(0.5)
        
        # シリアルバッファをクリア
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("Serial buffers cleared")
        time.sleep(0.2)
        
        # モーター制御実行
        print("Starting motor control sequence...")
        duty.ramp_and_hold(-MAX_DUTY, RUN_TIME_SEC)
        print("Motor control sequence completed")
        
        # VESCの完全安定化を待つ
        print(f"Waiting {VESC_STABILIZATION_TIME}s for VESC to stabilize...")
        time.sleep(VESC_STABILIZATION_TIME)
        
        # シリアルバッファを再度クリア
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        print("Serial buffers cleared")
        time.sleep(0.5)
        
        # Reader再作成・起動（モーター動作後）
        print("Starting reader for post-motor data collection...")
        reader = VESCReader(ser, interval=LOG_INTERVAL, csv_filename=CSV_FILE)
        reader.start()
        time.sleep(2.0)
        
        # Reader停止
        reader.stop()
        print("Reader stopped")
        
        print("=" * 50)
        print("REVERSE COMPLETED")
        print("=" * 50)

    relay.on_forward = forward
    relay.on_reverse = reverse

    try:
        print("=" * 50)
        print("SYSTEM READY (Reader on-demand mode)")
        print(f"GPIO debounce time: {GPIO_DEBOUNCE_TIME}s")
        print(f"GPIO lockout time: {GPIO_LOCKOUT_TIME}s")
        print(f"Cooldown time: {COOLDOWN_SEC}s")
        print(f"VESC stabilization time: {VESC_STABILIZATION_TIME}s")
        print("=" * 50)
        relay.wait()
    finally:
        print("SYSTEM STOP")
        duty.emergency_stop()
        ser.close()


if __name__ == "__main__":
    main()