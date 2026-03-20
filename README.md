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
* 1x **Controller:** [Adafruit Matrix Portal M4](https://www.adafruit.com/product/4745)
* 1x **Display:** 64x32 RGB LED Matrix (P3 or P4 pitch)
* 1x **Power:** USB-C Power Supply (5V, 2A+ recommended)

---

## 🛠 Assembly

### Software Features
- **Centralized Mapping**: The dashboard maps generic sensor feeds (e.g., `sensor-1-moisture`) to custom names and sprite variants via a local `plants.json` file. No sensor reflashing required to swap plants!
- **Battery Monitoring**: Telemetry includes a calibrated battery percentage (0-100%) for power management.
- **Dynamic Calibration**: Sensor nodes read `DRY_VAL` and `WET_VAL` directly from `settings.toml` without firmware reflashing.

### Sensor Nodes
1.  **Soldering:** Solder the **LiPo Charger BFF** to the back of the **QT Py ESP32-S3**.
    * *Note:* Ensure the "Top" of the BFF aligns with the "Top" of the QT Py (USB port side).
2.  **Battery:** Plug the 420mAh LiPo battery into the JST port on the BFF.
3.  **Sensor:** Connect the **STEMMA Soil Sensor** to the QT Py using the **STEMMA QT Cable**.
4.  **Mounting:** Velcro or tape the battery/board "sandwich" to the back of your plant pot, and insert the sensor into the soil (up to the line).

### Dashboard Hub
1.  **Mounting:** Plug the **Matrix Portal M4** directly into the input header on the back of the **64x32 LED Matrix**.
2.  **Power:** Connect the USB-C cable to the Matrix Portal.
3.  **Important:** Ensure the screw terminals on the Matrix Portal are tightened if you are using the separate power fork connectors.

---

## ☁️ Adafruit IO Setup

1.  Create an account at [io.adafruit.com](https://io.adafruit.com).
2.  Create **Feeds** for each sensor. We recommend using generic names so the sensor firmware never needs to change:
    * `sensor-1-moisture`
    * `sensor-2-moisture`
    * `sensor-3-moisture`
3.  Note your **AIO Username** and **AIO Key** (found by clicking the yellow key icon on the dashboard).

---

## 💾 Software Installation

### 1. The Sensor Nodes (QT Py ESP32-S3)
* **CircuitPython Version:** 9.x or 10.x (stable).
* **Deep Sleep:** These nodes wake up, measure, transmit, and sleep for 1 hour to save battery.

**File Structure (`sensor-firmware/`):**
```text
CIRCUITPY/
├── lib/                       # NOW INCLUDED in this repo!
│   ├── adafruit_bus_device/
│   ├── adafruit_connection_manager.mpy
│   ├── adafruit_io/
│   ├── adafruit_logging.mpy
│   ├── adafruit_minimqtt/
│   ├── adafruit_requests.mpy
│   ├── adafruit_seesaw/
│   └── adafruit_ticks.mpy
├── code.py                    # The sensor logic
└── settings.toml              # WiFi and API keys (ignored by Git)
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

### 2. The Dashboard Hub (Matrix Portal M4)
* **CircuitPython Version:** **10.x** (Required for latest MatrixPortal graphics optimizations).
* **Display:** 64x32 Grid with custom "Tom Thumb" font for compact text.
* **Architecture:** Uses `PlantUI` for component-based rendering and `PlantMonitor` for application logic.

**File Structure (`hub-firmware/`):**
```text
CIRCUITPY/
├── fonts/
│   └── tom-thumb.bdf          # REQUIRED: Tiny pixel font
├── lib/
│   ├── adafruit_bitmap_font/
│   ├── adafruit_bus_device/
│   ├── adafruit_display_shapes/
│   ├── adafruit_display_text/
│   ├── adafruit_esp32spi/     # For M4 Wifi
│   ├── adafruit_io/
│   ├── adafruit_matrixportal/
│   ├── adafruit_portalbase/
│   ├── adafruit_requests.mpy
│   └── neopixel.mpy
├── code.py                    # The dashboard logic
└── settings.toml              # WiFi and API keys (ignored by Git)
```

**Configuration (`settings.toml`):**
```toml
CIRCUITPY_WIFI_SSID = "Your_WiFi_Name"
CIRCUITPY_WIFI_PASSWORD = "Your_WiFi_Password"
# MatrixPortal M4 handles AIO keys via settings.toml
aio_username = "your_username"
aio_key = "your_active_key"
```

**Application Modes (`DISPLAY_MODE`):**
*   `NORMAL`: Fetches data from Adafruit IO.
*   `SPRITE_DEMO`: Cycles through all available plant variants.
*   `FEED_DEBUG`: Tests UI states (Healthy, Thirsty, Critical) with local mock data.

---

## 🎨 Sprite System

The hub uses a custom sprite system designed for the 64x32 matrix.

*   **Format:** 16x20 pixel sprites.
*   **Palette:** 5-color HSL-adjacent palette (Black, Green, Yellow, Red, Brown).
*   **Optimization:** Configured with `bit_depth=2` for memory efficiency on the M4.
*   **Variants:** Includes 10 unique healthy plant variants (Broadleaf, Cactus, Fern, Bonsai, Bamboo, Succulent, Vine, Palm, Snake Plant, Monstera) plus 2 universal health states (Thirsty, Critical).

**Plant Configuration (`plants.json`):**
Create this file in the root of the Hub's `CIRCUITPY` drive.
```json
[
  {"key": "sensor-1-moisture", "name": "FERN", "variant": 0},
  {"key": "sensor-2-moisture", "name": "SNAK", "variant": 1}
]
```
*   `key`: The Adafruit IO feed key (e.g., `sensor-1-moisture`).
*   `name`: 4-character label displayed on the matrix.
*   `variant`: Sprite index (0-9 for healthy variants).

---

## 🧩 Calibration

The soil sensors return a "Raw Capacitance" value (usually between 200 and 2000). You must calibrate the range in the Sensor Node `code.py`:

```python
# Inside code.py on the QT Py
DRY_VAL = 350   # Value when sensor is in dry air
WET_VAL = 1015  # Value when sensor is in a cup of water
```

Adjust these numbers based on your specific soil type for accurate percentages.

### 🛠 New Sensor Troubleshooting & Setup

If a new sensor is not mounting or needs a fresh install:

1.  **Power Isolation:** If the board won't mount, unplug the LiPo battery and STEMMA sensor. Connect *only* the QT Py board to rule out power draw/short issues.
2.  **Enter Bootloader:** Double-tap the **Reset** button quickly. The NeoPixel should pulse green, and a drive named `QTPYS3BOOT` will appear.
3.  **Flash Firmware:** 
    - Use the **[Web Serial Installer](https://circuitpython.org/board/adafruit_qtpy_esp32s3_4mbflash_2mbpsram/)** for the easiest setup.
    - If the web installer hangs, download the `.uf2` file manually and drag it onto the `QTPYS3BOOT` drive.
4.  **Initial Files:** Once the drive reboots as `CIRCUITPY`, copy `code.py` and the `lib/` folder from `sensor-firmware/` in this repository.

---

## 📚 Resources
* **Font:** [Tom Thumb BDF](https://github.com/apparentlymart/led-matrix-fonts/blob/master/tom-thumb.bdf) (Right Click -> Save As)
* **Library Bundle:** [Adafruit CircuitPython Bundle](https://circuitpython.org/libraries)
