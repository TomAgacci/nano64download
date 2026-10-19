#!/usr/bin/env python3
"""
nano64_pipeline_literal.py

Current Nano64 pipeline with:

- BASIC / PRG / D64 input
- PLOT / COLOR / BOX / PRINT
- SPRITE / SPRITEMOVE / SPRITEFRAME / SCROLL
- sprite sheets (2bpp, multicolor, named)
- Z-index / layering (per-sprite)
- VIC-II style state (border/background/scroll)
- collision detection
- JSON output (program.json) for HTML + firmware
"""

import sys
import os
import json

# ------------------------------------------------------------
# Sprite sheet registry (logical names → sheet metadata)
# ------------------------------------------------------------

SPRITE_SHEETS = {
    # Logical name "player" — matches firmware's playerSpriteSheet
    "player": {
        "name": "player",
        "frames": 4,
        "w": 8,
        "h": 8,
        "format": "2bpp_multicolor"
        # Actual bytes live in firmware (PROGMEM) and HTML (JS array)
    }
    # You can add more sheets here (enemy, bullet, etc.)
}

# ------------------------------------------------------------
# BASIC → screen/colors/sprites/VIC parser
# ------------------------------------------------------------

def parse_nano64_basic_to_state(bas_text):
    """
    Parse Nano64 BASIC into:

    - screen[1000]  (40x25 PETSCII/tile codes)
    - colors[1000]  (foreground color per cell)
    - sprites{}     (sprite table with sheet/frame/z)
    - vic{}         (border/background/scrollX/scrollY)
    """
    screen = [32] * 1000
    colors = [1] * 1000

    sprites = {}  # idx → dict
    fg = 1
    bg = 0
    cur_x = 0
    cur_y = 0

    vic = {
        "border": 6,
        "background": 0,
        "scrollX": 0,
        "scrollY": 0
    }

    lines = bas_text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if not line[0].isdigit():
            continue

        # Split line number and command
        try:
            _, cmd = line.split(" ", 1)
        except ValueError:
            continue

        parts = cmd.split()
        if not parts:
            continue

        keyword = parts[0].upper()

        # --------------------------------------------------------
        # COLOR fg,bg
        # --------------------------------------------------------
        if keyword == "COLOR":
            try:
                args = parts[1].split(",")
                fg = int(args[0])
                bg = int(args[1])
                vic["background"] = bg
            except Exception:
                pass

        # --------------------------------------------------------
        # PLOT x,y,c
        # --------------------------------------------------------
        elif keyword == "PLOT":
            try:
                args = parts[1].split(",")
                x = int(args[0])
                y = int(args[1])
                c = int(args[2])
                if 0 <= x < 40 and 0 <= y < 25:
                    idx = y * 40 + x
                    screen[idx] = c
                    colors[idx] = fg
            except Exception:
                pass

        # --------------------------------------------------------
        # BOX x,y,w,h,c
        # --------------------------------------------------------
        elif keyword == "BOX":
            try:
                args = parts[1].split(",")
                x = int(args[0])
                y = int(args[1])
                w = int(args[2])
                h = int(args[3])
                c = int(args[4])
                for yy in range(y, y + h):
                    for xx in range(x, x + w):
                        if 0 <= xx < 40 and 0 <= yy < 25:
                            idx = yy * 40 + xx
                            screen[idx] = c
                            colors[idx] = fg
            except Exception:
                pass

        # --------------------------------------------------------
        # PRINT "text"
        # with cursor, scrolling
        # --------------------------------------------------------
        elif keyword == "PRINT":
            try:
                text = cmd.split("PRINT", 1)[1].strip()
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]

                for ch in text:
                    if ch == '\r':
                        cur_x = 0
                        cur_y += 1
                    else:
                        if 0 <= cur_x < 40 and 0 <= cur_y < 25:
                            idx = cur_y * 40 + cur_x
                            screen[idx] = ord(ch)
                            colors[idx] = fg
                        cur_x += 1
                        if cur_x >= 40:
                            cur_x = 0
                            cur_y += 1

                    # Scroll when reaching bottom
                    if cur_y >= 25:
                        for row in range(1, 25):
                            for col in range(40):
                                src = row * 40 + col
                                dst = (row - 1) * 40 + col
                                screen[dst] = screen[src]
                                colors[dst] = colors[src]
                        for col in range(40):
                            idx = 24 * 40 + col
                            screen[idx] = 32
                            colors[idx] = fg
                        cur_y = 24
            except Exception:
                pass

        # --------------------------------------------------------
        # SPRITE idx,x,y,color[,z[,sheet]]
        # default sheet="player", z=0
        # --------------------------------------------------------
        elif keyword == "SPRITE":
            try:
                args = parts[1].split(",")
                idx = int(args[0])
                x   = int(args[1])
                y   = int(args[2])
                col = int(args[3])
                z   = int(args[4]) if len(args) > 4 else 0
                sheet_name = args[5] if len(args) > 5 else "player"

                if sheet_name not in SPRITE_SHEETS:
                    sheet_name = "player"

                sprites[idx] = {
                    "x": x,
                    "y": y,
                    "w": SPRITE_SHEETS[sheet_name]["w"],
                    "h": SPRITE_SHEETS[sheet_name]["h"],
                    "color": col,
                    "color1": 2,
                    "color2": 3,
                    "frame": 0,
                    "z": z,
                    "sheet": sheet_name,
                    "multicolor": True
                }
            except Exception:
                pass

        # --------------------------------------------------------
        # SPRITEMOVE idx,dx,dy
        # --------------------------------------------------------
        elif keyword == "SPRITEMOVE":
            try:
                args = parts[1].split(",")
                idx = int(args[0])
                dx  = int(args[1])
                dy  = int(args[2])
                if idx in sprites:
                    sprites[idx]["x"] += dx
                    sprites[idx]["y"] += dy
            except Exception:
                pass

        # --------------------------------------------------------
        # SPRITEFRAME idx,frame
        # --------------------------------------------------------
        elif keyword == "SPRITEFRAME":
            try:
                args = parts[1].split(",")
                idx   = int(args[0])
                frame = int(args[1])
                if idx in sprites:
                    sprites[idx]["frame"] = frame
            except Exception:
                pass

        # --------------------------------------------------------
        # SCROLL dx,dy
        # --------------------------------------------------------
        elif keyword == "SCROLL":
            try:
                args = parts[1].split(",")
                dx = int(args[0])
                dy = int(args[1])
                vic["scrollX"] += dx
                vic["scrollY"] += dy
            except Exception:
                pass

        # You can add more BASIC commands here (e.g. TILE, MAP, etc.)

    return screen, colors, sprites, vic

