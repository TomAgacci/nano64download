#!/usr/bin/env python3
import sys
import subprocess
import serial
import time

def compile_basic(path):
    """Run zc_basic_compiler.py and capture bytecode array."""
    out = subprocess.check_output(
        [sys.executable, "zc_basic_compiler.py", path]
    ).decode()

    bytecode = []
    for line in out.splitlines():
        if "0x" in line:
            parts = line.replace(",", "").split()
            for p in parts:
                if p.startswith("0x"):
                    bytecode.append(int(p, 16))
    return bytes(bytecode)

def send_to_nano(port_name, baud, bytecode):
    """Send bytecode to Nano64 using SerialDisk protocol."""
    port = serial.Serial(port_name, baud, timeout=1)
    time.sleep(2)

    print("Sending :NEW")
    port.write(b":NEW\n")

    print("Sending :BIN", len(bytecode))
    port.write(f":BIN {len(bytecode)}\n".encode())

    print("Streaming bytecode...")
    port.write(bytecode)
    port.flush()
    time.sleep(0.1)

    print("Sending :RUN")
    port.write(b":RUN\n")

    print("Done.")

def main():
    if len(sys.argv) < 4:
        print("Usage: zc_disk.py COM5 program.bas 115200")
        return

    com = sys.argv[1]
    bas = sys.argv[2]
    baud = int(sys.argv[3])

    print("Compiling BASIC:", bas)
    bytecode = compile_basic(bas)

    print("Sending to Nano64:", com)
    send_to_nano(com, baud, bytecode)

if __name__ == "__main__":
    main()
