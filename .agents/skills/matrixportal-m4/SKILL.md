---
name: matrixportal-m4
description: Specialized knowledge for CircuitPython on Adafruit MatrixPortal M4 boards, including sprite design systems, deployment workflows, and displayio patterns.
---

# MatrixPortal M4 CircuitPython Skill

This skill provides essential knowledge and patterns for developing plant moisture hub firmware on the Adafruit MatrixPortal M4.

## Hardware Overview
- **MCU**: SAMD51 (Cortex M4)
- **Display**: 64x32 RGB LED Matrix
- **Connectivity**: ESP32 for Wi-Fi (handled by `adafruit_matrixportal.network`)

## Core Concepts

### Graphics and Display
- **Library**: `adafruit_displayio_matrix` or `adafruit_matrixportal.matrix`.
- **Bit Depth**: Use `bit_depth=3` in the `Matrix` constructor for accurate color rendering, especially for brown (`0x884400`).
- **Brightness**: Currently set to `0.5` in `code.py`. Adjust as needed for ambient light or power constraints.
- **Palette Management**: Use a 16-color or 8-color palette. Note that `displayio.Bitmap` requires a `value_count` that matches the palette size (e.g., `value_count=8` for a 3-bit palette).

### Sprite Design System
- **Size**: 16x20 pixels per sprite.
- **Data Format**: `SPRITE_DATA` is a list of strings, each 320 characters long (0-7 indices).
- **Palette Indices**:
  - `0`: BLACK (0x000000) - Background
  - `1`: EMERALD GREEN (0x00A000) - Healthy leaves
  - `2`: YELLOW (0xFFFF00) - Thirsty leaves
  - `3`: RED (0xFF0000) - Critical leaves
  - `4`: BROWN (0x884400) - Terracotta pot
  - `5`: FOREST GREEN (0x103000) - Shading
  - `6`: POT SHADOW (0x5D2200) - Pot shading (2-pixel sides, full shadow base)
  - `7`: MOSS HIGHLIGHT (0x306000) - Interior highlights

### Configuration
- **File**: `/plants.json` on the board's ROOT directory.
- **Structure**: A list of objects with `key` (AIO feed), `name` (display label), and `variant` (sprite index).

### Sprite Preview
- **Tool**: `hub-firmware/preview.html` allows for offline verification of sprite appearance and palette colors.
- **Regeneration**: The preview file contains hardcoded data for portability. **Always update and regenerate the preview when making changes to sprite appearance or palette colors.**
- **Automation**: Use `python3 hub-firmware/update_preview.py` to automatically sync `sprites.py` and `code.py` data into `preview.html`.

## Deployment Workflow
1. **Local Development**: Edit files in the repository.
2. **Push to Board**: Copy files to `/Volumes/CIRCUITPY`.
   - > [!IMPORTANT]
   - > **Hardware Verification**: Both the physical sensors (QT Py/Seeed) and the physical hub (MatrixPortal M4) mount at the same `/Volumes/CIRCUITPY` location on macOS. Both types of hardware use a `code.py` and `settings.toml` (or `secrets.json`).
   - > **Action**: Prior to pushing, verify that the hardware currently mounted matches the intended target for the code being pushed. Check for board-specific files or use `boot_out.txt` to identify the board.
3. **Verification**: The board will auto-reload when `code.py` or its dependencies change.
4. **Secrets**: Sensitive data (Wi-Fi, AIO keys) should be in `secrets.json` or `settings.toml` on the board (not in the repo).

## Best Practices
- **Memory Management**: Periodically call `gc.collect()` particularly after UI builds or network requests.
- **Error Handling**: Wrap network requests (`aio_client.receive_data`) in try/except blocks to prevent main loop crashes.
- **Sprite Demo**: Set `DISPLAY_MODE = "SPRITE_DEMO"` in `code.py` to loop through all healthy sprite variants for testing.
