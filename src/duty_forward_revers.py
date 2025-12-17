# src/duty.py
import time
import threading
from pyvesc.messages.setters import SetDutyCycle, SetCurrent
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

    # ----------------------------
    # 正転・逆転ランプ制御
    # ----------------------------
    def ramp_and_hold(self, target_duty, hold_time):
        with self._lock:
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
        Duty再生成を防ぐ「完全停止」
        
        改善内容:
        1. 即座にDuty=0を複数回送信（緊急停止）
        2. 電流制御モードへの切り替えを複数回実施
        3. Duty=0の維持送信回数を2倍に増加
        4. 最後に電流制御モードを再確認
        """
        # 1. まず即座にDuty=0を送信（緊急停止）
        for _ in range(3):
            self._send_duty(0)
            time.sleep(0.01)
        
        # 2. Duty制御モードから抜けて電流制御モードへ（確実に切り替え）
        for _ in range(3):
            self.ser.write(encode(SetCurrent(0)))
            time.sleep(0.1)
        
        # 3. Duty=0を長時間維持送信（VESCの内部状態を完全にクリア）
        for _ in range(20):
            self._send_duty(0)
            time.sleep(0.05)
        
        # 4. 最後にもう一度電流制御モードに固定（念のため）
        self.ser.write(encode(SetCurrent(0)))
        time.sleep(0.1)

    # 非常停止用
    def emergency_stop(self):
        with self._lock:
            self.hard_stop()