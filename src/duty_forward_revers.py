# src/duty.py (通信バッファクリア版)
import time
import threading
from pyvesc.messages.setters import SetDutyCycle, SetCurrent, SetRPM
from pyvesc.interface import encode


class VESCDutyController:
    def __init__(self, ser, max_duty=10, step_delay=0.05):
        self.ser = ser
        self.max_duty = max_duty
        self.step_delay = step_delay
        self._lock = threading.Lock()

    def _send_duty(self, duty):
        duty = max(-100.0, min(100.0, duty))
        duty_int = int(duty * 1000)
        self.ser.write(encode(SetDutyCycle(duty_int)))

    def _clear_serial_buffer(self):
        """シリアル通信バッファをクリア"""
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        time.sleep(0.05)

    # ----------------------------
    # 正転・逆転ランプ制御
    # ----------------------------
    def ramp_and_hold(self, target_duty, hold_time):
        with self._lock:
            # 開始前にバッファクリア
            self._clear_serial_buffer()
            
            step = 1 if target_duty > 0 else -1
            d = 0

            # 0 → target
            while abs(d) < abs(target_duty):
                d += step
                self._send_duty(d)
                time.sleep(self.step_delay)

            # 保持
            self._send_duty(target_duty)
            time.sleep(hold_time)

            # target → 0
            while abs(d) > 0:
                d -= step
                self._send_duty(d)
                time.sleep(self.step_delay)

            # 完全停止
            self.hard_stop()

    def hard_stop(self):
        """
        VESCの完全停止（通信バッファクリア版）
        
        改善内容:
        1. 通信バッファをクリア（送信・受信両方）
        2. 複数の制御モードで停止コマンドを送信
        3. RPM制御モードも使用して確実に停止
        4. 長時間のDuty=0維持
        """
        print("[HARD_STOP] Starting complete stop sequence...")
        
        # ステップ1: 通信バッファクリア
        self._clear_serial_buffer()
        
        # ステップ2: 即座にDuty=0を送信
        for i in range(5):
            self._send_duty(0)
            time.sleep(0.01)
        print("[HARD_STOP] Duty=0 sent (5 times)")
        
        # ステップ3: 電流制御モードで停止
        for i in range(5):
            self.ser.write(encode(SetCurrent(0)))
            time.sleep(0.05)
        print("[HARD_STOP] SetCurrent(0) sent (5 times)")
        
        # ステップ4: RPM制御モードでも停止（二重の安全策）
        for i in range(5):
            self.ser.write(encode(SetRPM(0)))
            time.sleep(0.05)
        print("[HARD_STOP] SetRPM(0) sent (5 times)")
        
        # ステップ5: 再度Duty=0を長時間維持
        for i in range(30):
            self._send_duty(0)
            time.sleep(0.05)
        print("[HARD_STOP] Duty=0 maintained for 1.5s")
        
        # ステップ6: 最終確認（電流制御モードに固定）
        for i in range(3):
            self.ser.write(encode(SetCurrent(0)))
            time.sleep(0.1)
        print("[HARD_STOP] Final SetCurrent(0) sent")
        
        # ステップ7: バッファを再度クリア
        self._clear_serial_buffer()
        print("[HARD_STOP] Stop sequence completed")

    # 非常停止用
    def emergency_stop(self):
        with self._lock:
            self.hard_stop()