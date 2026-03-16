import time
import board
import terminalio
import displayio
import math
import gc
import random
import os
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# --- CONSTANTS & CONFIG ---
PLANT_CONFIG = {
    "plant-1-moisture": {"name": "FIG", "variant": 1},
}
REFRESH_RATE = 600
ROTATION_INTERVAL = 15 

# Display Modes: "NORMAL", "SPRITE_DEMO"
DISPLAY_MODE = "NORMAL" 

COLORS = {
    "BLACK":  0x000000,
    "GREEN":  0x00FF00,
    "YELLOW": 0xFFFF00,
    "RED":    0xFF0000,
    "BROWN":  0x884400,
    "TEXT":   0xFFFFFF,
    "PCT":    0xAAAAAA,
}

# Sprite Data (simplified for memory stability)
SPRITE_DATA = [
    # VARIANT 1: FIG
    ("00000000000000000000000000000000000000000100000000000001110000000000001111100000000011100111000000011110011110000011101001011100011110100101111001111110011111100111011001101110001111111111110000011010010110000000111111110000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000"),
    # THIRSTY
    ("0000000000000000000000000000000000000000000000000000000222200000000000220022000000000220000220000000220000022200000022000022222000002200002222200000022000022200000000220000200000000002200000000000000220000000000000022000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000"),
    # CRITICAL
    ("00000000000000000000000000000000000000000000000000000000000030000000000000330000000000000330000000030000003300000003300003300000000033003300000000000333300003000000000330000330000000003300033000000000033003300000000000333300000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000")
]

class PlantUI:
    SPRITE_W = 16
    SPRITE_H = 20
    def __init__(self, name, feed_id, font, sheet, palette):
        self.name = name
        self.feed_id = feed_id
        self.group = displayio.Group()
        self.tile_grid = displayio.TileGrid(sheet, pixel_shader=palette, width=1, height=1, tile_width=16, tile_height=20)
        self.tile_grid.y = 6
        self.group.append(self.tile_grid)
        self.pct_label = label.Label(font, text="--%", color=COLORS["PCT"])
        self.pct_label.anchor_point, self.pct_label.anchored_position = ((0.5, 0.0), (8, 0))
        self.group.append(self.pct_label)
        self.name_label = label.Label(font, text=name, color=COLORS["TEXT"])
        self.name_label.anchor_point, self.name_label.anchored_position = ((0.5, 1.0), (8, 32))
        self.group.append(self.name_label)
    def update(self, val):
        self.pct_label.text = f"{val}%"
        state = 0 if val >= 50 else (1 if val >= 20 else 2)
        self.tile_grid[0] = state

class PlantMonitor:
    def __init__(self):
        print("Booting Hub...")
        self.matrixportal = MatrixPortal(bit_depth=2, debug=False)
        self.group = displayio.Group()
        self.matrixportal.display.root_group = self.group
        self.font = terminalio.FONT
        self.palette = displayio.Palette(5)
        for i, c in enumerate([0x000000, 0x00FF00, 0xFFFF00, 0xFF0000, 0x884400]): self.palette[i] = c
        self.sheet = displayio.Bitmap(16 * len(SPRITE_DATA), 20, 5)
        for s, d in enumerate(SPRITE_DATA):
            for i in range(320): self.sheet[s*16+(i%16), i//16] = int(d[i])
        
        self.status = label.Label(self.font, text="Init...", color=0xFFFFFF)
        self.status.anchor_point, self.status.anchored_position = ((0.5, 0.5), (32, 16))
        self.group.append(self.status)
        
        self.plants = []
        self._discover()
        self.group.remove(self.status)
        self._refresh_display()

    def _discover(self):
        self.status.text = "WiFi..."
        try:
            self.matrixportal.network.connect()
            self.status.text = "Feed..."
            io = self.matrixportal.network.io_http
            feeds = io.get_feeds()
            print(f"Found {len(feeds)} feeds")
            for f in feeds:
                key = str(f.get('key',''))
                if key.endswith("-moisture"):
                    name = key.replace("-moisture","").upper()
                    print(f"Found: {name}")
                    self.plants.append(PlantUI(name, key, self.font, self.sheet, self.palette))
        except Exception as e:
            print(f"Error: {e}")
        
        if not self.plants:
            print("Fallback to Fig")
            self.plants.append(PlantUI("FIG", "plant-1-moisture", self.font, self.sheet, self.palette))

    def _refresh_display(self):
        while len(self.group) > 0: self.group.pop()
        for i, p in enumerate(self.plants[:3]):
            p.group.x = (i * 20) + 2
            self.group.append(p.group)

    def run(self):
        last_fetch = 0
        while True:
            if time.monotonic() - last_fetch > 600 or last_fetch == 0:
                print("Fetching data...")
                for p in self.plants:
                    try:
                        d = self.matrixportal.get_io_data(p.feed_id)
                        p.update(int(float(d[0]['value'])) if d else 0)
                    except: print(f"Error {p.feed_id}")
                last_fetch = time.monotonic()
            time.sleep(1)

if __name__ == "__main__":
    PlantMonitor().run()