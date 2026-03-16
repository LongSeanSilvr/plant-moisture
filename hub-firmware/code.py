import time
import gc

# 1. BOOT DELAY
print("BOOTING (5s)...")
time.sleep(5)

import board
import terminalio
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label

# 2. SINGLE INIT (MatrixPortal handles the display)
print("Init MatrixPortal...")
mp = MatrixPortal(bit_depth=1, debug=False) 
display = mp.display
group = displayio.Group()
display.root_group = group

# Status display
status = label.Label(terminalio.FONT, text="WIFI...", color=0x00FF00)
status.anchor_point, status.anchored_position = ((0.5, 0.5), (32, 16))
group.append(status)

def set_status(txt):
    print(f"STATUS: {txt}")
    status.text = txt
    gc.collect()

# Configuration
PLANT_CONFIG = {}

class PlantUI:
    def __init__(self, name, f_id):
        self.name, self.f_id = name, f_id
        self.group = displayio.Group()
        self.pct = label.Label(terminalio.FONT, text="--%", color=0xAAAAAA)
        self.pct.anchor_point, self.pct.anchored_position = ((0.5, 0.0), (8, 0))
        self.lbl = label.Label(terminalio.FONT, text=name[:3].upper(), color=0xFFFFFF)
        self.lbl.anchor_point, self.lbl.anchored_position = ((0.5, 1.0), (8, 32))
        self.group.append(self.pct); self.group.append(self.lbl)
    def update(self, val): self.pct.text = f"{val}%"

class Hub:
    def __init__(self):
        self.plants = []
        self._setup()
    
    def _setup(self):
        set_status("CONNECT...")
        try:
            mp.network.connect()
            set_status("SCAN FEED...")
            io = mp.network.io_http
            all_feeds = io.get_feeds()
            for f in all_feeds:
                key = str(f.get('key',''))
                if key.endswith('-moisture'):
                    name = key.replace('-moisture','').upper()
                    print(f"Found: {name}")
                    self.plants.append(PlantUI(name, key))
        except Exception as e:
            print(f"Error: {e}")
        
        if not self.plants:
            print("Fallback: FIG")
            self.plants.append(PlantUI("FIG", "plant-1-moisture"))
        
        # Display plants
        group.remove(status)
        for i, p in enumerate(self.plants[:3]):
            p.group.x = (i * 20) + 2
            group.append(p.group)

    def run(self):
        last_fetch = 0
        while True:
            if time.monotonic() - last_fetch > 600 or last_fetch == 0:
                print("Updating data...")
                for p in self.plants:
                    try:
                        d = mp.get_io_data(p.f_id)
                        p.update(int(float(d[0]['value'])) if d else 0)
                    except Exception as e:
                        print(f"Update error {p.f_id}: {e}")
                last_fetch = time.monotonic()
            time.sleep(1)

if __name__ == "__main__":
    Hub().run()