import time
import gc
import board
import os
import json
import displayio
import terminalio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.network import Network
from adafruit_io.adafruit_io import IO_HTTP
from sprites import SPRITE_DATA

# ---- INIT ----
matrix = Matrix(bit_depth=2)
display = matrix.display
display.brightness = 0.5

font = terminalio.FONT
try:
    font = bitmap_font.load_font("/fonts/tom-thumb.bdf")
except:
    pass

palette = displayio.Palette(5)
for i, c in enumerate([0x000000, 0x00FF00, 0xFFFF00, 0xFF0000, 0x884400]):
    palette[i] = c

sheet = displayio.Bitmap(16 * len(SPRITE_DATA), 20, 5)
for s, d in enumerate(SPRITE_DATA):
    for i in range(320):
        sheet[s * 16 + (i % 16), i // 16] = int(d[i])

NUM_HEALTHY = len(SPRITE_DATA) - 2

def sprite_index(moisture, variant):
    if moisture < 20: return len(SPRITE_DATA) - 1
    if moisture < 50: return len(SPRITE_DATA) - 2
    return variant % NUM_HEALTHY

def make_plant(name, x, variant):
    g = displayio.Group()
    g.x = x
    tg = displayio.TileGrid(sheet, pixel_shader=palette, width=1, height=1, tile_width=16, tile_height=20)
    tg.x = 1
    tg.y = 6
    g.append(tg)
    pct = label.Label(font, text="--%", color=0xAAAAAA)
    pct.anchor_point = (0.5, 0.0)
    pct.anchored_position = (9, 1)
    g.append(pct)
    name_lbl = label.Label(font, text=name[:4].upper(), color=0xFFFFFF)
    name_lbl.anchor_point = (0.5, 1.0)
    name_lbl.anchored_position = (9, 31)
    g.append(name_lbl)
    return g, tg, pct

# ---- STATUS MSG ----
status_group = displayio.Group()
status_lbl = label.Label(font, text="CONNECTING...", color=0x00FF00)
status_lbl.anchor_point = (0.5, 0.5)
status_lbl.anchored_position = (32, 16)
status_group.append(status_lbl)
display.root_group = status_group

# ---- NETWORK ----
plants = []
aio_client = None
try:
    net = Network(debug=False)
    net.connect()
    aio_username = os.getenv("AIO_USERNAME")
    aio_key = os.getenv("AIO_KEY")
    aio_client = IO_HTTP(aio_username, aio_key, net.requests)
    # receive_data returns dict, just confirm connection works
    status_lbl.text = "CONNECTED"
except Exception as e:
    print(f"Network error: {e}")

# ---- CONFIG ----
plants = []
try:
    with open("/plants.json", "r") as f:
        plants = json.load(f)
    for p in plants:
        p["moisture"] = None
    print(f"Loaded {len(plants)} plants from config.")
except Exception as e:
    print(f"Config error: {e}")
    # Fallback
    plants = [{"key": "plant-1-moisture", "name": "LGP", "variant": 7, "moisture": None}]

# ---- BUILD UI ----
main = displayio.Group()
count = len(plants[:3])
margin = (64 - count * 19) // 2
plant_widgets = []

for idx, p in enumerate(plants[:3]):
    x = margin + idx * 19
    g, tg, pct = make_plant(p["name"], x, p["variant"])
    main.append(g)
    plant_widgets.append({"tg": tg, "pct": pct, "data": p})

display.root_group = main
gc.collect()
print(f"UI ready. {gc.mem_free()} bytes free.")

# ---- MAIN LOOP ----
last_update = 0.0
UPDATE_INTERVAL = 600.0  # 10 min

while True:
    now = time.monotonic()
    if now - last_update > UPDATE_INTERVAL or last_update == 0:
        for w in plant_widgets:
            p = w["data"]
            try:
                print(f"Fetching {p['key']}...")
                resp = aio_client.receive_data(p["key"])
                val = int(float(resp["value"]))
                p["moisture"] = val
                w["pct"].text = f"{val}%"
                w["tg"][0] = sprite_index(val, p["variant"])
                print(f"  {p['name']}: {val}%")
            except Exception as e:
                print(f"Fetch error {p['name']}: {e}")
        last_update = time.monotonic()
        gc.collect()

    time.sleep(5)