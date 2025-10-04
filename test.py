import time
import serial
import pyvesc

PORT = "/dev/serial0"
BAUDRATE = 115200
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

def set_duty(duty):
    duty = max(-1.0, min(1.0, duty))
    # SetDutyCycle は float を受け取る
    msg = pyvesc.SetDutyCycle(duty)
    packet = pyvesc.encode(msg)
    ser.write(packet)

try:
    print("Starting motor ramp test...")
    while True:
        for d in [i/20 for i in range(21)]:
            set_duty(d)
            print(f"Duty: {d:.2f}")
            time.sleep(0.2)
        for d in [i/20 for i in range(20, -1, -1)]:
            set_duty(d)
            print(f"Duty: {d:.2f}")
            time.sleep(0.2)

except KeyboardInterrupt:
    set_duty(0)
    ser.close()
