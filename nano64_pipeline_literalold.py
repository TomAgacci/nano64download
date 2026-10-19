#!/usr/bin/env python3
import sys
import os
import struct
import serial
import time
import json

TOKENS = {
    0x80: "END", 0x81: "FOR", 0x82: "NEXT", 0x83: "DATA",
    0x84: "INPUT", 0x85: "DIM", 0x86: "READ", 0x87: "LET",
    0x88: "GOTO", 0x89: "RUN", 0x8A: "IF", 0x8B: "RESTORE",
    0x8C: "GOSUB", 0x8D: "RETURN", 0x8E: "REM", 0x97: "PRINT",
}

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

# ---------- 1541 sector layout ----------
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

# ---------- D64 directory walker ----------
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
            if file_type & 0x07 != 0x02:  # PRG
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

# ---------- BASIC decode ----------
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

# ---------- literal color mapping ----------
def auto_color_postprocess(basic_lines):
    mapped = []
    for line in basic_lines:
        # Simple literal mapping examples:
        # POKE 1024+N, X  -> PLOT (N%40),(N//40),X
        # POKE 55296+N, C -> PLOT (N%40),(N//40),C (color)
        if "POKE" in line:
            try:
                parts = line.split("POKE")[1].strip()
                addr_expr, val_expr = parts.split(",")
                addr_expr = addr_expr.strip()
                val_expr = val_expr.strip()
                if addr_expr.startswith("1024+"):
                    n = int(addr_expr[5:])
                    x = n % 40
                    y = n // 40
                    mapped.append(f"{line} : PLOT {x},{y},{val_expr}")
                    continue
                if addr_expr.startswith("55296+"):
                    n = int(addr_expr[6:])
                    x = n % 40
                    y = n // 40
                    mapped.append(f"{line} : PLOT {x},{y},{val_expr}")
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

# ---------- BASIC → bytecode → Assets.h ----------
def compile_basic_to_assets(bas_path, assets_path):
    out = []
    OPCODES = {
        'WAVE':  0x0A, 'ENV':   0x07, 'SOUND': 0x06,
        'LFOF':  0x08, 'LFOP':  0x09, 'ARP':   0x0B,
        'SEQ':   0x0C, 'PLAY':  0x0D, 'TRACK': 0x0E,
    }

    with open(bas_path) as f:
        for line in f:
            line = line.strip()
            if not line or not line[0].isdigit():
                continue
            _, rest = line.split(" ", 1)
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

# ---------- upload + HTML integration ----------
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
    with open(os.path.join(out_dir, "program.bas"), "w") as f:
        f.write(bas_text)
    with open(os.path.join(out_dir, "program.json"), "w") as f:
        json.dump({"bytecode": list(bytecode)}, f, indent=2)

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
        # For now, use first PRG; you can add selection later
        name, prg = prgs[0]
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
