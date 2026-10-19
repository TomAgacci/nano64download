#!/usr/bin/env python3
import sys
import struct

# Very small C64 BASIC token map (extend as needed)
TOKENS = {
    0x80: "END",
    0x81: "FOR",
    0x82: "NEXT",
    0x83: "DATA",
    0x84: "INPUT",
    0x85: "DIM",
    0x86: "READ",
    0x87: "LET",
    0x88: "GOTO",
    0x89: "RUN",
    0x8A: "IF",
    0x8B: "RESTORE",
    0x8C: "GOSUB",
    0x8D: "RETURN",
    0x8E: "REM",
    0x99: "PRINT",
    0x9E: "SYS",
}

def read_prg_from_d64(d64_path, file_index=0):
    with open(d64_path, "rb") as f:
        data = f.read()

    # Very naive: assume first directory entry is our PRG
    # Directory starts at track 18, sector 1 → offset 0x16500 in standard 35-track D64
    dir_offset = 0x16500
    entries = []
    for i in range(8):  # 8 entries per sector
        e = data[dir_offset + i*32 : dir_offset + (i+1)*32]
        file_type = e[2] & 0x07
        if file_type == 0:  # DEL / empty
            continue
        start_track = e[3]
        start_sector = e[4]
        name = e[5:21].decode("petscii", errors="ignore").rstrip()
        entries.append((name, start_track, start_sector))

    if not entries:
        raise RuntimeError("No files found in directory")

    name, t, s = entries[file_index]
    print("Using file:", name, "at", t, s)

    # Follow track/sector chain
    prg = bytearray()
    while t != 0:
        offset = ((t - 1) * 21 + s) * 256
        block = data[offset:offset+256]
        next_t = block[0]
        next_s = block[1]
        prg.extend(block[2:])
        t, s = next_t, next_s

    return bytes(prg)

def decode_basic(prg):
    # First two bytes: load address (usually 0x01 0x08)
    load_addr = prg[0] | (prg[1] << 8)
    code = prg[2:]

    pos = 0
    lines = []
    while True:
        if pos + 4 > len(code):
            break
        next_link = code[pos] | (code[pos+1] << 8)
        if next_link == 0:
            break
        line_no = code[pos+2] | (code[pos+3] << 8)
        pos += 4
        line_bytes = []
        while pos < len(code) and code[pos] != 0:
            line_bytes.append(code[pos])
            pos += 1
        pos += 1  # skip 0
        lines.append((line_no, line_bytes))
    return lines

def petscii_to_ascii(b):
    # Very rough mapping for BASIC text
    if 0x41 <= b <= 0x5A:
        return chr(b)  # uppercase
    if 0x30 <= b <= 0x39:
        return chr(b)
    if b == 0x20:
        return " "
    if b == 0x22:
        return '"'
    if b == 0x2C:
        return ","
    if b == 0x3A:
        return ":"
    if b == 0x3B:
        return ";"
    if b == 0x3D:
        return "="
    return "?"

def line_bytes_to_zcbasic(line_no, bytes_):
    out = []
    i = 0
    out.append(str(line_no) + " ")
    while i < len(bytes_):
        b = bytes_[i]
        if b >= 0x80:
            # token
            kw = TOKENS.get(b, None)
            if kw is None:
                out.append("REM[UNK]")
            else:
                out.append(kw)
            out.append(" ")
            i += 1
        else:
            # plain char
            out.append(petscii_to_ascii(b))
            i += 1
    return "".join(out).rstrip()

def main():
    if len(sys.argv) < 3:
        print("Usage: d64_to_zcbasic.py disk.d64 output.zcb")
        sys.exit(1)

    d64_path = sys.argv[1]
    out_path = sys.argv[2]

    prg = read_prg_from_d64(d64_path, file_index=0)
    lines = decode_basic(prg)

    with open(out_path, "w", encoding="utf-8") as f:
        for ln, b in lines:
            zc_line = line_bytes_to_zcbasic(ln, b)
            f.write(zc_line + "\n")

    print("Wrote ZeroCircle BASIC to", out_path)

if __name__ == "__main__":
    main()
