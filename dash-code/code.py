import time
import board
import terminalio
import displayio
import math
import gc
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# --- CONSTANTS & CONFIG ---
PLANT_CONFIG = {
    "plant-1": "FIG",
    "plant-2": "IVY",
    "plant-3": "PAL",
}
REFRESH_RATE = 600
DEBUG_MODE = True

# Color Palette (HSL-adjacent visuals)
COLORS = {
    "BLACK":  0x000000,
    "GREEN":  0x00FF00,
    "YELLOW": 0xFFFF00,
    "RED":    0xFF0000,
    "BROWN":  0x884400,
    "TEXT":   0xFFFFFF,
    "PCT":    0xAAAAAA,
}

# Sprite Data Strings
SPRITE_DATA = [
    # HEALTHY (State 0)
    (
        "0000000000000000" "0000000000000000" "0000000001000000" "0000000111000000"
        "0000001111100000" "0000111001110000" "0001111001111000" "0011101001011100"
        "0111101001011110" "0111111001111110" "0111011001101110" "0011111111111100"
        "0001101001011000" "0000111111110000" "0004444444444000" "0044444444444400"
        "0044444444444400" "0004444444444000" "0000000000000000" "0000000000000000"
    ),
    # THIRSTY (State 1)
    (
        "0000000000000000" "0000000000000000" "0000000000000000" "0000000222200000"
        "0000002200220000" "0000022000022000" "0000220000022200" "0000220000222220"
        "0000220000222220" "0000022000022200" "0000002200002000" "0000000220000000"
        "0000000220000000" "0000000220000000" "0004444444444000" "0044444444444400"
        "0044444444444400" "0004444444444000" "0000000000000000" "0000000000000000"
    ),
    # CRITICAL (State 2)
    (
        "0000000000000000" "0000000000000000" "0000000000000000" "0000000000003000"
        "0000000000033000" "0000000000330000" "0003000000330000" "0003300003300000"
        "0000330033000000" "0000033330000300" "0000003300003300" "0000003300033000"
        "0000003300330000" "0000003333000000" "0004444444444000" "0044444444444400"
        "0044444444444400" "0004444444444000" "0000000000000000" "0000000000000000"
    )
]

class PlantUI:
    """Manages the visual representation of a single plant."""
    SPRITE_W = 16
    SPRITE_H = 20

    def __init__(self, name, feed_id, font, sprite_sheet, palette):
        self.name = name
        self.feed_id = feed_id
        self.group = displayio.Group()
        
        # 1. Sprite TileGrid
        self.tile_grid = displayio.TileGrid(
            sprite_sheet, pixel_shader=palette,
            width=1, height=1,
            tile_width=self.SPRITE_W, tile_height=self.SPRITE_H
        )
        self.tile_grid.y = 6
        self.group.append(self.tile_grid)

        # 2. Percentage Label
        self.pct_label = label.Label(font, text="--%", color=COLORS["PCT"])
        self.pct_label.anchor_point = (0.5, 0.0)
        self.pct_label.anchored_position = (self.SPRITE_W // 2, 0)
        self.group.append(self.pct_label)

        # 3. Name Label
        self.name_label = label.Label(font, text=name, color=COLORS["TEXT"])
        self.name_label.anchor_point = (0.5, 1.0)
        self.name_label.anchored_position = (self.SPRITE_W // 2, 32)
        self.group.append(self.name_label)

    def set_position(self, x):
        self.group.x = x

    def update(self, value):
        """Update text and sprite based on moisture value."""
        self.pct_label.text = f"{value}%"
        
        # Determine State
        if value < 20:
            state = 2 # Critical
        elif value < 50:
            state = 1 # Thirsty
        else:
            state = 0 # Healthy
        
        self.tile_grid[0] = state

class PlantMonitor:
    """Main application orchestrator."""
    def __init__(self):
        gc.collect()
        self.matrixportal = MatrixPortal(bit_depth=2, debug=False)
        self.group = displayio.Group()
        self.matrixportal.display.root_group = self.group

        self.font = self._load_font()
        self.palette = self._create_palette()
        self.sprite_sheet = self._create_sprite_sheet()
        
        self.plants = []
        self._setup_ui()

    def _load_font(self):
        try:
            return bitmap_font.load_font("/fonts/tom-thumb.bdf")
        except:
            return terminalio.FONT

    def _create_palette(self):
        palette = displayio.Palette(5)
        palette[0] = COLORS["BLACK"]
        palette[1] = COLORS["GREEN"]
        palette[2] = COLORS["YELLOW"]
        palette[3] = COLORS["RED"]
        palette[4] = COLORS["BROWN"]
        return palette

    def _create_sprite_sheet(self):
        sheet = displayio.Bitmap(16 * 3, 20, 5)
        for s, data in enumerate(SPRITE_DATA):
            for y in range(20):
                for x in range(16):
                    val = int(data[y * 16 + x])
                    sheet[s * 16 + x, y] = val
        return sheet

    def _setup_ui(self):
        num_plants = len(PLANT_CONFIG)
        plant_feeds = list(PLANT_CONFIG.keys())
        
        # Calculate Layout
        sprite_w = PlantUI.SPRITE_W
        gap = 3
        total_w = (num_plants * sprite_w) + ((num_plants - 1) * gap)
        
        if total_w > 64:
            gap = (64 - (num_plants * sprite_w)) // (num_plants - 1) if num_plants > 1 else 0
            total_w = (num_plants * sprite_w) + ((num_plants - 1) * gap)
        
        margin_left = (64 - total_w) // 2

        for i, feed in enumerate(plant_feeds):
            name = PLANT_CONFIG[feed]
            p_ui = PlantUI(name, feed, self.font, self.sprite_sheet, self.palette)
            p_ui.set_position(margin_left + (i * (sprite_w + gap)))
            
            self.plants.append(p_ui)
            self.group.append(p_ui.group)

    def fetch_data(self):
        """Fetch moisture levels and update UI."""
        for i, plant in enumerate(self.plants):
            try:
                if DEBUG_MODE:
                    test_vals = [85, 42, 12, 60]
                    value = test_vals[i % 4]
                else:
                    data = self.matrixportal.get_io_data(plant.feed_id)
                    value = int(float(data[0]['value'])) if data else 0
                
                print(f"Updating {plant.name}: {value}%")
                plant.update(value)
                
            except Exception as e:
                print(f"Error fetching {plant.feed_id}: {e}")

    def run(self):
        """Main loop."""
        while True:
            self.fetch_data()
            gc.collect() # Regular cleanup
            time.sleep(REFRESH_RATE)

# --- START APP ---
if __name__ == "__main__":
    app = PlantMonitor()
    app.run()