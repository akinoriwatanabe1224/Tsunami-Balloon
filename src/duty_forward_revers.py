# src/duty_forward_revers.py - デバッグ版（ランプダウンの動きを詳細表示）
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
        ランプアップ → 保持 → ランプダウン → 完全停止（デバッグ版）
        
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
            
            # ===== ランプダウン: target_duty → 0（詳細ログ付き） =====
            print(f"Ramping down to 0%...")
            print(f"[DEBUG] Starting ramp down from d={d}")
            
            loop_count = 0
            while abs(d) > 0:
                d -= step
                loop_count += 1
                print(f"[DEBUG] Loop {loop_count}: d={d}, sending Duty={d}%")
                self._send_duty(d)
                time.sleep(self.step_delay)
            
            print(f"[DEBUG] Ramp down completed. Total loops: {loop_count}, final d={d}")
            
            # 即座にDuty=0を送信
            print("[DEBUG] Sending immediate Duty=0 after ramp down...")
            for i in range(5):
                self._send_duty(0)
                print(f"[DEBUG] Immediate Duty=0 sent ({i+1}/5)")
                time.sleep(0.01)
            
            # ===== 完全停止 =====
            print("Stopping motor...")
            self._complete_stop()
            print("Motor stopped")
    
    def _complete_stop(self):
        """
        VESCを完全に停止させる
        """
        # ステップ1: Duty=0を大量に送信
        print("[STOP] Step 1: Sending Duty=0 (20 times)...")
        for i in range(20):
            self._send_duty(0)
            if i % 5 == 0:
                print(f"[STOP] Duty=0 sent {i}/20")
            time.sleep(0.01)
        
        # ステップ2: 電流制御モード(0A)に切り替え
        print("[STOP] Step 2: Switching to current mode (0A, 10 times)...")
        for i in range(10):
            self._send_current(0)
            if i % 3 == 0:
                print(f"[STOP] SetCurrent(0) sent {i}/10")
            time.sleep(0.05)
        
        # ステップ3: バッファをクリア
        print("[STOP] Step 3: Clearing buffers...")
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        time.sleep(0.1)
        
        # ステップ4: 再度Duty=0を大量送信
        print("[STOP] Step 4: Re-sending Duty=0 (20 times)...")
        for _ in range(20):
            self._send_duty(0)
            time.sleep(0.01)
        
        # ステップ5: 電流制御モード(0A)で完全固定
        print("[STOP] Step 5: Final current mode lock (10 times)...")
        for _ in range(10):
            self._send_current(0)
            time.sleep(0.05)
        
        # ステップ6: 最終バッファクリア
        print("[STOP] Step 6: Final buffer clear...")
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        
        # ステップ7: VESCの内部状態が安定するまで長めに待機
        print("[STOP] Step 7: Waiting 2s for VESC stabilization...")
        time.sleep(2.0)
        
        # ステップ8: 念のため最後にもう一度電流制御(0A)
        print("[STOP] Step 8: Final confirmation (5 times)...")
        for _ in range(5):
            self._send_current(0)
            time.sleep(0.05)
        
        print("[STOP] All steps completed")
    
    def emergency_stop(self):
        """緊急停止"""
        with self._lock:
            print("EMERGENCY STOP")
            self._complete_stop()