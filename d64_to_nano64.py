#!/usr/bin/env python3
import sys

# ------------------------------------------------------------
# C64 BASIC token table (expanded)
# ------------------------------------------------------------
TOKENS = {
    0x80: "END",     0x81: "FOR",     0x82: "NEXT",
    0x83: "DATA",    0x84: "INPUT",   0x85: "DIM",
    0x86: "READ",    0x87: "LET",     0x88: "GOTO",
    0x89: "RUN",     0x8A: "IF",      0x8B: "RESTORE",
    0x8C: "GOSUB",   0x8D: "RETURN",  0x8E: "REM",
    0x8F: "STOP",    0x90: "ON",      0x91: "WAIT",
    0x92: "LOAD",    0x93: "SAVE",    0x94: "VERIFY",
    0x95: "DEF",     0x96: "POKE",    0x97: "PRINT",
    0x98: "CONT",    0x99: "LIST",    0x9A: "CLR",
    0x9B: "CMD",     0x9C: "SYS",     0x9D: "OPEN",
    0x9E: "CLOSE",   0x9F: "GET",     0xA0: "NEW",
}

# ------------------------------------------------------------
# PETSCII → ASCII (Nano64-safe)
# ------------------------------------------------------------
def petscii_to_ascii(b):
    if 0x41 <= b <= 0x5A: return chr(b)      # A-Z
    if 0x30 <= b <= 0x39: return chr(b)      # 0-9
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

# ------------------------------------------------------------
# Read ALL PRG files from a D64 image
# ------------------------------------------------------------
def read_all_prg_from_d64(path):
    with open(path, "rb") as f:
        d = f.read()

    prgs = []
    dir_offset = 0x16500  # Track 18 sector 1

    for i in range(8):  # 8 directory sectors
        off = dir_offset + i * 256
        for e in range(8):  # 8 entries per sector
            entry = d[off + e*32 : off + e*32 + 32]
            if entry[2] != 0x82:  # PRG type
                continue
            t, s = entry[3], entry[4]
            name = entry[5:21].decode("ascii", errors="ignore").strip()

            prg = bytearray()
            while t != 0:
                block_off = ((t - 1) * 21 + s) * 256
                block = d[block_off:block_off+256]
                t, s = block[0], block[1]
                prg.extend(block[2:])
            prgs.append((name, bytes(prg)))

    return prgs

# ------------------------------------------------------------
# Decode BASIC PRG
# ------------------------------------------------------------
def decode_basic(prg):
    load_addr = prg[0] | (prg[1] << 8)
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

# ------------------------------------------------------------
# Convert BASIC line to Nano64 BASIC
# ------------------------------------------------------------
def convert_line(ln, bytes_):
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

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------
def main():
    if len(sys.argv) < 3:
        print("Usage: d64_to_nano64.py disk.d64 output.bas")
        return

    prgs = read_all_prg_from_d64(sys.argv[1])

    if not prgs:
        print("No PRG files found.")
        return

    with open(sys.argv[2], "w") as f:
        for name, prg in prgs:
            f.write(f"REM --- {name} ---\n")
            lines = decode_basic(prg)
            for ln, b in lines:
                f.write(convert_line(ln, b) + "\n")
            f.write("\n")

    print("Wrote Nano64 BASIC to", sys.argv[2])

if __name__ == "__main__":
    main()
