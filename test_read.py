import struct

def parse_getvalues(buf):
    # payload のみ抽出 (短パケットなら 2 バイト目が length)
    length = buf[1]
    payload = buf[2:2+length]
    
    # FET 温度, モータ温度, 電流などをアンパック
    # Vedder FW 6.6.x 想定 (例)
    temp_fet, temp_motor, current_motor, current_in, duty, rpm = struct.unpack('>hhiiih', payload[:20])
    
    temp_fet /= 10
    temp_motor /= 10
    current_motor /= 100
    current_in /= 100
    duty /= 1000
    
    return {
        'temp_fet': temp_fet,
        'temp_motor': temp_motor,
        'current_motor': current_motor,
        'current_in': current_in,
        'duty': duty,
        'rpm': rpm
    }
data = ser.read(1024)
if data:
    parsed = parse_getvalues(data)
    print(parsed)