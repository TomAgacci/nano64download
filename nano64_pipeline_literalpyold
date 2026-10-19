#!/usr/bin/env python3
import sys
import os
import serial
import time
import json

TOKENS = {
    0x80: "END", 0x81: "FOR", 0x82: "NEXT", 0x83: "DATA",
    0x84: "INPUT", 0x85: "DIM", 0x86: "READ", 0x87: "LET",
    0x88: "GOTO", 0x89: "RUN", 0x8A: "IF", 0x8B: "RESTORE",
    0x8C: "GOSUB", 0x8D: "RETURN", 0x8E: "REM", 0x97: "PRINT",
}

TRACK_SECTORS = {
    **{t:21 for t in range(1,18)},
    **{t:19 for t in range(18,25)},
    **{t:18 for t in range(25,31)},
    **{t:17 for t in range(31,36)},
}

def track_sector_offset(track, sector):
    if track < 1 or track > 35:
        return 0
    off = 0
    for t in range(1, track):
        off += TRACK_SECTORS[t] * 256
    off += sector * 256
    return off

def petscii_to_ascii(b):
    if 0x41 <= b <= 0x5A: return chr(b)
    if 0x30 <= b <= 0x39: return chr(b)
    if b == 0x20: return " "
    if b == 0x22: return '"'
    if b == 0x3A: return ":"
    if b == 0x3B: return ";"
    if b == 0x3D: return "="
    if b == 0x2C: return ","
    if b == 0x2B: return "+"
    if b == 0x2D: return "-"
    if b == 0x2A: return "*"
    if b == 0x2F: return "/"
    return "?"

def read_all_prg_from_d64(path):
    with open(path, "rb") as f:
        d = f.read()

    prgs = []
    track = 18
    sector = 1

    while track != 0:
        off = track_sector_offset(track, sector)
        block = d[off:off+256]
        next_track = block[0]
        next_sector = block[1]

        for i in range(8):
            e = block[2 + i*32 : 2 + (i+1)*32]
            file_type = e[2]
            if file_type & 0x07 != 0x02:
                continue
            start_t = e[3]
            start_s = e[4]
            name = e[5:21].decode("ascii", errors="ignore").strip()

            prg = bytearray()
            t, s = start_t, start_s
            while t != 0:
                boff = track_sector_offset(t, s)
                b = d[boff:boff+256]
                t, s = b[0], b[1]
                prg.extend(b[2:])
            prgs.append((name, bytes(prg)))

        track, sector = next_track, next_sector

    return prgs

def decode_basic_prg(prg):
    code = prg[2:]
    pos = 0
    lines = []
    while True:
        if pos + 4 > len(code): break
        nxt = code[pos] | (code[pos+1] << 8)
        if nxt == 0: break
        ln = code[pos+2] | (code[pos+3] << 8)
        pos += 4
        bytes_ = []
        while pos < len(code) and code[pos] != 0:
            bytes_.append(code[pos])
            pos += 1
        pos += 1
        lines.append((ln, bytes_))
    return lines

def convert_line_to_basic(ln, bytes_):
    out = [str(ln), " "]
    i = 0
    while i < len(bytes_):
        b = bytes_[i]
        if b >= 0x80:
            out.append(TOKENS.get(b, "REM"))
            out.append(" ")
            i += 1
        else:
            out.append(petscii_to_ascii(b))
            i += 1
    return "".join(out).rstrip()

def auto_color_postprocess(basic_lines):
    mapped = []
    for line in basic_lines:
        if "POKE" in line:
            try:
                parts = line.split("POKE")[1].strip()
                addr_expr, val_expr = parts.split(",")
                addr = int(addr_expr.strip())
                val = int(val_expr.strip())

                if 1024 <= addr < 1024+1000:
                    n = addr - 1024
                    x = n % 40
                    y = n // 40
                    mapped.append(f"{line} : PLOT {x},{y},{val}")
                    continue

                if 55296 <= addr < 55296+1000:
                    n = addr - 55296
                    x = n % 40
                    y = n // 40
                    mapped.append(f"{line} : PLOT {x},{y},{val}")
                    continue

                if addr == 53280:
                    mapped.append(f"{line} : COLOR {val},0")
                    continue

                if addr == 53281:
                    mapped.append(f"{line} : COLOR 0,{val}")
                    continue

                if 53287 <= addr <= 53294:
                    sprite_idx = addr - 53287
                    mapped.append(f"{line} : REM SPRITE{sprite_idx}_COLOR {val}")
                    continue

            except Exception:
                mapped.append(line)
                continue
        else:
            mapped.append(line)
    return mapped

def prg_to_basic(prg_bytes):
    lines = decode_basic_prg(prg_bytes)
    basic = [convert_line_to_basic(ln, b) for ln, b in lines]
    basic = auto_color_postprocess(basic)
    return "\n".join(basic) + "\n"

