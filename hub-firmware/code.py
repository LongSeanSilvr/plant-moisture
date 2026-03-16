import time
import board
import digitalio
import gc
import terminalio
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# --- 1. STABILIZATION (10s Boot Delay) ---
pixel = digitalio.DigitalInOut(board.NEOPIXEL)
pixel.direction = digitalio.Direction.OUTPUT
print("STABILIZING (10s)...")
for i in range(10):
    pixel.value = (i % 2 == 0)
    time.sleep(1)
pixel.value = False
gc.collect()

# --- 2. CONFIG & ASSETS ---
PLANT_CONFIG = { "plant-1-moisture": {"name": "FIG", "variant": 1} }
REFRESH_RATE = 600
ROTATION_INTERVAL = 15

COLORS = {
    "BLACK":  0x000000,
    "GREEN":  0x00FF00,
    "YELLOW": 0xFFFF00,
    "RED":    0xFF0000,
    "BROWN":  0x884400,
    "TEXT":   0xFFFFFF,
    "PCT":    0xAAAAAA,
}

# Full Premium Sprite Data
SPRITE_DATA = [
    "00000000000000000000000000000000000000000100000000000001110000000000001111100000000011100111000000011110011110000011101001011100011110100101111001111110011111100111011001101110001111111111110000011010010110000000111111110000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "0000000000000000000000000000000000000001100000000000000110001100000110011001110000011001100110000001100110011000000111111001100000001111111110000000000111110000000000011000000000000000110000000000000001100000000000000011000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "000000000000000000000000110000000000000111100000000011001100110000011101111011100011110111101111001100011110001100110001111000110001100111100110000011111111110000000111111110000000011111100000000011110000000000111100000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "0000000000000000000000000000000000000000010000000000000011100000000000111110000000000011001000000000001110100000000001110110000000001110011000000001110011100000001111000111000001111110011110000001100001100000000110011100000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "000000100000100000000110000110000000011000011000000011110011110000001111001111000000011000011000000001100001100000000110000110000000111100111100000011110011110000000110000110000000011000011000000001100001100000000110000110000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "00000000000000000000000000000000000000000000000000000000000000000000000110000000000001111000000000001111110000000000111111110000000111011011100000111101101111000011111111111100000110111101100000001100001100000000011111100000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "00000000000000000000000000000000000000000100000000000001111000000000001111100000000011111100000000011111100000000011111100000000111110000000000111000000000000100000000000000010000000000000001000000000000000100000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "0000000000000000000000000000000000100000000000000011000000001000000110000001100000001100001100000000011001100000000000111100000000000001100000000000000110000000000000011000000000000001100000000000000110000000000000011000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "000000000000000000000000100000000000000110000000000001011001000000001101101100000001100110110100000110111011011000111011101111100011101110111110001111111011111000111111111111100001111111111100000011111111100000000111111100000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "000000000000000000000000000000000000000110000000000001111110000000001101101100000001111111111000000110111101100000111111111111000011011111101100001111011011110000011111111110000000110000110000000000111100000000000001100000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "0000000000000000000000000000000000000000000000000000000222200000000000220022000000000220000220000000220000022200000022000022222000002200002222200000022000022200000000220000200000000002200000000000000220000000000000022000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    "00000000000000000000000000000000000000000000000000000000000030000000000000330000000000000330000000030000003300000003300003300000000033003300000000000333300003000000000330000330000000003300033000000000033003300000000000333300000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000"
]

