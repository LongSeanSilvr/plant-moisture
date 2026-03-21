import re
import os

# Paths
SPRITES_PY = "hub-firmware/sprites.py"
CODE_PY = "hub-firmware/code.py"
PREVIEW_HTML = "hub-firmware/preview.html"

def get_palette_from_code():
    with open(CODE_PY, "r") as f:
        content = f.read()
    # Find the palette initialization line
    match = re.search(r"enumerate\(\[(.*?)\]\)", content)
    if match:
        colors_str = match.group(1)
        colors = [c.strip() for c in colors_str.split(",")]
        return colors
    return None

def get_sprites_from_sprites():
    with open(SPRITES_PY, "r") as f:
        content = f.read()
    
    # Find all content inside parentheses (the sprites)
    sprite_blocks = re.findall(r'\(\s*(.*?)\s*\)', content, re.DOTALL)
    
    sprites = []
    for block in sprite_blocks:
        # Extract all strings in quotes within this block and join them
        parts = re.findall(r'"([0-9]+)"', block)
        sprite_str = "".join(parts)
        if len(sprite_str) == 320:
            sprites.append(sprite_str)
    
    return sprites

def update_preview():
    palette = get_palette_from_code()
    sprites = get_sprites_from_sprites()
    
    if palette is None or not sprites:
        print("Failed to extract palette or sprites.")
        return

    with open(PREVIEW_HTML, "r") as f:
        html = f.read()

    # Update PALETTE in JS
    palette_js = "const PALETTE = [\n            " + ",\n            ".join(palette) + "\n        ];"
    html = re.sub(r"const PALETTE = \[.*?\];", palette_js, html, flags=re.DOTALL)

    # Update SPRITE_DATA in JS
    sprites_js = "const SPRITE_DATA = [\n            \"" + "\",\n            \"".join(sprites) + "\"\n        ];"
    html = re.sub(r"const SPRITE_DATA = \[.*?\];", sprites_js, html, flags=re.DOTALL)

    with open(PREVIEW_HTML, "w") as f:
        f.write(html)
    
    print(f"Successfully updated {PREVIEW_HTML} with {len(sprites)} sprites.")

if __name__ == "__main__":
    update_preview()
