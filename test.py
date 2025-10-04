#!/usr/bin/env python3
import time
import serial
from pyvesc import VESC, set_duty_cycle, set_rpm

# ====== 設定 ======
SERIAL_PORT = '/dev/serial0'
BAUDRATE = 115200

# ====== VESC 接続 ======
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
vesc = VESC(serial_port=ser)
print(f"VESC connected on {SERIAL_PORT}")

# ====== 制御ループ ======
try:
    while True:
        # VESCからデータ取得
        try:
            values = vesc.get_vesc_values()
        except Exception as e:
            print("Failed to get values:", e)
            values = None

        if values:
            print("=== VESC Status ===")
            print(f"ERPM: {values.rpm}")
            print(f"Input Voltage: {values.v_in} V")
            print(f"Motor Current: {values.motor_current} A")
            if hasattr(values, "temp_fet"):
                print(f"FET Temp: {values.temp_fet} C")
            if hasattr(values, "temp_motor"):
                print(f"Motor Temp: {values.temp_motor} C")
            print("==================\n")

        # ユーザー入力でスロットル指定
        cmd = input("Enter command (d <duty>, r <rpm>, stop, exit): ").strip()
        if cmd == "exit":
            break
        elif cmd.startswith("d "):
            try:
                duty = float(cmd.split()[1])
                set_duty_cycle(vesc, duty / 100)  # 0.0～1.0
            except Exception as e:
                print("Invalid duty:", e)
        elif cmd.startswith("r "):
            try:
                rpm_val = float(cmd.split()[1])
                set_rpm(vesc, rpm_val)
            except Exception as e:
                print("Invalid RPM:", e)
        elif cmd == "stop":
            set_duty_cycle(vesc, 0)
        else:
            print("Unknown command")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("Exiting...")

# 終了時に停止
set_duty_cycle(vesc, 0)
ser.close()
