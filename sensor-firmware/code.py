import os
import time
import board
import busio
import wifi
import adafruit_connection_manager
import adafruit_requests
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
from adafruit_seesaw.seesaw import Seesaw

# 1. Hardware Initialization
print("Initializing Firmware (Dynamic Calibration)...")
i2c_bus = board.STEMMA_I2C()
soil_sensor = Seesaw(i2c_bus, addr=0x36)

# 2. Network Authentication
print(f"Connecting to SSID: {os.getenv('CIRCUITPY_WIFI_SSID')}")
wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
print(f"Connected. IP Address: {wifi.radio.ipv4_address}")

# 3. Adafruit IO Session Setup
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(wifi.radio)
requests = adafruit_requests.Session(pool, ssl_context)
io_client = IO_HTTP(os.getenv("AIO_USERNAME"), os.getenv("AIO_KEY"), requests)

# 4. Feed Allocation
base_feed_name = os.getenv("AIO_FEED_NAME", "plant-1")
feed_moisture_name = f"{base_feed_name}-moisture"
feed_temp_name = f"{base_feed_name}-temperature"

try:
    moisture_feed = io_client.get_feed(feed_moisture_name)
    temp_feed = io_client.get_feed(feed_temp_name)
except AdafruitIO_RequestError:
    moisture_feed = io_client.create_new_feed(feed_moisture_name)
    temp_feed = io_client.create_new_feed(feed_temp_name)

# 5. Calibration Helper
def map_range(x, in_min, in_max, out_min, out_max):
    return max(min((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min, out_max), out_min)

# 6. Telemetry Loop
while True:
    try:
        # Check for calibration updates in settings.toml
        dry_val = os.getenv("DRY_VAL")
        wet_val = os.getenv("WET_VAL")
        
        # Fallback and type correction
        dry = int(dry_val) if dry_val is not None else 300
        wet = int(wet_val) if wet_val is not None else 1015

        # Read raw data from the Seesaw chip
        moisture_val = soil_sensor.moisture_read()
        temperature_c = soil_sensor.get_temp()
        temperature_f = temperature_c * 9 / 5 + 32
        
        # Calculate Percentage using current dry/wet values
        moisture_percent = int(map_range(moisture_val, dry, wet, 0, 100))
        
        print(f"DEBUG: Read DRY_VAL='{dry_val}' -> using {dry}")
        print(f"Telemetry -> Raw: {moisture_val} | Moisture: {moisture_percent}%")

        # Transmit
        io_client.send_data(moisture_feed["key"], moisture_percent)
        io_client.send_data(temp_feed["key"], f"{temperature_f:.2f}")
        print("Sent successfully.")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(60) 
