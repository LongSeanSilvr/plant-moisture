import time
import gc

# 1. IMMEDIATE STARTUP DELAY (Stabilizes USB/Power)
print("BOOT DELAY (5s)...")
time.sleep(5)

import board
import terminalio
import displayio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text import label

# 2. IMMEDIATE DISPLAY INIT (Show status to user!)
matrix = Matrix(bit_depth=1) # bit_depth=1 saves a lot of memory
display = matrix.display
group = displayio.Group()
display.root_group = group

# Custom Palette
palette = displayio.Palette(5)
palette[0] = 0x000000 # Black
palette[1] = 0x00FF00 # Green
palette[2] = 0xFFFF00 # Yellow
palette[3] = 0xFF0000 # Red
palette[4] = 0x884400 # Brown

status = label.Label(terminalio.FONT, text="BOOT...", color=0x00FF00)
status.anchor_point, status.anchored_position = ((0.5, 0.5), (32, 16))
group.append(status)

def set_status(txt):
    print(f"STATUS: {txt}")
    status.text = txt
    gc.collect()

# 3. LATE IMPORTS (Save memory during display init)
import adafruit_requests
import adafruit_esp32spi.adafruit_esp32spi_socketpool as socketpool
from adafruit_matrixportal.matrixportal import MatrixPortal

# Configuration Overrides
PLANT_CONFIG = { "plant-1-moisture": {"name": "FIG", "variant": 1} }

class PlantUI:
    def __init__(self, name, f_id):
        self.name, self.f_id = name, f_id
        self.group = displayio.Group()
        self.pct = label.Label(terminalio.FONT, text="--%", color=0xAAAAAA)
        self.pct.anchor_point, self.pct.anchored_position = ((0.5, 0.0), (8, 0))
        self.lbl = label.Label(terminalio.FONT, text=name[:3], color=0xFFFFFF)
        self.lbl.anchor_point, self.lbl.anchored_position = ((0.5, 1.0), (8, 32))
        self.group.append(self.pct); self.group.append(self.lbl)
    def update(self, val): self.pct.text = f"{val}%"

class Hub:
    def __init__(self):
        self.mp = MatrixPortal(bit_depth=1, debug=False)
        self.plants = []
        self._setup()
    
    def _setup(self):
        set_status("WIFI...")
        try:
            self.mp.network.connect()
            set_status("SCAN...")
            io = self.mp.network.io_http
            all_feeds = io.get_feeds()
            for f in all_feeds:
                key = str(f.get('key',''))
                if key.endswith('-moisture'):
                    name = key.replace('-moisture','').upper()
                    self.plants.append(PlantUI(name, key))
        except Exception as e:
            print(f"Scan Error: {e}")
        
        if not self.plants:
            self.plants.append(PlantUI("FIG", "plant-1-moisture"))
        
        # Switch to Plant Display
        group.remove(status)
        for i, p in enumerate(self.plants[:3]):
            p.group.x = (i * 20) + 2
            group.append(p.group)

    def run(self):
        last_fetch = 0
        while True:
            if time.monotonic() - last_fetch > 600 or last_fetch == 0:
                print("Updating feeds...")
                for p in self.plants:
                    try:
                        d = self.mp.get_io_data(p.f_id)
                        p.update(int(float(d[0]['value'])) if d else 0)
                    except: pass
                last_fetch = time.monotonic()
            time.sleep(1)

if __name__ == "__main__":
    Hub().run()