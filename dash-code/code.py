import time
import board
import terminalio
import displayio
import math
import gc
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# --- CONFIGURATION ---
PLANT_CONFIG = {
    "plant-1": "FIG",
    "plant-2": "IVY",
    "plant-3": "PAL",
    # "plant-4": "JADE", 
}
REFRESH_RATE = 600
DEBUG_MODE = True # Set to True to cycle mock data for testing UI

# --- COLOR PALETTE ---
COLOR_BLACK   = 0x000000 # 0
COLOR_GREEN   = 0x00FF00 # 1
COLOR_YELLOW  = 0xFFFF00 # 2
COLOR_RED     = 0xFF0000 # 3
COLOR_BROWN   = 0x884400 # 4
COLOR_POT     = COLOR_BROWN
COLOR_TEXT    = 0xFFFFFF
COLOR_PCT     = 0xAAAAAA

# --- PIXEL ART DATA (16x20) ---
# 0: Black, 1: Green, 2: Yellow, 3: Red, 4: Brown
SPRITE_DATA = [
    # HEALTHY (State 0) - Green Leaf in Brown Pot
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
    # THIRSTY (State 1) - Wilted Seedling in Brown Pot
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
    # CRITICAL (State 2) - Red Branch in Brown Pot
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

def create_sprite_sheet():
    sheet = displayio.Bitmap(16 * 3, 20, 5)
    for s in range(3):
        data = SPRITE_DATA[s]
        for y in range(20):
            for x in range(16):
                val = int(data[y * 16 + x])
                sheet[s * 16 + x, y] = val
    return sheet

# --- SETUP MATRIX ---
gc.collect()
try:
    matrixportal = MatrixPortal(bit_depth=2, debug=False)
except Exception:
    print("Hardware Error")
    raise

group = displayio.Group()
matrixportal.display.root_group = group

# --- LOAD FONTS ---
try:
    small_font = bitmap_font.load_font("/fonts/tom-thumb.bdf")
except:
    small_font = terminalio.FONT

# --- UI STATE ---
num_plants = len(PLANT_CONFIG)
plant_feeds = list(PLANT_CONFIG.keys())
sprite_sheet = create_sprite_sheet()
palette = displayio.Palette(5)
palette[0] = COLOR_BLACK
palette[1] = COLOR_GREEN
palette[2] = COLOR_YELLOW
palette[3] = COLOR_RED
palette[4] = COLOR_BROWN

tile_grids = []
name_labels = []
pct_labels = []

# --- HORIZONTAL LAYOUT ENGINE ---
sprite_w = 16
gap = 3 
total_width_needed = (num_plants * sprite_w) + ((num_plants - 1) * gap)

if total_width_needed > 64:
    gap = (64 - (num_plants * sprite_w)) // (num_plants - 1) if num_plants > 1 else 0
    total_width_needed = (num_plants * sprite_w) + ((num_plants - 1) * gap)

margin_left = (64 - total_width_needed) // 2

for i in range(num_plants):
    x_start = margin_left + (i * (sprite_w + gap))
    x_center = x_start + 8
    
    # 1. Sprite
    tg = displayio.TileGrid(sprite_sheet, pixel_shader=palette,
                            width=1, height=1,
                            tile_width=16, tile_height=20)
    tg.x = x_start
    tg.y = 6 
    tile_grids.append(tg)
    group.append(tg)
    
    # 2. % Label
    text_pct = label.Label(small_font, text="--%", color=COLOR_PCT)
    text_pct.anchor_point = (0.5, 0.0)
    text_pct.anchored_position = (x_center, 0)
    pct_labels.append(text_pct)
    group.append(text_pct)
    
    # 3. Name Label
    name = PLANT_CONFIG[plant_feeds[i]]
    text_name = label.Label(small_font, text=name, color=COLOR_TEXT)
    text_name.anchor_point = (0.5, 1.0)
    text_name.anchored_position = (x_center, 32)
    name_labels.append(text_name)
    group.append(text_name)

def update_display():
    for i, feed in enumerate(plant_feeds):
        try:
            if DEBUG_MODE:
                test_vals = [100, 40, 10, 80]
                value = test_vals[i % 4]
            else:
                data = matrixportal.get_io_data(feed)
                value = int(float(data[0]['value'])) if data else 0
            
            print(f"{PLANT_CONFIG[feed]}: {value}%")
            
            # Update % Text
            pct_labels[i].text = f"{value}%"
            
            # Determine State
            state = 0 # Healthy
            if value < 20:
                state = 2 # Critical
            elif value < 50:
                state = 1 # Thirsty
            
            # Update Sprite
            tile_grids[i][0] = state
            
        except Exception as e:
            print(f"Error updating {feed}: {e}")

while True:
    update_display()
    time.sleep(REFRESH_RATE)