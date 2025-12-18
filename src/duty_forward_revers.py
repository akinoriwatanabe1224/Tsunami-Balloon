# src/duty_forward_revers.py - ランプダウン削除版
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
        """Duty指令を送信"""
        duty = max(-100.0, min(100.0, duty))
        duty_int = int(duty * 1000)
        self.ser.write(encode(SetDutyCycle(duty_int)))
    
    def _send_current(self, current):
        """電流指令を送信（単位：A）"""
        current_mA = int(current * 1000)
        self.ser.write(encode(SetCurrent(current_mA)))
    
    def ramp_and_hold(self, target_duty, hold_time):
        """
        ランプアップ → 保持 → 即座に完全停止（ランプダウンなし）
        
        Args:
            target_duty: 目標Duty（+MAX_DUTY または -MAX_DUTY）
            hold_time: 保持時間（秒）
        """
        with self._lock:
            step = 1 if target_duty > 0 else -1
            d = 0
            
            # ===== ランプアップ: 0 → target_duty =====
            print(f"Ramping up to {target_duty}%...")
            while abs(d) < abs(target_duty):
                d += step
                self._send_duty(d)
                time.sleep(self.step_delay)
            
            # ===== 保持 =====
            print(f"Holding at {target_duty}% for {hold_time}s...")
            self._send_duty(target_duty)
            time.sleep(hold_time)
            
            # ===== ランプダウンを削除！即座に停止 =====
            print("Stopping immediately (no ramp down)...")
            self._complete_stop()
            print("Motor stopped")
    
    def _complete_stop(self):
        """
        VESCを完全に停止させる（超強化版）
        
        ランプダウンなしで即座に停止
        """
        # ステップ1: 即座にDuty=0を連続送信
        print("[STOP] Sending Duty=0...")
        for _ in range(30):
            self._send_duty(0)
            time.sleep(0.005)
        
        # ステップ2: バッファクリア
        print("[STOP] Clearing buffers...")
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        time.sleep(0.1)
        
        # ステップ3: 電流制御モード(0A)に強制切替
        print("[STOP] Switching to current mode (0A)...")
        for _ in range(20):
            self._send_current(0)
            time.sleep(0.02)
        
        # ステップ4: バッファ再クリア
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        time.sleep(0.1)
        
        # ステップ5: 再度Duty=0を連続送信
        print("[STOP] Re-sending Duty=0...")
        for _ in range(30):
            self._send_duty(0)
            time.sleep(0.005)
        
        # ステップ6: 電流制御モード(0A)で完全固定
        print("[STOP] Final current mode lock...")
        for _ in range(20):
            self._send_current(0)
            time.sleep(0.02)
        
        # ステップ7: 最終バッファクリア
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        
        # ステップ8: 長時間待機（VESCの完全安定化）
        print("[STOP] Waiting for VESC stabilization...")
        time.sleep(2.0)
        
        # ステップ9: 念のため最後にもう一度
        for _ in range(10):
            self._send_current(0)
            time.sleep(0.02)
        
        print("[STOP] Complete")
    
    def emergency_stop(self):
        """緊急停止"""
        with self._lock:
            print("EMERGENCY STOP")
            self._complete_stop()


if __name__ == "__main__":
    # テスト用
    import serial
    ser = serial.Serial("/dev/serial0", 115200, timeout=0.1)
    duty = VESCDutyController(ser, max_duty=10, step_delay=0.05)
    
    print("Testing forward...")
    duty.ramp_and_hold(+10, 2)
    
    time.sleep(5)
    
    print("Testing reverse...")
    duty.ramp_and_hold(-10, 2)
    
    ser.close()
    print("Test completed")