# ------------------------------------------------------------
# Collision detection
# ------------------------------------------------------------

def compute_collisions(sprites):
    """
    Compute sprite collisions as pairs of indices.
    """
    hits = []
    keys = list(sprites.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a_idx = keys[i]
            b_idx = keys[j]
            a = sprites[a_idx]
            b = sprites[b_idx]
            if (a["x"] < b["x"] + b["w"] and
                a["x"] + a["w"] > b["x"] and
                a["y"] < b["y"] + b["h"] and
                a["y"] + a["h"] > b["y"]):
                hits.append([a_idx, b_idx])
    return hits

# ------------------------------------------------------------
# PRG → BASIC (stub; you can replace with real token decoding)
# ------------------------------------------------------------

def prg_to_basic(prg_bytes):
    """
    Minimal stub: convert PRG bytes to BASIC text.
    Replace with real token decoding when you’re ready.
    """
    # For now, just a placeholder BASIC program:
    return "10 COLOR 1,0\n20 PRINT \"PRG LOADED\"\n30 SPRITE 0,10,10,5\n40 SPRITEMOVE 0,5,0\n50 SPRITEFRAME 0,1\n60 SCROLL 1,0\n"

# ------------------------------------------------------------
# D64 → PRG (stub; you can replace with real directory walker)
# ------------------------------------------------------------

def d64_extract_first_prg(path):
    """
    Minimal stub: extract first PRG from D64.
    Replace with real directory walker + sector reader.
    """
    # For now, just return dummy bytes:
    return b"\x01\x08\x97\x22\x00"

# ------------------------------------------------------------
# Bytecode compiler (optional; here we just stub it)
# ------------------------------------------------------------

def basic_to_bytecode(bas_text):
    """
    Stub: compile BASIC to Nano64 bytecode.
    For now, we just return a tiny program that uses sprite opcodes.
    """
    # Example bytecode:
    # 0x12 SPRITE idx,x,y,color
    # 0x13 SPRITEMOVE idx,dx,dy
    # 0x14 SPRITEFRAME idx,frame
    # 0x15 SCROLL dx,dy
    # 0xFF END
    return [
        0x12, 0, 40, 40, 5,   # SPRITE 0,40,40,color=5
        0x13, 0,  2,  0,      # SPRITEMOVE 0,+2,0
        0x14, 0,  1,          # SPRITEFRAME 0,1
        0x15,  1,  0,         # SCROLL +1,0
        0xFF
    ]

# ------------------------------------------------------------
# JSON output builder
# ------------------------------------------------------------

def build_program_json(bas_text):
    """
    Full pipeline:

    BASIC → screen/colors/sprites/vic → collisions → bytecode → JSON
    """
    screen, colors, sprites, vic = parse_nano64_basic_to_state(bas_text)
    collisions = compute_collisions(sprites)
    bytecode = basic_to_bytecode(bas_text)

    # Convert sprite keys to strings for JSON
    sprites_json = {}
    for idx, s in sprites.items():
        sprites_json[str(idx)] = s

    return {
        "bytecode": bytecode,
        "screen": screen,
        "colors": colors,
        "sprites": sprites_json,
        "vic": vic,
        "collisions": collisions,
        "spriteSheets": SPRITE_SHEETS
    }

# ------------------------------------------------------------
# MAIN CLI
# ------------------------------------------------------------

def main():
    if len(sys.argv) < 3:
        print("Usage: nano64_pipeline_literal.py <input.bas|input.prg|input.d64> <output.json>")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2]

    # Load BASIC from various sources
    if inp.lower().endswith(".bas"):
        bas_text = open(inp, "r", encoding="utf-8").read()

    elif inp.lower().endswith(".prg"):
        prg = open(inp, "rb").read()
        bas_text = prg_to_basic(prg)

    elif inp.lower().endswith(".d64"):
        prg = d64_extract_first_prg(inp)
        bas_text = prg_to_basic(prg)

    else:
        print("Unknown input type:", inp)
        sys.exit(1)

    program = build_program_json(bas_text)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(program, f, indent=2)

    print("nano64_pipeline_literal: wrote", out)

if __name__ == "__main__":
    main()