class PlantUI:
    def __init__(self, name, feed_id, font, sheet, palette, variant=None):
        self.name, self.feed_id = name, feed_id
        num_healthy = len(SPRITE_DATA) - 2
        if variant is not None: self.assigned_variant = (variant - 1) % num_healthy
        else: self.assigned_variant = sum(ord(c) for c in feed_id) % num_healthy
            
        self.group = displayio.Group()
        self.tile_grid = displayio.TileGrid(sheet, pixel_shader=palette, width=1, height=1, tile_width=16, tile_height=20)
        self.tile_grid.y = 6
        self.group.append(self.tile_grid)

        self.pct_label = label.Label(font, text="--%", color=COLORS["PCT"])
        self.pct_label.anchor_point, self.pct_label.anchored_position = ((0.5, 0.0), (8, 0))
        self.group.append(self.pct_label)

        self.name_label = label.Label(font, text=name.upper(), color=COLORS["TEXT"])
        self.name_label.anchor_point, self.name_label.anchored_position = ((0.5, 1.0), (8, 32))
        self.group.append(self.name_label)

    def set_position(self, x): self.group.x = x

    def update(self, value):
        self.pct_label.text = f"{value}%"
        state = self.assigned_variant
        if value < 20: state = len(SPRITE_DATA) - 1
        elif value < 50: state = len(SPRITE_DATA) - 2
        self.tile_grid[0] = state

class PlantMonitor:
    def __init__(self):
        print("Starting Hub Monitor...")
        self.mp = MatrixPortal(bit_depth=1, debug=False)
        self.display = self.mp.display
        self.group = displayio.Group()
        self.display.root_group = self.group

        # Load Premium Font
        try: self.font = bitmap_font.load_font("/fonts/tom-thumb.bdf")
        except: self.font = terminalio.FONT
            
        self.palette = displayio.Palette(5)
        for i, c in enumerate([0x0, 0x00FF00, 0xFFFF00, 0xFF0000, 0x884400]): self.palette[i] = c
            
        self.sheet = displayio.Bitmap(16 * len(SPRITE_DATA), 20, 5)
        for s, d in enumerate(SPRITE_DATA):
            for i in range(len(d)):
                self.sheet[s*16+(i%16), i//16] = int(d[i])
        
        self.status = label.Label(self.font, text="BOOTING...", color=COLORS["GREEN"])
        self.status.anchor_point, self.status.anchored_position = ((0.5, 0.5), (32, 16))
        self.group.append(self.status)
        
        self.plants = []
        self._window_start = 0
        self._max_visible = 3
        self._setup()
        self.group.remove(self.status)
        self._update_display()

    def set_status(self, txt):
        print(f"STATUS: {txt}"); self.status.text = txt; gc.collect()

    def _setup(self):
        self.set_status("CONNECT...")
        try:
            self.mp.network.connect()
            self.set_status("SCANNING...")
            io = self.mp.network.io_http
            feeds = io.get_feeds()
            for f in feeds:
                key = str(f.get('key',''))
                if key.endswith('-moisture'):
                    name = key.replace('-moisture','').upper()
                    cfg = PLANT_CONFIG.get(key, {})
                    l_name = cfg.get("name", name)
                    self.plants.append(PlantUI(l_name, key, self.font, self.sheet, self.palette, variant=cfg.get("variant")))
        except Exception as e:
            print(f"Discovery Error: {e}")
        
        if not self.plants:
            self.plants.append(PlantUI("FIG", "plant-1-moisture", self.font, self.sheet, self.palette))

    def _update_display(self):
        while len(self.group) > 0: self.group.pop()
        count = min(len(self.plants), self._max_visible)
        total_w = (count * 16) + ((count - 1) * 3)
        margin = (64 - total_w) // 2
        for i in range(count):
            idx = (self._window_start + i) % len(self.plants)
            p = self.plants[idx]
            p.set_position(margin + (i * 19))
            self.group.append(p.group)

    def rotate(self):
        if len(self.plants) > self._max_visible:
            self._window_start = (self._window_start + 1) % len(self.plants)
            self._update_display()

    def fetch(self):
        print("Updating telemetry...")
        for p in self.plants:
            try:
                d = self.mp.get_io_data(p.feed_id)
                if d: p.update(int(float(d[0]['value'])))
            except: pass
        gc.collect()

    def run(self):
        last_fetch, last_rotate = 0, time.monotonic()
        while True:
            now = time.monotonic()
            if now - last_fetch >= REFRESH_RATE or last_fetch == 0:
                self.fetch(); last_fetch = now
            if now - last_rotate >= ROTATION_INTERVAL:
                self.rotate(); last_rotate = now
            time.sleep(1)

if __name__ == "__main__":
    PlantMonitor().run()