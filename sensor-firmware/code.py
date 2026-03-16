import os
import time
import board
import busio
import wifi
import adafruit_connection_manager
import adafruit_requests
import analogio
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
from adafruit_seesaw.seesaw import Seesaw

# 1. Hardware Initialization
print("Restoring Always-On Loop (Telemetery Expansion)...")
print("Initializing Hardware...")
i2c_bus = board.STEMMA_I2C()
soil_sensor = Seesaw(i2c_bus, addr=0x36)

# Battery monitor on pin A2 (halved via voltage divider on BFF)
vbat_pin = analogio.AnalogIn(board.A2)

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
def get_or_create_feed(client, name):
    try:
        return client.get_feed(name)
    except AdafruitIO_RequestError:
        print(f"Creating feed: {name}")
        return client.create_new_feed(name)

base_feed_name = os.getenv("AIO_FEED_NAME", "plant-1")
moisture_feed = get_or_create_feed(io_client, f"{base_feed_name}-moisture")
temp_feed = get_or_create_feed(io_client, f"{base_feed_name}-temperature")
battery_feed = get_or_create_feed(io_client, f"{base_feed_name}-battery")
print("All feeds verified.")

# 5. Calibration Helper
def map_range(x, in_min, in_max, out_min, out_max):
    # Maps a value from one range to another
    return max(min((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min, out_max), out_min)

# 6. Telemetry Loop
while True:
    try:
        # Check for calibration updates in settings.toml
        dry_val = os.getenv("DRY_VAL")
        wet_val = os.getenv("WET_VAL")
        
        # Fallback and type correction
        dry = int(dry_val) if dry_val is not None else 330
        wet = int(wet_val) if wet_val is not None else 1015

        # Read raw data from the Seesaw chip
        moisture_val = soil_sensor.moisture_read()
        temperature_c = soil_sensor.get_temp()
        temperature_f = temperature_c * 9 / 5 + 32
        
        # Calculate Battery Voltage (halved via divider, 3.3V ref, 0.9 correction)
        battery_voltage = (vbat_pin.value * 3.3 * 2 * 0.9) / 65535
        
        # Calculate Percentages
        moisture_percent = int(map_range(moisture_val, dry, wet, 0, 100))
        # Battery range: 3.2V (0%) to 4.15V (100%)
        battery_percent = int(map_range(battery_voltage, 3.2, 4.15, 0, 100))
        
        print(f"Update -> Moist: {moisture_percent}% | Temp: {temperature_f:.1f}F | Battery: {battery_percent}% ({battery_voltage:.2f}V)")

        # Transmit
        io_client.send_data(moisture_feed["key"], moisture_percent)
        io_client.send_data(temp_feed["key"], f"{temperature_f:.2f}")
        # Sending battery as a percentage now
        io_client.send_data(battery_feed["key"], battery_percent)
        print("Sent successfully.")

    except Exception as e:
        print(f"Telemetry Failure: {e}")

    # Delay to comply with Adafruit IO rate limits
    time.sleep(60) 
