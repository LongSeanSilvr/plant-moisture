import time
import board
import digitalio
import gc

# 1. VISUAL HEARTBEAT (Blinks NeoPixel blue during boot)
pixel = digitalio.DigitalInOut(board.NEOPIXEL)
pixel.direction = digitalio.Direction.OUTPUT

print("HEARTBEAT BOOT (10s)...")
for i in range(10):
    pixel.value = True
    time.sleep(0.5)
    pixel.value = False
    time.sleep(0.5)

import terminalio
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label

# 2. INIT DISPLAY
print("Loading MatrixPortal...")
try:
    mp = MatrixPortal(bit_depth=1, debug=False)
except Exception as e:
    print(f"Hardware Error: {e}")
    while True: time.sleep(1)

display = mp.display
group = displayio.Group()
display.root_group = group

status = label.Label(terminalio.FONT, text="CONNECTING...", color=0x00FF00)
status.anchor_point, status.anchored_position = ((0.5, 0.5), (32, 16))
group.append(status)

# 3. HUB LOGIC
class Hub:
    def __init__(self):
        self.plants = []
        self._setup()
    
    def _setup(self):
        print("WiFi Connect...")
        try:
            mp.network.connect()
            status.text = "SCANNING..."
            io = mp.network.io_http
            feeds = io.get_feeds()
            for f in feeds:
                key = str(f.get('key',''))
                if key.endswith('-moisture'):
                    name = key.replace('-moisture','').upper()
                    self.plants.append(name)
        except Exception as e:
            print(f"Setup Error: {e}")
        
        # Simple list for now to save memory
        if not self.plants:
            self.plants = ["FIG"]
        
        # Final display transition
        group.remove(status)
        for i, name in enumerate(self.plants[:3]):
            lbl = label.Label(terminalio.FONT, text=name[:3], color=0xFFFFFF)
            lbl.x = (i * 20) + 2
            lbl.y = 16
            group.append(lbl)

    def run(self):
        while True:
            print("Running...")
            time.sleep(10)

if __name__ == "__main__":
    Hub().run()