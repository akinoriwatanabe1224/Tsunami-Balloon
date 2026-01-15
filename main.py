# main.py - 回転中のみログ取得版
import serial
import time
import threading
from src.duty_forward_revers import VESCDutyController
from src.relay import RelayController
from src.reader import VESCReader

# シリアルポート排他制御用ロック（DutyController/Reader共有）
serial_lock = threading.Lock()

# ===== 設定 =====
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 115200

MAX_DUTY = 30
STEP_DELAY = 0.05
RUN_TIME_SEC = 40

# GPIO設定
GPIO_DEBOUNCE = 0.5
GPIO_COOLDOWN = 15.0

# ログ設定
LOG_INTERVAL = 0.1  # 100msに増加（Dutyコマンドとの競合を減らす）
CSV_FILE = "log/motor.csv"
CSV_FIELDS = ["time", "duty", "rpm", "v_in", "current_in", "current_motor", "temp_fet"]

# ログ取得時間（モーター動作時間 + マージン）
LOG_DURATION = RUN_TIME_SEC+3  # 5秒 + 3秒マージン = 8秒
# =================


def main():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    
    # VESC制御（ランプダウンなし版を使用）
    duty = VESCDutyController(
        ser,
        max_duty=MAX_DUTY,
        step_delay=STEP_DELAY,
        serial_lock=serial_lock
    )

    # ログ取得（一時的使用専用）
    reader = VESCReader(
        ser,
        interval=LOG_INTERVAL,
        csv_filename=CSV_FILE,
        csv_fields=CSV_FIELDS,
        serial_lock=serial_lock
    )
    
    # GPIO制御
    relay = RelayController(
        pin_forward=17,
        pin_reverse=27,
        debounce_time=GPIO_DEBOUNCE,
        cooldown_time=GPIO_COOLDOWN
    )
    
    def forward_action():
        """正転動作（ログ付き）"""
        print("\n" + "="*50)
        print("FORWARD START")
        print("="*50)

        # バッファクリア
        with serial_lock:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        time.sleep(0.2)
        
        # ★ログ取得開始（自動停止タイマー付き）
        reader.start_temporary(LOG_DURATION)
        time.sleep(0.5)  # Reader起動待機
        
        # モーター制御
        duty.ramp_and_hold(+MAX_DUTY, RUN_TIME_SEC)
        
        # Readerが自動停止するまで待機（マージン含む）
        print(f"Waiting for reader to auto-stop...")
        time.sleep(LOG_DURATION - RUN_TIME_SEC + 1)
        
        # 念のため停止確認
        reader.stop()
        
        # 安定化待機
        print("Waiting for VESC stabilization...")
        time.sleep(3.0)

        # 最終バッファクリア
        with serial_lock:
            ser.reset_input_buffer()
            ser.reset_output_buffer()

        print("="*50)
        print("FORWARD COMPLETED")
        print("="*50 + "\n")
    
    def reverse_action():
        """逆転動作（ログ付き）"""
        print("\n" + "="*50)
        print("REVERSE START")
        print("="*50)

        # バッファクリア
        with serial_lock:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        time.sleep(0.2)
        
        # ★ログ取得開始（自動停止タイマー付き）
        reader.start_temporary(LOG_DURATION)
        time.sleep(0.5)  # Reader起動待機
        
        # モーター制御
        duty.ramp_and_hold(-MAX_DUTY, RUN_TIME_SEC)
        
        # Readerが自動停止するまで待機（マージン含む）
        print(f"Waiting for reader to auto-stop...")
        time.sleep(LOG_DURATION - RUN_TIME_SEC + 1)
        
        # 念のため停止確認
        reader.stop()
        
        # 安定化待機
        print("Waiting for VESC stabilization...")
        time.sleep(3.0)

        # 最終バッファクリア
        with serial_lock:
            ser.reset_input_buffer()
            ser.reset_output_buffer()

        print("="*50)
        print("REVERSE COMPLETED")
        print("="*50 + "\n")
    
    # コールバック設定
    relay.on_forward = forward_action
    relay.on_reverse = reverse_action
    
    try:
        print("="*50)
        print("SYSTEM READY")
        print(f"GPIO debounce: {GPIO_DEBOUNCE}s")
        print(f"GPIO cooldown: {GPIO_COOLDOWN}s")
        print(f"Log duration: {LOG_DURATION}s per action")
        print("="*50 + "\n")
        
        relay.wait()
        
    except KeyboardInterrupt:
        print("\n\nKeyboard Interrupt detected")
    finally:
        print("\nSYSTEM STOPPING...")
        reader.stop()
        duty.emergency_stop()
        ser.close()
        print("SYSTEM STOPPED")


if __name__ == "__main__":
    main()
