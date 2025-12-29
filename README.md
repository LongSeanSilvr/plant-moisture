# Plant Moisture Monitor System

A distributed plant monitoring system using Adafruit hardware and CircuitPython. This project consists of wireless, battery-operated **Sensor Nodes** that report soil moisture to Adafruit IO, and a central **Dashboard Hub** (LED Matrix) that visualizes the data.

## 📦 Hardware Requirements

### Part A: The Sensor Nodes (Per Plant)
* 1x **Microcontroller:** [Adafruit QT Py ESP32-S3](https://www.adafruit.com/product/5426) (2MB PSRAM version recommended)
* 1x **Power Management:** [LiPo Charger BFF Add-On](https://www.adafruit.com/product/5397)
* 1x **Battery:** [Lithium Ion Polymer Battery - 3.7v 420mAh](https://www.adafruit.com/product/4236)
* 1x **Sensor:** [Adafruit STEMMA Soil Sensor](https://www.adafruit.com/product/4026)
* 1x **Cable:** [STEMMA QT Cable (100mm or 50mm)](https://www.adafruit.com/product/4210)

### Part B: The Dashboard Hub
* 1x **Controller:** [Adafruit Matrix Portal S3](https://www.adafruit.com/product/5778)
* 1x **Display:** 64x32 RGB LED Matrix (P3 or P4 pitch)
* 1x **Power:** USB-C Power Supply (5V, 2A+ recommended)

---

## 🛠 Assembly

### Sensor Nodes
1.  **Soldering:** Solder the **LiPo Charger BFF** to the back of the **QT Py ESP32-S3**.
    * *Note:* Ensure the "Top" of the BFF aligns with the "Top" of the QT Py (USB port side).
2.  **Battery:** Plug the 420mAh LiPo battery into the JST port on the BFF.
3.  **Sensor:** Connect the **STEMMA Soil Sensor** to the QT Py using the **STEMMA QT Cable**.
4.  **Mounting:** Velcro or tape the battery/board "sandwich" to the back of your plant pot, and insert the sensor into the soil (up to the line).

### Dashboard Hub
1.  **Mounting:** Plug the **Matrix Portal S3** directly into the input header on the back of the **64x32 LED Matrix**.
2.  **Power:** Connect the USB-C cable to the Matrix Portal.
3.  **Important:** Ensure the screw terminals on the Matrix Portal are tightened if you are using the separate power fork connectors.

---

## ☁️ Adafruit IO Setup

1.  Create an account at [io.adafruit.com](https://io.adafruit.com).
2.  Create **Feeds** for each plant. Naming convention used in this code:
    * `plant-1`
    * `plant-2`
    * `plant-3`
3.  Note your **AIO Username** and **AIO Key** (found by clicking the yellow key icon on the dashboard).

---

## 💾 Software Installation

### 1. The Sensor Nodes (QT Py ESP32-S3)
* **CircuitPython Version:** 9.x or 10.x (stable).
* **Deep Sleep:** These nodes wake up, measure, transmit, and sleep for 1 hour to save battery.

**File Structure:**
```text
CIRCUITPY/
├── lib/
│   ├── adafruit_bus_device/   # Folder
│   ├── adafruit_requests.mpy
│   └── adafruit_seesaw.mpy
├── code.py                    # The sensor logic
└── settings.toml              # WiFi and API keys
```

**Configuration (`settings.toml`):**
```toml
CIRCUITPY_WIFI_SSID = "Your_WiFi_Name"
CIRCUITPY_WIFI_PASSWORD = "Your_WiFi_Password"
AIO_USERNAME = "your_username"
AIO_KEY = "your_active_key"
AIO_FEED_NAME = "plant-1"     # CHANGE THIS per board (plant-2, plant-3, etc)
SLEEP_SECONDS = 3600          # 1 Hour
```

### 2. The Dashboard Hub (Matrix Portal S3)
* **CircuitPython Version:** **10.x** (Required for latest MatrixPortal graphics optimizations).
* **Display:** 64x32 Grid with custom "Tom Thumb" font for compact text.

**File Structure:**
```text
CIRCUITPY/
├── fonts/
│   └── tom-thumb.bdf          # REQUIRED: Tiny pixel font
├── lib/
│   ├── adafruit_bitmap_font/  # Folder
│   ├── adafruit_bus_device/   # Folder
│   ├── adafruit_display_shapes/ # Folder
│   ├── adafruit_display_text/ # Folder
│   ├── adafruit_esp32spi/     # Folder
│   ├── adafruit_io/           # Folder
│   ├── adafruit_matrixportal/ # Folder
│   ├── adafruit_portalbase/   # Folder
│   ├── adafruit_requests.mpy
│   └── neopixel.mpy
├── code.py                    # The dashboard logic
└── settings.toml              # WiFi and API keys
```

**Configuration (`settings.toml`):**
```toml
CIRCUITPY_WIFI_SSID = "Your_WiFi_Name"
CIRCUITPY_WIFI_PASSWORD = "Your_WiFi_Password"
AIO_USERNAME = "your_username"
AIO_KEY = "your_active_key"
```

---

## 🧩 Calibration

The soil sensors return a "Raw Capacitance" value (usually between 200 and 2000). You must calibrate the range in the Sensor Node `code.py`:

```python
# Inside code.py on the QT Py
DRY_VAL = 350   # Value when sensor is in dry air
WET_VAL = 1015  # Value when sensor is in a cup of water
```

Adjust these numbers based on your specific soil type for accurate percentages.

## 📚 Resources
* **Font:** [Tom Thumb BDF](https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bitmap_Font/main/examples/fonts/tom-thumb.bdf) (Right Click -> Save As)
* **Library Bundle:** [Adafruit CircuitPython Bundle](https://circuitpython.org/libraries)
