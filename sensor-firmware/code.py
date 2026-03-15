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
print("Restoring Always-On Loop...")
print("Initializing I2C Bus...")
i2c_bus = board.STEMMA_I2C()
soil_sensor = Seesaw(i2c_bus, addr=0x36)
print("Soil Sensor detected.")

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
    print(f"Feeds located: {feed_moisture_name}, {feed_temp_name}")
except AdafruitIO_RequestError:
    print("Feeds not found. Generating new feeds on Adafruit IO...")
    moisture_feed = io_client.create_new_feed(feed_moisture_name)
    temp_feed = io_client.create_new_feed(feed_temp_name)

# 5. Calibration Helpers
dry_val = int(os.getenv("DRY_VAL", 300))
wet_val = int(os.getenv("WET_VAL", 1015))

def map_range(x, in_min, in_max, out_min, out_max):
    # Maps a value from one range to another
    return max(min((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min, out_max), out_min)

# 6. Telemetry Loop
while True:
    try:
        # Read raw data from the Seesaw chip
        moisture_val = soil_sensor.moisture_read()
        temperature_c = soil_sensor.get_temp()
        temperature_f = temperature_c * 9 / 5 + 32
        
        # Calculate Percentage
        moisture_percent = int(map_range(moisture_val, dry_val, wet_val, 0, 100))
        
        print(f"Raw: {moisture_val} | Moisture: {moisture_percent}% | Temp: {temperature_f:.2f}F")

        # Transmit payloads to Adafruit IO
        io_client.send_data(moisture_feed["key"], moisture_percent)
        io_client.send_data(temp_feed["key"], f"{temperature_f:.2f}")
        print("Transmission successful.")

    except Exception as e:
        print(f"Hardware or Network Error: {e}")

    # Delay to comply with Adafruit IO free-tier rate limits (30 requests/minute max)
    time.sleep(60) 
