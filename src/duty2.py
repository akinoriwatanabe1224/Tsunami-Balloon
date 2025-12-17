# vesc/duty.py
# 元の test_duty.py をクラス化（duty 計算はそのまま）
import time
import threading
from pyvesc.VESC.messages.setters import SetDutyCycle
from pyvesc.protocol.interface import encode

class VESCDutyController:
        """
        ser: serial.Serial オブジェクト（main で開くことを想定）
        max_duty: 元のコードの max_duty と同じ扱い
        step_delay: 各ステップの sleep 秒
        """
        self.ser = ser
        self.max_duty = max_duty
        self.step_delay = step_delay
        self._stop_flag = threading.Event()
        self._thread = None
        keep_time=3.0
        self.keep_time = keep_time

    def set_duty(self, duty: float):
        # 元のロジックと同じ（clamp と 1000 倍）
        duty = max(-100.0, min(100.0, duty))
        duty_int = int(duty * 1000)  # 0～1000 に変換（元コード）
        msg = SetDutyCycle(duty_int)
        self.ser.write(encode(msg))

    # def _waveform_loop(self):
    #     # 元の test_duty.py のループを再現（構造は変えない）
    #     max_duty = self.max_duty
    #     try:
    #         while not self._stop_flag.is_set():
    #             # Duty上昇 0 -> max
    #             for d in [i / max_duty for i in range(max_duty + 1)]:
    #                 if self._stop_flag.is_set(): break
    #                 self.set_duty(d * max_duty)
    #                 print(d * max_duty)
    #                 time.sleep(self.step_delay)

    #             if self._stop_flag.is_set(): break

    #             # Duty下降 max -> -max
    #             for d in [i / max_duty for i in range(max_duty, -max_duty - 1, -1)]:
    #                 if self._stop_flag.is_set(): break
    #                 self.set_duty(d * max_duty)
    #                 print(d * max_duty)
    #                 time.sleep(self.step_delay)

    #             if self._stop_flag.is_set(): break

    #             # Duty負 -> 0
    #             for d in [i / max_duty for i in range(-max_duty, 1)]:
    #                 if self._stop_flag.is_set(): break
    #                 self.set_duty(d * max_duty)
    #                 print(d * max_duty)
    #                 time.sleep(self.step_delay)
    #     except Exception as e:
    #         print(f"[ERROR in duty loop] {e}")
    #         # エラーが出てもループを抜ける

    def _waveform_loop(self):
        max_duty = self.max_duty
        try:
            while not self._stop_flag.is_set():

                # ① 0 → +max
                for d in range(0, max_duty + 1):
                    if self._stop_flag.is_set(): return
                    self.set_duty(d)
                    print(d)
                    time.sleep(self.step_delay)

                # ★ +max でキープ
                if self.keep_time > 0:
                    print(f"KEEP +{max_duty}")
                    time.sleep(self.keep_time)

                # ② +max → -max
                for d in range(max_duty, -max_duty - 1, -1):
                    if self._stop_flag.is_set(): return
                    self.set_duty(d)
                    print(d)
                    time.sleep(self.step_delay)

                # ★ -max でキープ
                if self.keep_time > 0:
                    print(f"KEEP { -max_duty }")
                    time.sleep(self.keep_time)

                # ③ -max → 0
                for d in range(-max_duty, 1):
                    if self._stop_flag.is_set(): return
                    self.set_duty(d)
                    print(d)
                    time.sleep(self.step_delay)

        except Exception as e:
            print(f"[ERROR in duty loop] {e}")


    def start_waveform(self):
        if self._thread is None:
            self._stop_flag.clear()
            self._thread = threading.Thread(target=self._waveform_loop, daemon=True)
            self._thread.start()

    def stop(self):
        if self._thread is not None:
            self._stop_flag.set()
            self._thread.join(timeout=1.0)
            self._thread = None
            # 停止時に Duty=0 送る（元のコードの挙動に合わせる）
            try:
                self.set_duty(0)
            except Exception:
                pass
