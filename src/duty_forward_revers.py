# src/duty_forward_revers.py
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
        msg = SetDutyCycle(duty_int)
        self.ser.write(encode(msg))

    def _brake_and_stop(self):
        """
        停止時のガクン防止用
        """
        # トルクを確実に0へ
        self.ser.write(encode(SetCurrent(0)))
        time.sleep(0.2)

        # Duty=0 を複数回送信して安定させる
        for _ in range(5):
            self._send_duty(0)
            time.sleep(0.05)

    def ramp_and_hold(self, target_duty, hold_time):
        """
        target_duty : +max_duty or -max_duty
        hold_time   : 秒
        """
        with self._lock:
            step = 1 if target_duty > 0 else -1
            d = 0

            # 0 → target_duty
            while abs(d) < abs(target_duty):
                d += step
                self._send_duty(d)
                time.sleep(self.step_delay)

            # 保持
            self._send_duty(target_duty)
            time.sleep(hold_time)

            # target_duty → 0（徐々に）
            while abs(d) > 0:
                d -= step
                self._send_duty(d)
                time.sleep(self.step_delay)

            # 完全停止処理
            self._brake_and_stop()

    def emergency_stop(self):
        """
        非常停止用（即時）
        """
        with self._lock:
            self._brake_and_stop()
