import serial
import requests
import json
import time

SERIAL_PORT = 'COM8'# Change to your Arduino's port (e.g., 'COM3' on Windows, '/dev/ttyUSB0' on Linux)
BAUD_RATE = 9600
FLASK_URL = 'http://127.0.0.1:5000/submit-data'

def parse_sensor_line(line):
    # Example: "25.5,60.2,512,150"
    try:
        parts = line.strip().split(',')
        return {
            "temperature": float(parts[0]),
            "humidity": float(parts[1]),
            "light_intensity": int(parts[2]),
            "gas_level": int(parts[3])
        }
    except Exception as e:
        print("Parse error:", e)
        return None

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
print("Listening to Arduino on", SERIAL_PORT)

while True:
    try:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8')
            print("Received:", line.strip())
            data = parse_sensor_line(line)
            if data:
                response = requests.post(FLASK_URL, json=data)
                print("Flask response:", response.json())
        time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped.")
        break
    except Exception as e:
        print("Error:", e)