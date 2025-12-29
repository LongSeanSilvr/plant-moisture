import time
import board
import terminalio
import displayio
import math
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_bitmap_font import bitmap_font

# --- CONFIGURATION ---
PLANT_CONFIG = {
    "plant-1": "FIG",
    "plant-2": "IVY",
    "plant-3": "PAL",
    # "plant-4": "JADE", 
}

plant_feeds = list(PLANT_CONFIG.keys())

REFRESH_RATE = 600

# --- COLOR PALETTE ---
COLOR_RED    = 0x880000 
COLOR_YELLOW = 0x888800
COLOR_GREEN  = 0x004400
COLOR_BLACK  = 0x000000
COLOR_TEXT   = 0xFFFFFF
COLOR_PCT    = 0x888888 

# --- VISUAL TWEAKS ---
# We build from the bottom up:
TEXT_AREA_HEIGHT = 8   # Bottom area for Name (Uses TerminalIO)
TEXT_BUFFER      = 1   # Gap between Name and Bar
PCT_AREA_HEIGHT  = 6   # Height for the Tiny Font

# --- LOAD FONTS ---
# Attempt to load the tiny font. Fallback to terminalio if missing.
try:
    small_font = bitmap_font.load_font("/fonts/tom-thumb.bdf")
except Exception as e:
    print("WARNING: Custom font not found. Using terminalio.")
    small_font = terminalio.FONT

# --- SETUP MATRIX ---
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=False)
group = displayio.Group()
matrixportal.display.root_group = group

# --- DYNAMIC LAYOUT ENGINE ---
num_plants = len(PLANT_CONFIG)
screen_w = 64
screen_h = 32

if num_plants <= 4:
    rows = 1
    cols = num_plants
else:
    rows = 2
    cols = math.ceil(num_plants / 2)

cell_h = screen_h // rows

# Calculate max bar height 
max_bar_h = cell_h - TEXT_AREA_HEIGHT - TEXT_BUFFER - PCT_AREA_HEIGHT
if max_bar_h < 1: max_bar_h = 1 

tile_rects = []
name_labels = []
pct_labels = []

# --- BUILD THE GRID ---
for i in range(num_plants):
    row_pos = i // cols
    col_pos = i % cols
    
    # 1. Geometry Calculation
    x_start = int((col_pos * screen_w) / cols)
    x_end   = int(((col_pos + 1) * screen_w) / cols)
    actual_cell_w = x_end - x_start
    cell_y = row_pos * cell_h
    
    center_x = x_start + (actual_cell_w / 2)

    # 2. Create the Bar (Rect)
    # Start it at the bottom of the valid bar zone
    # Note: With TomThumb, we don't need extra padding at top
    bar_bottom_y = cell_y + PCT_AREA_HEIGHT + max_bar_h
    
    rect_w = actual_cell_w - 1
    if col_pos == cols - 1: rect_w = actual_cell_w

    bar = Rect(x_start, bar_bottom_y - 1, rect_w, 1, fill=COLOR_BLACK)
    tile_rects.append(bar)
    group.append(bar)
    
    # 3. Create the Name Label (Bottom - Large Font)
    name = PLANT_CONFIG[plant_feeds[i]]
    text_name = label.Label(terminalio.FONT, text=name, color=COLOR_TEXT)
    text_name.anchor_point = (0.5, 0.5)
    text_name.anchored_position = (center_x, cell_y + cell_h - (TEXT_AREA_HEIGHT / 2))
    name_labels.append(text_name)
    group.append(text_name)

    # 4. Create the Percentage Label (Floating - Tiny Font)
    text_pct = label.Label(small_font, text="0%", color=COLOR_PCT)
    text_pct.anchor_point = (0.5, 1.0) # Anchor bottom-center
    
    # Initial position: Just above the bar bottom
    # Tom Thumb has almost no bottom padding, so we sit it directly on the bar (offset 0)
    text_pct.anchored_position = (center_x, bar_bottom_y)
    pct_labels.append(text_pct)
    group.append(text_pct)

# --- HELPER FUNCTIONS ---
def get_color(moisture_val):
    if moisture_val < 20: return COLOR_RED
    elif moisture_val < 50: return COLOR_YELLOW
    return COLOR_GREEN

def update_display():
    print("Updating Dashboard...")
    
    for i, feed in enumerate(plant_feeds):
        try:
            data = matrixportal.get_io_data(feed)
            
            if data and len(data) > 0:
                value = int(float(data[0]['value']))
            else:
                value = 0
            
            print(f"{PLANT_CONFIG[feed]}: {value}%")
            
            # --- CALCULATE GEOMETRY ---
            current_bar_h = int((value / 100) * max_bar_h)
            if current_bar_h < 1: current_bar_h = 1
            if current_bar_h > max_bar_h: current_bar_h = max_bar_h
            
            # Positions
            row_pos = i // cols
            col_pos = i % cols
            
            x_start = int((col_pos * screen_w) / cols)
            x_end   = int(((col_pos + 1) * screen_w) / cols)
            actual_cell_w = x_end - x_start
            rect_w = actual_cell_w - 1
            if col_pos == cols - 1: rect_w = actual_cell_w

            cell_y = row_pos * cell_h
            bar_bottom_y = cell_y + PCT_AREA_HEIGHT + max_bar_h
            new_y = bar_bottom_y - current_bar_h
            
            # --- 1. UPDATE BAR ---
            old_bar = tile_rects[i]
            if old_bar in group:
                bar_idx = group.index(old_bar)
                group.remove(old_bar)
            else: bar_idx = 0
            
            new_bar = Rect(x_start, new_y, rect_w, current_bar_h, fill=get_color(value))
            group.insert(bar_idx, new_bar)
            tile_rects[i] = new_bar

            # --- 2. UPDATE PERCENTAGE LABEL ---
            pct_labels[i].text = f"{value}%"
            
            center_x = x_start + (actual_cell_w / 2)
            
            # Anchor directly to the top of the bar. 
            # Tom Thumb is extremely tight, so new_y (top of bar) is perfect.
            pct_labels[i].anchored_position = (center_x, new_y)

        except Exception as e:
            print(f"Error fetching {feed}: {e}")
            pass 

while True:
    update_display()
    time.sleep(REFRESH_RATE)