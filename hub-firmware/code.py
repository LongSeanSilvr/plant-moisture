import time
import board
import digitalio
import gc
import terminalio
import displayio
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# --- STABILIZATION ---
pixel = digitalio.DigitalInOut(board.NEOPIXEL)
pixel.direction = digitalio.Direction.OUTPUT
print("STABILIZING (10s)...")
for i in range(10):
    pixel.value = (i % 2 == 0)
    time.sleep(1)
pixel.value = False

# --- CONFIG ---
REFRESH_RATE = 600
ROTATION_INTERVAL = 15
SPRITE_DATA = [
    "00000000000000000000000000000000000000000100000000000001110000000000001111100000000011100111000000011110011110000011101001011100011110100101111001111110011111100111011001101110001111111111110000011010010110000000111111110000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "0000000000000000000000000000000000000001100000000000000110001100000110011001110000011001100110000001100110011000000111111001100000001111111110000000000111110000000000011000000000000000110000000000000001100000000000000011000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "00000000000000000000000000000000000000000000000000000000000000000000000222200000000000220022000000000220000220000000220000022200000022000022222000002200002222200000022000022200000000220000200000000002200000000000000220000000000000022000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000030000000000000330000000000000330000000030000003300000003300003300000000033003300000000000333300003000000000330000330000000003300033000000000033003300000000000333300000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000"
]

class PlantUI:
    def __init__(self, name, f_id, font, sheet, palette):
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

class PlantMonitor:
    def __init__(self):
        # 1. Surgical Display Init
        print("Init Display...")
        self.matrix = Matrix(bit_depth=1)
        self.display = self.matrix.display
        self.main_group = displayio.Group()
        self.display.root_group = self.main_group
        
        # Load Premium Font
        try: self.font = bitmap_font.load_font("/fonts/tom-thumb.bdf")
        except: self.font = terminalio.FONT
            
        self.status = label.Label(self.font, text="CONNECTING...", color=0x00FF00)
        self.status.anchor_point, self.status.anchored_position = ((0.5, 0.5), (32, 16))
        self.main_group.append(self.status)

        # 2. Network Init
        print("Init Network...")
        self.network = Network(status_neopixel=None, debug=False)
        self.plants = []
        
        # 3. Assets
        self.palette = displayio.Palette(5)
        for i, c in enumerate([0x0, 0x00FF00, 0xFFFF00, 0xFF0000, 0x884400]): self.palette[i] = c
        self.sheet = displayio.Bitmap(16 * len(SPRITE_DATA), 20, 5)
        for s, d in enumerate(SPRITE_DATA):
            for i in range(len(d)): self.sheet[s*16+(i%16), i//16] = int(d[i])
            
        self._setup()

    def _setup(self):
        try:
            self.network.connect()
            self.status.text = "SCANNING..."
            io = self.network.io_http
            feeds = io.get_feeds()
            for f in feeds:
                key = str(f.get('key',''))
                if key.endswith('-moisture'):
                    name = key.replace('-moisture','').upper()
                    self.plants.append(PlantUI(name, key, self.font, self.sheet, self.palette))
        except Exception as e: print(f"Error: {e}")
        
        if not self.plants: self.plants.append(PlantUI("FIG", "plant-1-moisture", self.font, self.sheet, self.palette))
        
        self.main_group.remove(self.status)
        for i, p in enumerate(self.plants[:3]):
            p.group.x = (64 - (len(self.plants[:3])*19))//2 + (i * 19)
            self.main_group.append(p.group)

    def run(self):
        last_fetch = 0
        while True:
            if time.monotonic() - last_fetch > 600 or last_fetch == 0:
                print("Fetching...")
                for p in self.plants:
                    try:
                        d = self.network.io_http.get_feed_data(p.f_id)
                        p.update(int(float(d[0]['value'])) if d else 0)
                    except: pass
                last_fetch = time.monotonic()
            time.sleep(1)

if __name__ == "__main__":
    PlantMonitor().run()