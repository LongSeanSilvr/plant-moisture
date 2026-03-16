import time
import board
import digitalio
import gc

# Status LED Configuration
pixel = digitalio.DigitalInOut(board.NEOPIXEL)
pixel.direction = digitalio.Direction.OUTPUT

def set_pixel(val):
    pixel.value = val

print("BOOT START")

# 1. PURPLE BLINK (Stabilization 10s)
for i in range(10):
    set_pixel(True)
    time.sleep(0.5)
    set_pixel(False)
    time.sleep(0.5)

# 2. SOLID ON (Loading Libs)
set_pixel(True)
import displayio
import terminalio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text import label
import adafruit_requests
from adafruit_matrixportal.network import Network
from adafruit_bitmap_font import bitmap_font
gc.collect()

# 3. ON/OFF RAPID (Init Display)
for i in range(10):
    set_pixel(True); time.sleep(0.1)
    set_pixel(False); time.sleep(0.1)

matrix = Matrix(bit_depth=1)
display = matrix.display
main_group = displayio.Group()
display.root_group = main_group

status = label.Label(terminalio.FONT, text="BOOTING...", color=0x00FF00)
status.anchor_point, status.anchored_position = ((0.5, 0.5), (32, 16))
main_group.append(status)

# Load Font
try: font = bitmap_font.load_font("/fonts/tom-thumb.bdf")
except: font = terminalio.FONT

# Sprites
SPRITE_DATA = [
    "00000000000000000000000000000000000000000100000000000001110000000000001111100000000011100111000000011110011110000011101001011100011110100101111001111110011111100111011001101110001111111111110000011010010110000000111111110000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "0000000000000000000000000000000000000001100000000000000110001100000110011001110000011001100110000001100110011000000111111001100000001111111110000000000111110000000000011000000000000000110000000000000001100000000000000011000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "00000000000000000000000000000000000000000000000000000000000000000000000222200000000000220022000000000220000220000000220000022200000022000022222000002200002222200000022000022200000000220000200000000002200000000000000220000000000000022000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000330000000000000330000000030000003300000003300003300000000033003300000000000333300003000000000330000330000000003300033000000000033003300000000000333300000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000"
]
palette = displayio.Palette(5)
for i, c in enumerate([0x0, 0x00FF00, 0xFFFF00, 0xFF0000, 0x884400]): palette[i] = c
sheet = displayio.Bitmap(16 * len(SPRITE_DATA), 20, 5)
for s, d in enumerate(SPRITE_DATA):
    for i in range(len(d)): sheet[s*16+(i%16), i//16] = int(d[i])
gc.collect()

class PlantUI:
    def __init__(self, name, f_id):
        self.name, self.f_id = name, f_id
        self.group = displayio.Group()
        self.tg = displayio.TileGrid(sheet, pixel_shader=palette, width=1, height=1, tile_width=16, tile_height=20)
        self.tg.y = 6
        self.pct = label.Label(font, text="--%", color=0xAAAAAA)
        self.pct.anchor_point, self.pct.anchored_position = ((0.5, 0.0), (8, 0))
        self.lbl = label.Label(font, text=name[:3].upper(), color=0xFFFFFF)
        self.lbl.anchor_point, self.lbl.anchored_position = ((0.5, 1.0), (8, 32))
        self.group.append(self.tg); self.group.append(self.pct); self.group.append(self.lbl)
    def update(self, val):
        self.pct.text = f"{val}%"
        self.tg[0] = 0 if val >= 50 else (1 if val >= 20 else 2)

# 4. WIFI (Solid On during connect)
set_pixel(True)
status.text = "WIFI..."
try:
    network = Network(debug=False)
    network.connect()
    status.text = "SCAN..."
    io = network.io_http
    feeds = io.get_feeds()
    plants = []
    for f in feeds:
        key = str(f.get('key',''))
        if key.endswith('-moisture'):
            plants.append(PlantUI(key.replace('-moisture','').upper(), key))
except Exception as e:
    print(f"Error: {e}")
    plants = [PlantUI("FIG", "plant-1-moisture")]

if not plants: plants = [PlantUI("FIG", "plant-1-moisture")]

# SUCCESS
main_group.remove(status)
for i, p in enumerate(plants[:3]):
    p.group.x = (64 - (len(plants[:3])*19))//2 + (i * 19)
    main_group.append(p.group)

# 5. RUN LOOP (Breath effect)
while True:
    for i in range(100):
        set_pixel(i % 10 == 0) # Tiny tick
        time.sleep(0.1)
    # Fetch
    for p in plants:
        try:
            data = network.io_http.get(f"https://io.adafruit.com/api/v2/{network.user}/feeds/{p.f_id}/data/last")
            p.update(int(float(data.json().get('value', 0))))
        except: pass
    gc.collect()