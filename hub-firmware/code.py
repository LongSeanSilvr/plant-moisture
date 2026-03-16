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
# Use this to override labels or variants for specific feed keys
PLANT_CONFIG = {
    # Example: "plant-1-moisture": {"name": "FIG", "variant": 1},
}
REFRESH_RATE = 600
ROTATION_INTERVAL = 15  # Seconds between plant rotations

# Display Modes: "NORMAL", "SPRITE_DEMO", "FEED_DEBUG"
DISPLAY_MODE = "NORMAL" 

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
    # VARIANT 1: Standard Broadleaf (Original)
    (
        "0000000000000000"
        "0000000000000000"
        "0000000001000000"
        "0000000111000000"
        "0000001111100000"
        "0000111001110000"
        "0001111001111000"
        "0011101001011100"
        "0111101001011110"
        "0111111001111110"
        "0111011001101110"
        "0011111111111100"
        "0001101001011000"
        "0000111111110000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 2: Cactus
    (
        "0000000000000000"
        "0000000000000000"
        "0000000110000000"
        "0000000110001100"
        "0001100110011100"
        "0001100110011000"
        "0001100110011000"
        "0001111110011000"
        "0000111111111000"
        "0000000111110000"
        "0000000110000000"
        "0000000110000000"
        "0000000110000000"
        "0000000110000000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 3: Fern
    (
        "0000000000000000"
        "0000000011000000"
        "0000000111100000"
        "0000110011001100"
        "0001110111101110"
        "0011110111101111"
        "0011000111100011"
        "0011000111100011"
        "0001100111100110"
        "0000111111111100"
        "0000011111111000"
        "0000001111110000"
        "0000000111100000"
        "0000000111100000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 4: Bonsai Tree
    (
        "0000000000000000"
        "0000000000000000"
        "0000000001000000"
        "0000000011100000"
        "0000001111100000"
        "0000001100100000"
        "0000001110100000"
        "0000011101100000"
        "0000111001100000"
        "0001110011100000"
        "0011110001110000"
        "0111111001111000"
        "0001100001100000"
        "0000110011100000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 5: Bamboo Stalks
    (
        "0000001000001000"
        "0000011000011000"
        "0000011000011000"
        "0000111100111100"
        "0000111100111100"
        "0000011000011000"
        "0000011000011000"
        "0000011000011000"
        "0000111100111100"
        "0000111100111100"
        "0000011000011000"
        "0000011000011000"
        "0000011000011000"
        "0000011000011000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 6: Rosette Succulent
    (
        "0000000000000000"
        "0000000000000000"
        "0000000000000000"
        "0000000000000000"
        "0000000110000000"
        "0000001111000000"
        "0000011111100000"
        "0000111111110000"
        "0001110110111000"
        "0011110110111100"
        "0011111111111100"
        "0001101111011000"
        "0000110000110000"
        "0000011111100000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 7: Trailing Vine
    (
        "0000000000000000"
        "0000000000000000"
        "0000000001000000"
        "0000000111100000"
        "0000001111100000"
        "0000111111000000"
        "0001111110000000"
        "0011111100000000"
        "0111110000000000"
        "0111000000000000"
        "0010000000000000"
        "0000100000000000"
        "0000001000000000"
        "0000000100000000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 8: Dracaena Palm
    (
        "0000000000000000"
        "0000000000000000"
        "0010000000000000"
        "0011000000001000"
        "0001100000011000"
        "0000110000110000"
        "0000011001100000"
        "0000001111000000"
        "0000000110000000"
        "0000000110000000"
        "0000000110000000"
        "0000000110000000"
        "0000000110000000"
        "0000000110000000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 9: Snake Plant
    (
        "0000000000000000"
        "0000000010000000"
        "0000000110000000"
        "0000010110010000"
        "0000110110110000"
        "0001100110110100"
        "0001101110110110"
        "0011101110111110"
        "0011101110111110"
        "0011111110111110"
        "0011111111111110"
        "0001111111111100"
        "0000111111111000"
        "0000011111110000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # VARIANT 10: Monstera
    (
        "0000000000000000"
        "0000000000000000"
        "0000000110000000"
        "0000011111100000"
        "0000110110110000"
        "0001111111111000"
        "0001101111011000"
        "0011111111111100"
        "0011011111101100"
        "0011110110111100"
        "0001111111111000"
        "0000110000110000"
        "0000001111000000"
        "0000000110000000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # THIRSTY
    (
        "0000000000000000"
        "0000000000000000"
        "0000000000000000"
        "0000000222200000"
        "0000002200220000"
        "0000022000022000"
        "0000220000022200"
        "0000220000222220"
        "0000220000222220"
        "0000022000022200"
        "0000002200002000"
        "0000000220000000"
        "0000000220000000"
        "0000000220000000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    ),
    # CRITICAL
    (
        "0000000000000000"
        "0000000000000000"
        "0000000000000000"
        "0000000000003000"
        "0000000000033000"
        "0000000000330000"
        "0003000000330000"
        "0003300003300000"
        "0000330033000000"
        "0000033330000300"
        "0000003300003300"
        "0000003300033000"
        "0000003300330000"
        "0000003333000000"
        "0004444444444000" 
        "0044444444444400" 
        "0044444444444400" 
        "0004444444444000" 
        "0000000000000000"
        "0000000000000000"
    )
]

class PlantUI:
    """Manages the visual representation of a single plant."""
    SPRITE_W = 16
    SPRITE_H = 20

    def __init__(self, name, feed_id, font, sprite_sheet, palette, variant=None):
        self.name = name
        self.feed_id = feed_id
        
        # Determine number of healthy variants (all except last two)
        num_healthy = len(SPRITE_DATA) - 2
        
        # Assign healthy variant
        if variant is not None:
            self.assigned_variant = (variant - 1) % num_healthy
        else:
            # Consistent variant assignment based on feed_id hash
            feed_hash = sum(ord(c) for c in feed_id)
            self.assigned_variant = feed_hash % num_healthy
            
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
        
        # Determine State Indices
        thirsty_idx = len(SPRITE_DATA) - 2
        critical_idx = len(SPRITE_DATA) - 1
        
        # Determine State
        if value < 20:
            state = critical_idx # Critical
        elif value < 50:
            state = thirsty_idx # Thirsty
        else:
            state = self.assigned_variant # Assigned Healthy Variant
        
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
        self._window_start = 0
        self._max_visible = 3
        
        # 1. Discover Feeds
        self.discover_plants()
            
        self._update_display()

    def discover_plants(self):
        """Scan Adafruit IO for all moisture feeds and setup PlantUI objects."""
        print("Waiting for network connection...")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.matrixportal.get_local_time() # Forces connection
                print("Network connected.")
                break
            except Exception as e:
                print(f"Connection attempt {attempt+1}/{max_retries} failed: {e}")
                time.sleep(2)
        
        print("Discovering moisture sensors on Adafruit IO...")
        try:
            io = self.matrixportal.network.io_http
            all_feeds = io.get_feeds()
            print(f"Total feeds found: {len(all_feeds)}")
            
            moisture_feeds = [f for f in all_feeds if f['key'].endswith('-moisture')]
            print(f"Moisture sensors detected: {len(moisture_feeds)}")
            
            for feed in moisture_feeds:
                f_id = feed['key']
                config = PLANT_CONFIG.get(f_id, {})
                default_name = f_id.replace('-moisture', '').upper()
                name = config.get('name', default_name)
                variant = config.get('variant')
                
                print(f" -> Adding {name} ({f_id})")
                p_ui = PlantUI(name, f_id, self.font, self.sprite_sheet, self.palette, variant=variant)
                self.plants.append(p_ui)
                
            if not self.plants:
                print("No live moisture feeds found. Check Adafruit IO.")
                self.plants.append(PlantUI("NONE", "none", self.font, self.sprite_sheet, self.palette))

        except Exception as e:
            print(f"Discovery Error: {e}")
            print("Falling back to hardcoded config...")
            for f_id, config in PLANT_CONFIG.items():
                p_ui = PlantUI(config['name'], f_id, self.font, self.sprite_sheet, self.palette, variant=config.get('variant'))
                self.plants.append(p_ui)

    def _load_font(self):
        try:
            return bitmap_font.load_font("/fonts/tom-thumb.bdf")
        except:
            return terminalio.FONT

    def _create_palette(self):
        palette = displayio.Palette(5)
        # 0: Black, 1: Green, 2: Yellow, 3: Red, 4: Brown
        palette[0] = COLORS["BLACK"]
        palette[1] = COLORS["GREEN"]
        palette[2] = COLORS["YELLOW"]
        palette[3] = COLORS["RED"]
        palette[4] = COLORS["BROWN"]
        return palette

    def _create_sprite_sheet(self):
        num_sprites = len(SPRITE_DATA)
        sheet = displayio.Bitmap(16 * num_sprites, 20, 5)
        for s, data in enumerate(SPRITE_DATA):
            for y in range(20):
                for x in range(16):
                    val = int(data[y * 16 + x])
                    sheet[s * 16 + x, y] = val
        return sheet

    def _update_display(self):
        """Update which plants are visible and their positions."""
        while len(self.group) > 0:
            self.group.pop()
            
        num_plants = len(self.plants)
        visible_count = min(num_plants, self._max_visible)
        
        sprite_w = PlantUI.SPRITE_W
        gap = 3
        total_w = (visible_count * sprite_w) + ((visible_count - 1) * gap)
        
        if total_w > 64:
            gap = (64 - (visible_count * sprite_w)) // (visible_count - 1) if visible_count > 1 else 0
            total_w = (visible_count * sprite_w) + ((visible_count - 1) * gap)
        
        margin_left = (64 - total_w) // 2

        for i in range(visible_count):
            idx = (self._window_start + i) % num_plants
            plant = self.plants[idx]
            x_pos = margin_left + (i * (sprite_w + gap))
            plant.set_position(x_pos)
            self.group.append(plant.group)

    def rotate_window(self):
        """Shift the sliding window by one plant."""
        self._window_start = (self._window_start + 1) % len(self.plants)
        self._update_display()

    def fetch_data(self):
        """Fetch moisture levels and update UI."""
        print(f"Fetching updates for {len(self.plants)} plants...")
        for i, plant in enumerate(self.plants):
            try:
                if DISPLAY_MODE == "SPRITE_DEMO":
                    num_all = len(SPRITE_DATA)
                    sprite_idx = (self._window_start + i) % num_all 
                    plant.pct_label.text = f"S{sprite_idx}"
                    plant.tile_grid[0] = sprite_idx
                elif DISPLAY_MODE == "FEED_DEBUG":
                    test_vals = [85, 42, 12, 65]
                    value = test_vals[i % len(test_vals)]
                    plant.update(value)
                else: # NORMAL mode
                    if plant.feed_id == "none":
                        continue
                    data = self.matrixportal.get_io_data(plant.feed_id)
                    value = int(float(data[0]['value'])) if data else 0
                    print(f" -> {plant.name}: {value}%")
                    plant.update(value)
            except Exception as e:
                print(f"Error updating {plant.feed_id}: {e}")

    def run(self):
        """Main loop."""
        last_rotate = time.monotonic()
        last_fetch = 0.0
        
        while True:
            now = time.monotonic()
            if now - last_fetch >= REFRESH_RATE or last_fetch == 0:
                self.fetch_data()
                last_fetch = now
                gc.collect()

            if now - last_rotate >= ROTATION_INTERVAL:
                if len(self.plants) > self._max_visible:
                    self.rotate_window()
                last_rotate = now
            time.sleep(1)

if __name__ == "__main__":
    app = PlantMonitor()
    app.run()