def compile_basic_to_assets(bas_path, assets_path):
    out = []
    OPCODES = {
        'WAVE':  0x0A, 'ENV':   0x07, 'SOUND': 0x06,
        'LFOF':  0x08, 'LFOP':  0x09, 'ARP':   0x0B,
        'SEQ':   0x0C, 'PLAY':  0x0D, 'TRACK': 0x0E,
        'SPRITE': 0x12, 'SPRITEMOVE': 0x13,
        'SPRITEFRAME': 0x14, 'SCROLL': 0x15,
    }

    with open(bas_path) as f:
        for line in f:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue
            try:
                _, rest = line.split(" ", 1)
            except ValueError:
                continue
            rest = rest.strip()
            cmd = rest.split(" ")[0].upper()
            args = rest[len(cmd):].strip()
            parts = [p.strip() for p in args.split(",")] if args else []

            if cmd not in OPCODES:
                continue
            out.append(OPCODES[cmd])

            if cmd in ('WAVE','PLAY'):
                out.append(int(parts[0]))
            elif cmd == 'ENV':
                out.append(int(parts[0]))
                out.extend(int(a) for a in parts[1:5])
            elif cmd == 'SOUND':
                out.append(int(parts[0]))
                out.append(int(parts[1]))
                out.append(int(parts[2]))
                out.append(int(parts[3]))
            elif cmd in ('LFOF','LFOP'):
                out.append(int(parts[0]))
                om = int(parts[1])
                out.append(om & 0xFF)
                out.append((om >> 8) & 0xFF)
                out.append(int(parts[2]))
            elif cmd == 'ARP':
                out.append(int(parts[0]))
                out.append(int(parts[1]))
                out.append(int(parts[2]))
            elif cmd == 'SEQ':
                v = int(parts[0])
                pairs = parts[1:]
                count = len(pairs)//2
                out.append(v)
                out.append(count)
                for i in range(count):
                    out.append(int(pairs[2*i]))
                    out.append(int(pairs[2*i+1]))
            elif cmd == 'TRACK':
                out.append(int(parts[0]))
                out.append(int(parts[1]))
                out.append(int(parts[2]))
                out.append(int(parts[3]))
                out.append(int(parts[4]))
            elif cmd == 'SPRITE':
                out.append(int(parts[0]))
                out.append(int(parts[1]))
                out.append(int(parts[2]))
                out.append(int(parts[3]))
            elif cmd == 'SPRITEMOVE':
                out.append(int(parts[0]))
                out.append(int(parts[1]))
                out.append(int(parts[2]))
            elif cmd == 'SPRITEFRAME':
                out.append(int(parts[0]))
                out.append(int(parts[1]))
            elif cmd == 'SCROLL':
                out.append(int(parts[0]))
                out.append(int(parts[1]))

    out.append(0xFF)

    with open(assets_path, "w") as f:
        f.write("#pragma once\n#include <Arduino.h>\n")
        f.write("const uint8_t programBytecode[] PROGMEM = {\n")
        for i,b in enumerate(out):
            end = "," if i < len(out)-1 else ""
            f.write(f"  0x{b:02X}{end}\n")
        f.write("};\n")
        f.write(f"const uint16_t programLength = {len(out)};\n")

    return bytes(out)

def parse_nano64_basic_to_screen(bas_text):
    screen = [32]*1000
    colors = [1]*1000
    sprites = {}
    fg = 1
    bg = 0
    cur_x = 0
    cur_y = 0
    vic = {"border": 6, "background": 0, "scrollX": 0, "scrollY": 0}

    lines = bas_text.splitlines()

    for line in lines:
        line = line.strip()
        if not line or not line[0].isdigit():
            continue

        try:
            _, cmd = line.split(" ", 1)
        except ValueError:
            continue

        parts = cmd.split()

        if parts[0].upper() == "COLOR":
            try:
                args = parts[1].split(",")
                fg = int(args[0]); bg = int(args[1])
                vic["background"] = bg
            except:
                pass

        elif parts[0].upper() == "PLOT":
            try:
                args = parts[1].split(",")
                x = int(args[0]); y = int(args[1]); c = int(args[2])
                if 0 <= x < 40 and 0 <= y < 25:
                    idx = y*40 + x
                    screen[idx] = c
                    colors[idx] = fg
            except:
                pass

        elif parts[0].upper() == "BOX":
            try:
                args = parts[1].split(",")
                x = int(args[0]); y = int(args[1])
                w = int(args[2]); h = int(args[3])
                c = int(args[4])
                for yy in range(y, y+h):
                    for xx in range(x, x+w):
                        if 0 <= xx < 40 and 0 <= yy < 25:
                            idx = yy*40 + xx
                            screen[idx] = c
                            colors[idx] = fg
            except:
                pass

        elif parts[0].upper() == "PRINT":
            try:
                text = cmd.split("PRINT",1)[1].strip()
                if text.startswith('"') and text.endswith('"'):
                    text = text[1:-1]
                for ch in text:
                    if ch == '\r':
                        cur_x = 0
                        cur_y += 1
                    else:
                        if 0 <= cur_x < 40 and 0 <= cur_y < 25:
                            idx = cur_y*40 + cur_x
                            screen[idx] = ord(ch)
                            colors[idx] = fg
                        cur_x += 1
                        if cur_x >= 40:
                            cur_x = 0
                            cur_y += 1
                    if cur_y >= 25:
                        for row in range(1,25):
                            for col in range(40):
                                src = row*40 + col
                                dst = (row-1)*40 + col
                                screen[dst] = screen[src]
                                colors[dst] = colors[src]
                        for col in range(40):
                            idx = 24*40 + col
                            screen[idx] = 32
                            colors[idx] = fg
                        cur_y = 24
            except:
                pass

        elif parts[0].upper() == "SPRITE":
            try:
                args = parts[1].split(",")
                idx = int(args[0])
                x   = int(args[1])
                y   = int(args[2])
                col = int(args[3])
                sprites[idx] = {"x":x, "y":y, "w":8, "h":8, "color":col, "frame":0}
            except:
                pass

        elif parts[0].upper() == "SPRITEMOVE":
            try:
                args = parts[1].split(",")
                idx = int(args[0])
                dx  = int(args[1])
                dy  = int(args[2])
                if idx in sprites:
                    sprites[idx]["x"] += dx
                    sprites[idx]["y"] += dy
            except:
                pass

        elif parts[0].upper() == "SPRITEFRAME":
            try:
                args = parts[1].split(",")
                idx = int(args[0])
                frame = int(args[1])
                if idx in sprites:
                    sprites[idx]["frame"] = frame
            except:
                pass

        elif parts[0].upper() == "SCROLL":
            try:
                args = parts[1].split(",")
                dx = int(args[0])
                dy = int(args[1])
                vic["scrollX"] += dx
                vic["scrollY"] += dy
            except:
                pass

    return screen, colors, sprites, vic

