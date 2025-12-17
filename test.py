# main.py
import serial
import time
from vesc.reader import VESCReader
from vesc.duty import VESCDutyController

def main():
    ser = serial.Serial("/dev/serial0", 115200, timeout=0.1)
    reader = VESCReader(
        ser,
        interval=0.05,
        csv_enable=True,                      # CSV出力(Trueで出力)
        csv_filename="log/0g.csv",      #  保存場所
        csv_fields=["time", "duty", "v_in", "current_motor", "current_in"]
    )
    duty = VESCDutyController(ser, max_duty=10, step_delay=0.05)

    try:
        reader.start()
        duty.start_waveform()
        print("Running... Press Ctrl-C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        duty.stop()
        reader.stop()
        ser.close()

if __name__ == "__main__":
    main()
