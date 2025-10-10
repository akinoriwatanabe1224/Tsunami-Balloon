import time
import csv
import os
from datetime import datetime
import serial
from pyvesc.messages.setters import SetDutyCycle
from pyvesc.interface import encode, decode

PORT = "/dev/serial0"
BAUDRATE = 115200
SAVE_DIR = "/home/pi/vesc_logs"
USE_ABSOLUTE_TIME = True

os.makedirs(SAVE_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = os.path.join(SAVE_DIR, f"vesc_data_{timestamp}.csv")

ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

def set_duty(duty: float):
    duty = max(-100.0, min(100.0, duty))
    duty_int = int(duty * 1000)
    ser.write(encode(SetDutyCycle(duty_int)))

def get_values():
    # raw GetValuesコマンド
    ser.write(b'\x02\x04\x00\x00\x03')  # VESCに値要求
    start = time.time()
    while True:
        if ser.in_waiting:
            try:
                msg = decode(ser.read(ser.in_waiting))
                if msg and msg.__class__.__name__ == "Values":
                    return {
                        "rpm": msg.rpm,
                        "avg_motor_current": msg.avg_motor_current,
                        "input_voltage": msg.input_voltage
                    }
            except Exception:
                pass
        if time.time() - start > 0.5:
            return None

with open(csv_filename, mode='w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Time", "Duty", "ERPM", "Current[A]", "Voltage[V]"])

max_duty = 10
start_time = time.time()

try:
    while True:
        for duty_seq in (
            [i/max_duty for i in range(max_duty+1)],
            [i/max_duty for i in range(max_duty,-max_duty-1,-1)],
            [i/max_duty for i in range(-max_duty,1)]
        ):
            for d in duty_seq:
                set_duty(d * max_duty)
                values = get_values()
                t = datetime.now().strftime("%H:%M:%S.%f")[:-3] if USE_ABSOLUTE_TIME else round(time.time()-start_time,2)
                if values:
                    with open(csv_filename, mode='a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([t, d*max_duty, values["rpm"], values["avg_motor_current"], values["input_voltage"]])
                print(d*max_duty, values)
                time.sleep(0.05)

except KeyboardInterrupt:
    set_duty(0)
    ser.close()
    print(f"Program stopped, CSV saved at: {csv_filename}")