def check_collisions(sprites):
    hits = []
    keys = list(sprites.keys())
    for i in range(len(keys)):
        for j in range(i+1, len(keys)):
            a = sprites[keys[i]]
            b = sprites[keys[j]]
            if (a["x"] < b["x"] + b["w"] and
                a["x"] + a["w"] > b["x"] and
                a["y"] < b["y"] + b["h"] and
                a["y"] + a["h"] > b["y"]):
                hits.append((keys[i], keys[j]))
    return hits

def upload_bytecode_to_nano(port_name, baud, bytecode):
    port = serial.Serial(port_name, baud, timeout=1)
    time.sleep(2)
    port.write(b":NEW\n")
    port.write(f":BIN {len(bytecode)}\n".encode())
    port.write(bytecode)
    port.flush()
    time.sleep(0.1)
    port.write(b":RUN\n")

def write_html_simulator_assets(bas_text, bytecode, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    screen, colors, sprites, vic = parse_nano64_basic_to_screen(bas_text)
    hits = check_collisions(sprites)

    with open(os.path.join(out_dir, "program.bas"), "w") as f:
        f.write(bas_text)

    with open(os.path.join(out_dir, "program.json"), "w") as f:
        json.dump({
            "bytecode": list(bytecode),
            "screen": screen,
            "colors": colors,
            "sprites": sprites,
            "vic": vic,
            "collisions": hits
        }, f, indent=2)

def choose_prg(prgs):
    print("PRG files found in D64:")
    for i, (name, _) in enumerate(prgs):
        print(f"  [{i}] {name}")
    while True:
        try:
            idx = int(input("Select PRG index: "))
            if 0 <= idx < len(prgs):
                return prgs[idx]
        except ValueError:
            pass
        print("Invalid selection, try again.")

def main():
    if len(sys.argv) < 5:
        print("Usage: nano64_pipeline_literal.py <input> <COM> <baud> <assets_dir>")
        print("input: .bas, .prg, or .d64")
        return

    inp = sys.argv[1]
    com = sys.argv[2]
    baud = int(sys.argv[3])
    assets_dir = sys.argv[4]

    if inp.lower().endswith(".bas") or inp.lower().endswith(".zcb"):
        bas_text = open(inp).read()
    elif inp.lower().endswith(".prg"):
        prg = open(inp, "rb").read()
        bas_text = prg_to_basic(prg)
    elif inp.lower().endswith(".d64"):
        prgs = read_all_prg_from_d64(inp)
        if not prgs:
            print("No PRG files found in D64.")
            return
        name, prg = choose_prg(prgs)
        print("Using PRG:", name)
        bas_text = prg_to_basic(prg)
    else:
        print("Unknown input type:", inp)
        return

    bas_path = os.path.join(assets_dir, "program.bas")
    assets_path = os.path.join(assets_dir, "Assets.h")
    os.makedirs(assets_dir, exist_ok=True)
    with open(bas_path, "w") as f:
        f.write(bas_text)

    bytecode = compile_basic_to_assets(bas_path, assets_path)
    upload_bytecode_to_nano(com, baud, bytecode)
    write_html_simulator_assets(bas_text, bytecode, assets_dir)

    print("Done. Assets.h, program.bas, program.json generated; bytecode uploaded.")

if __name__ == "__main__":
    main()
