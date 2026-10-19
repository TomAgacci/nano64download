#!/usr/bin/env python3
import sys

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

def main():
    if len(sys.argv) < 3:
        print("Usage: prg_to_nano64.py program.prg output.bas")
        return

    with open(sys.argv[1], "rb") as f:
        prg = f.read()

    lines = decode_basic(prg)

    with open(sys.argv[2], "w") as f:
        for ln, b in lines:
            f.write(convert_line(ln, b) + "\n")

    print("Wrote Nano64 BASIC to", sys.argv[2])

if __name__ == "__main__":
    main()
