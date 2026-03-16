import os
import time
import board
import busio
import wifi
import adafruit_connection_manager
import adafruit_requests
import analogio
import alarm
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
from adafruit_seesaw.seesaw import Seesaw

# 1. Hardware Initialization
print("Initializing Firmware (Deep Sleep Mode)...")
i2c_bus = board.STEMMA_I2C()
soil_sensor = Seesaw(i2c_bus, addr=0x36)

# Battery monitor on pin A2 (halved via voltage divider on BFF)
vbat_pin = analogio.AnalogIn(board.A2)

# 2. Network Authentication
ssid = os.getenv('CIRCUITPY_WIFI_SSID')
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

print(f"Connecting to SSID: {ssid}")
try:
    wifi.radio.connect(ssid, password)
    print(f"Connected. IP: {wifi.radio.ipv4_address}")
except Exception as e:
    print(f"WiFi Connection Failed: {e}")
    # Still proceed to sleep to save battery even if WiFi fails
    pass

# 3. Adafruit IO Session Setup
if wifi.radio.ipv4_address:
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

    # 5. Calibration Helpers
    def map_range(x, in_min, in_max, out_min, out_max):
        return max(min((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min, out_max), out_min)

    # 6. Read and Transmit (Once)
    try:
        # Dynamic Calibration Lookup
        dry = int(os.getenv("DRY_VAL", 330))
        wet = int(os.getenv("WET_VAL", 1015))

        # Sensory Data
        moisture_val = soil_sensor.moisture_read()
        temperature_c = soil_sensor.get_temp()
        temperature_f = temperature_c * 9 / 5 + 32
        
        # Battery Voltage (Correcting for divider and ADC reference)
        # Using 3.3V ref, 16-bit range, 2:1 divider. 
        # Adding a 0.9 calibration factor to correct 4.64V -> ~4.17V (Full battery)
        battery_voltage = (vbat_pin.value * 3.3 * 2 * 0.9) / 65535
        
        moisture_percent = int(map_range(moisture_val, dry, wet, 0, 100))
        
        print(f"Telemetry -> Raw:{moisture_val} | Moist:{moisture_percent}% | Batt:{battery_voltage:.2f}V")

        # Transmit
        io_client.send_data(moisture_feed["key"], moisture_percent)
        io_client.send_data(temp_feed["key"], f"{temperature_f:.2f}")
        io_client.send_data(battery_feed["key"], f"{battery_voltage:.2f}")
        print("Transmission Successful.")

    except Exception as e:
        print(f"Telemetry Failure: {e}")

# 7. Enter Deep Sleep
sleep_duration = int(os.getenv("SLEEP_SECONDS", 3600))
print(f"Cycle Complete. Entering Deep Sleep for {sleep_duration} seconds...")

time_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + sleep_duration)
alarm.exit_and_deep_sleep_until_alarms(time_alarm)
