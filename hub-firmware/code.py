import time
import board
import digitalio
import gc
import terminalio
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label

# --- STABILIZATION ---
# 1. Visual Heartbeat & Boot Delay
pixel = digitalio.DigitalInOut(board.NEOPIXEL)
pixel.direction = digitalio.Direction.OUTPUT
print("BOOTING (10s)...")
for i in range(10):
    pixel.value = (i % 2 == 0)
    time.sleep(1)
pixel.value = False

# --- CONFIG & ASSETS ---
PLANT_CONFIG = { "plant-1-moisture": {"name": "FIG", "variant": 1} }
REFRESH_RATE = 600
ROTATION_INTERVAL = 15

# Color Palette
COLORS = {
    "BLACK":  0x000000,
    "GREEN":  0x00FF00,
    "YELLOW": 0xFFFF00,
    "RED":    0xFF0000,
    "BROWN":  0x884400,
    "TEXT":   0xFFFFFF,
    "PCT":    0xAAAAAA,
}

# Condensed Sprite Data (Memory efficient)
# Indices: 0: Healthy (Fig), 1: Thirsty, 2: Critical
SPRITE_DATA = [
    # FIG
    "00000000000000000000000000000000000000000100000000000001110000000000001111100000000011100111000000011110011110000011101001011100011110100101111001111110011111100111011001101110001111111111110000011010010110000000111111110000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    # THIRSTY
    "0000000000000000000000000000000000000000000000000000000222200000000000220022000000000220000220000000220000022200000022000022222000002200002222200000022000022200000000220000200000000002200000000000000220000000000000022000000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000",
    # CRITICAL
    "00000000000000000000000000000000000000000000000000000000000030000000000000330000000000000330000000030000003300000003300003300000000033003300000000000333300003000000000330000330000000003300033000000000033003300000000000333300000000000444444444400000444444444444000044444444444400000444444444400000000000000000000000000000000000"
]

class PlantUI:
    def __init__(self, name, feed_id, sheet, palette):
        self.name = name
        self.feed_id = feed_id
        self.group = displayio.Group()
        
        # Sprite
        self.tg = displayio.TileGrid(sheet, pixel_shader=palette, width=1, height=1, tile_width=16, tile_height=20)
        self.tg.y = 6
        self.group.append(self.tg)
        
        # Labels
        self.pct = label.Label(terminalio.FONT, text="--%", color=COLORS["PCT"])
        self.pct.anchor_point, self.pct.anchored_position = ((0.5, 0.0), (8, 0))
        self.group.append(self.pct)
        
        self.lbl = label.Label(terminalio.FONT, text=name[:3].upper(), color=COLORS["TEXT"])
        self.lbl.anchor_point, self.lbl.anchored_position = ((0.5, 1.0), (8, 32))
        self.group.append(self.lbl)

    def update(self, val):
        self.pct.text = f"{val}%"
        state = 0 if val >= 50 else (1 if val >= 20 else 2)
        self.tg[0] = state

class Hub:
    def __init__(self):
        print("Init Hub...")
        # Single Init MatrixPortal
        self.mp = MatrixPortal(bit_depth=1, debug=False)
        self.display = self.mp.display
        self.group = displayio.Group()
        self.display.root_group = self.group

        # Init Palette
        self.palette = displayio.Palette(5)
        self.palette[0] = COLORS["BLACK"]; self.palette[1] = COLORS["GREEN"]
        self.palette[2] = COLORS["YELLOW"]; self.palette[3] = COLORS["RED"]
        self.palette[4] = COLORS["BROWN"]

        # Init Spritesheet
        self.sheet = displayio.Bitmap(16 * len(SPRITE_DATA), 20, 5)
        for s, d in enumerate(SPRITE_DATA):
            for i in range(320): self.sheet[s*16+(i%16), i//16] = int(d[i])

        # Status Label
        self.status = label.Label(terminalio.FONT, text="BOOT...", color=COLORS["GREEN"])
        self.status.anchor_point, self.status.anchored_position = ((0.5, 0.5), (32, 16))
        self.group.append(self.status)
        
        self.plants = []
        self._setup()

    def set_status(self, txt):
        print(f"STATUS: {txt}")
        self.status.text = txt
        gc.collect()

    def _setup(self):
        self.set_status("CONNECT...")
        try:
            self.mp.network.connect()
            self.set_status("SCANNING...")
            io = self.mp.network.io_http
            feeds = io.get_feeds()
            print(f"Found {len(feeds)} feeds")
            for f in feeds:
                key = str(f.get('key',''))
                if key.endswith('-moisture'):
                    name = key.replace('-moisture','').upper()
                    # Check overrides
                    cfg = PLANT_CONFIG.get(key, {})
                    label_name = cfg.get("name", name)
                    print(f"Adding: {label_name}")
                    self.plants.append(PlantUI(label_name, key, self.sheet, self.palette))
        except Exception as e:
            print(f"Discovery Error: {e}")
        
        if not self.plants:
            print("Fallback: FIG")
            self.plants.append(PlantUI("FIG", "plant-1-moisture", self.sheet, self.palette))

        self.group.remove(self.status)
        self._layout()

    def _layout(self):
        # Center alignment for 1-3 plants
        count = len(self.plants[:3])
        total_w = (count * 16) + ((count - 1) * 4)
        start_x = (64 - total_w) // 2
        for i, p in enumerate(self.plants[:3]):
            p.group.x = start_x + (i * 20)
            self.group.append(p.group)

    def run(self):
        last_fetch = 0
        while True:
            now = time.monotonic()
            if now - last_fetch >= REFRESH_RATE or last_fetch == 0:
                print("Fetching updates...")
                for p in self.plants:
                    try:
                        data = self.mp.get_io_data(p.feed_id)
                        val = int(float(data[0]['value'])) if data else 0
                        print(f" -> {p.name}: {val}%")
                        p.update(val)
                    except Exception as e: print(f"Update fail {p.feed_id}: {e}")
                last_fetch = now
                gc.collect()
            time.sleep(1)

if __name__ == "__main__":
    Hub().run()