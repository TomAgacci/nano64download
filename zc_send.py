#!/usr/bin/env python3
import sys
import serial
import time

def send_packet(port, packet):
    port.write(packet)
    port.flush()
    time.sleep(0.05)

def main():
    if len(sys.argv) < 4:
        print("Usage: zc_send.py COM5 program.zcb 115200")
        sys.exit(1)

    com = sys.argv[1]
    bas_path = sys.argv[2]
    baud = int(sys.argv[3])

    # Compile BASIC → bytecode using your compiler
    import subprocess
    bytecode = subprocess.check_output(
        [sys.executable, "zc_basic_compiler.py", bas_path]
    ).decode()

    # Extract the bytecode array from the compiler output
    lines = bytecode.splitlines()
    arr = []
    for line in lines:
        if "0x" in line:
            parts = line.strip().replace(",", "").split()
            for p in parts:
                if p.startswith("0x"):
                    arr.append(int(p, 16))

    packet = bytes(arr)

    print("Opening serial:", com)
    port = serial.Serial(com, baud, timeout=1)
    time.sleep(2)

    print("Sending :NEW")
    port.write(b":NEW\n")

    print("Sending :BIN", len(packet))
    port.write(f":BIN {len(packet)}\n".encode())

    print("Streaming bytecode...")
    send_packet(port, packet)

    print("Sending :RUN")
    port.write(b":RUN\n")

    print("Done.")

if __name__ == "__main__":
    main()
