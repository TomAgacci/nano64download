Licensed under MIT License

# Nano64 — C64-style BASIC Machine on Arduino Nano

```
███╗   ██╗ █████╗ ███╗   ██╗ ██████╗  ██████╗ ██╗  ██╗
████╗  ██║██╔══██╗████╗  ██║██╔═══██╗██╔════╝ ██║  ██║
██╔██╗ ██║███████║██╔██╗ ██║██║   ██║███████╗ ███████║
██║╚██╗██║██╔══██║██║╚██╗██║██║   ██║██╔═══██╗╚════██║
██║ ╚████║██║  ██║██║ ╚████║╚██████╔╝╚██████╔╝     ██║
╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝      ╚═╝
   C64-like BASIC Machine · Arduino Nano Edition
```

github.com/TomAgacci/basicmachinenano64color
Color Update


Nano64 is a self-contained Commodore-64-inspired BASIC computer running on an
**Arduino Nano** (ATmega328P). It features:

| Feature | Details |
|---|---|
| BASIC interpreter | 200-line program store, A-Z variables, GOSUB/FOR/NEXT |
| Display | SSD1306 128×64 OLED — 16×8 text console + pixel graphics |
| Sound | 3-voice PWM (square/triangle/saw/noise), ADSR envelopes |
| Storage | SerialDisk — load/save programs over USB from host PC |
| Pattern editor | Full-screen 8×8 sprite/tile editor (PATTERN command) |
| Browser sim | `web/nano64_test.html` — runs the BASIC VM in your browser |
| D64 pipeline | Python tools to pack programs into C64 disk images |

---

## Repository Layout

```
nano64/
├── src/                    Arduino sketch (open nano64.ino in Arduino IDE)
│   ├── nano64.ino          Main sketch — setup(), loop(), ISR
│   ├── Assets.h            Character ROM, colour palette, tile set (PROGMEM)
│   ├── BasicVM.h / .cpp    BASIC interpreter (recursive-descent parser)
│   ├── Video.h / .cpp      SSD1306 I2C driver + framebuffer
│   ├── PulseEngine.h/.cpp  3-voice PWM audio (Timer1/Timer2)
│   ├── SerialDisk.h / .cpp Serial virtual disk protocol
│   └── PatternEditor.h/.cpp 8×8 sprite/pattern editor
│
├── tools/                  Python 3 host-side pipeline
│   ├── convert_bas.py      Tokenise / detokenise BASIC programs
│   ├── d64_extract.py      Extract files from .d64 disk images
│   ├── prg_to_basic.py     Convert raw PRG → readable BASIC text
│   ├── capture_from_vice.py Capture output from VICE C64 emulator
│   └── build_assets.py     Full asset pipeline: BAS→PRG→D64→C header
│
├── web/
│   └── nano64_test.html    Self-contained browser BASIC simulator
│
├── assets/
│   ├── programs/           Example BASIC source files (.bas)
│   │   ├── hello.bas
│   │   ├── demo.bas
│   │   ├── starfield.bas
│   │   ├── fizbuzz.bas
│   │   ├── music.bas
│   │   ├── plasma.bas
│   │   ├── maze.bas
│   │   └── sieve.bas
│   └── (nano64.d64 generated here by build_assets.py)
│
└── README.md               This file
```

---

## Hardware Required

| Component | Notes |
|---|---|
| Arduino Nano (ATmega328P) | 5 V, 16 MHz. Old or new bootloader both work. |
| SSD1306 128×64 OLED | I2C — SDA→A4, SCL→A5, VCC→3.3 V or 5 V, GND→GND |
| Speaker / buzzer | Between D9 and GND (voice 0). Add RC filter for clarity. |
| USB cable | For Serial REPL + SerialDisk host link |
| (Optional) 3× RC filter | One per voice (D9/D10/D3) for cleaner audio |

### Wiring Diagram

```
Arduino Nano           SSD1306 OLED
────────────           ────────────
A4  (SDA)  ──────────  SDA
A5  (SCL)  ──────────  SCL
3V3        ──────────  VCC
GND        ──────────  GND

D9  ──[1kΩ]──[100nF]── SPEAKER + ── GND
D10 ──[1kΩ]──[100nF]── (voice 1, optional)
D3  ──[1kΩ]──[100nF]── (voice 2, optional)
```

---

## Building & Uploading (Arduino IDE)

1. **Install Arduino IDE 2.x** from https://arduino.cc
2. Open `src/nano64.ino` — the IDE will import all `.cpp`/`.h` files in `src/`.
3. Select board: **Arduino Nano** → Processor: **ATmega328P (Old Bootloader)**
   (or "ATmega328P" if you have a newer clone).
4. Select the correct COM/tty port.
5. Click **Upload** (Ctrl+U).
6. Open **Serial Monitor** at **115200 baud**. You should see:

```
NANO64 BASIC V1.0
64 BASIC LINES FREE

READY.
```

> **No extra libraries needed.** The firmware uses only the built-in `Wire`
> library for I2C.

---

## BASIC Language Reference

### Statements

| Statement | Syntax | Description |
|---|---|---|
| LET | `LET A=expr` or `A=expr` | Assign variable (A–Z, integer) |
| PRINT | `PRINT expr[;expr][,expr]` | Print to screen; `;` = no newline |
| INPUT | `INPUT [prompt;] var` | Read a number from serial |
| IF/THEN | `IF cond THEN stmt` | Conditional execution |
| GOTO | `GOTO linenum` | Unconditional branch |
| GOSUB/RETURN | `GOSUB linenum` / `RETURN` | Subroutine call |
| FOR/NEXT | `FOR V=from TO to [STEP s]` | Counting loop |
| REM | `REM comment` | Comment |
| END / STOP | `END` | Stop execution |
| CLS | `CLS` | Clear screen |
| COLOR | `COLOR fg,bg` | Set text colours (0–15) |
| PLOT | `PLOT x,y,c` | Set pixel (c=0 clear, c≠0 set) |
| LINE | `LINE x0,y0,x1,y1,c` | Draw a line |
| SND | `SND voice,note,ms` | Play MIDI note (voice 0–2) |
| SOUND | `SOUND voice,freq,ms[,wave]` | Play raw frequency |
| POKE | `POKE addr,val` | Write byte to memory address |
| WAIT | `WAIT ms` | Pause execution (milliseconds) |
| PATTERN | `PATTERN` | Open sprite/tile editor |
| LIST | `LIST` | List the program |
| RUN | `RUN` | Run the stored program |
| NEW | `NEW` | Clear program and variables |
| LOAD | `LOAD "name"` | Load program via SerialDisk |
| SAVE | `SAVE "name"` | Save program via SerialDisk |

### Functions

| Function | Returns |
|---|---|
| `RND(n)` | Random integer 0 to n-1 |
| `ABS(n)` | Absolute value |
| `INT(n)` | Integer part (truncate) |
| `PEEK(addr)` | Byte at memory address |
| `LEN(s$)` | String length |
| `ASC(s$)` | ASCII code of first character |
| `VAL(s$)` | String to integer |

### Operators

`+` `-` `*` `/` `MOD` `AND` `OR` `NOT` `=` `<>` `<` `>` `<=` `>=`

### Colour Codes

| Code | Colour | Code | Colour |
|---|---|---|---|
| 0 | Black | 8 | Orange |
| 1 | White | 9 | Brown |
| 2 | Red | 10 | Light Red |
| 3 | Cyan | 11 | Dark Grey |
| 4 | Purple | 12 | Mid Grey |
| 5 | Green | 13 | Light Green |
| 6 | Blue | 14 | Light Blue |
| 7 | Yellow | 15 | Light Grey |

---

## Example Programs

### Hello World
```basic
10 CLS
20 PRINT "HELLO FROM NANO64!"
30 PRINT "READY."
```

### Pixel Graphics
```basic
10 CLS
20 FOR I=4 TO 60 STEP 4
30   LINE 4,I,I,60,1
40   LINE 123,I,127-I,4,1
50 NEXT I
```

### 3-Voice Chord
```basic
10 SOUND 0,262,500,0
20 SOUND 1,330,500,0
30 SOUND 2,392,500,0
```

---

## SerialDisk Workflow (LOAD / SAVE over USB)

The SerialDisk system lets you transfer programs between your PC and the Nano64
over the same USB/Serial connection used for the REPL.

### Loading a program onto the Nano64

```bash
# Step 1: tokenise your BASIC text file
python tools/convert_bas.py encode assets/programs/hello.bas /tmp/hello.prg

# Step 2: stream it to the device (use your serial port)
python - <<'EOF'
import serial, struct, time

PORT = '/dev/ttyUSB0'   # Windows: 'COM3'
BAUD = 115200

payload = open('/tmp/hello.prg','rb').read()
crc = 0
for b in payload:
    crc ^= b
    for _ in range(8):
        crc = (crc << 1) ^ 0x07 if crc & 0x80 else crc << 1
crc &= 0xFF

pkt = bytes([0xA5, 0x02]) + struct.pack('<H', len(payload)) + bytes([crc]) + payload
s   = serial.Serial(PORT, BAUD, timeout=3)
time.sleep(2)      # let Arduino reset
s.write(pkt)
ack = s.read(1)
print('ACK' if ack == b'\x06' else f'NAK/timeout: {ack!r}')
s.close()
EOF

# Step 3: on the Nano64 REPL, type:
# LOAD "HELLO"
# RUN
```

### Saving a program from the Nano64

```
SAVE "MYPROG"
```

The device will emit a framed packet over Serial that the host can capture.

---

## D64 Disk Image Workflow

### Extract files from a .d64 image

```bash
# List the directory
python tools/d64_extract.py myimage.d64 --list

# Extract all PRG files and convert to BASIC text
python tools/d64_extract.py myimage.d64 --out extracted/ --bas

# Extract a single file
python tools/d64_extract.py myimage.d64 --file "HELLO" --out extracted/
```

### Convert PRG → BASIC text

```bash
python tools/prg_to_basic.py extracted/HELLO.prg
# writes extracted/HELLO.bas
```

### Build the full asset pipeline (BAS → PRG → D64 → C header)

```bash
python tools/build_assets.py
# Output:
#   assets/nano64.d64          ← disk image with all programs
#   assets/assets_generated.h  ← PROGMEM C header for embedding in firmware
```

To also capture screen dumps via VICE:

```bash
# Start VICE: x64 -remotemonitor -remotemonitoraddress 127.0.0.1:6510
python tools/build_assets.py --vice
```

---

## Browser HTML Simulator

Open `web/nano64_test.html` in any modern browser — **no server required**.

Features of the simulator:
- Faithful 128×64 OLED rendering (4× scale, phosphor-green pixels on black)
- BASIC REPL: type numbered lines to build programs, or direct commands
- 7 built-in example programs (click to load & run)
- Load your own `.bas` file from disk
- Export current program as `.bas`
- Live variable watch (A–Z) and PC/line counter
- Pixel PLOT, LINE, CLS, FOR/NEXT, GOTO, GOSUB, IF/THEN all work

> The browser VM does **not** simulate audio (Web Audio not wired in this
> build). SND/SOUND statements are silently ignored so programs still run.

---

## PatternEditor

Type `PATTERN` in the REPL or include it in a BASIC program to enter the
full-screen 8×8 sprite/tile editor.

| Key | Action |
|---|---|
| W / A / S / D | Move cursor |
| Space | Toggle pixel on/off |
| N | Next tile (0–15) |
| P | Previous tile |
| C | Clear current tile |
| X | Copy tile to clipboard |
| V | Paste clipboard into current tile |
| ESC | Close editor and return to BASIC |

After editing, tiles are held in RAM. Use `PatEdit.printToSerial()` in your
sketch to dump them as a C array for permanent storage.

---

## Modifying & Extending

### Adding new BASIC keywords

1. Add a new `T_*` token in `BasicVM.h`.
2. Add the keyword string to `KEYWORDS[]` in `BasicVM.cpp`.
3. Add a `_matchKW(p,"KEYWORD")` branch in `_execStmt()`.
4. Implement `_doKEYWORD(p)`.

### Swapping the display

Replace `Disp.begin()` / `Disp.flip()` / `Disp.setPixel()` calls in
`Video.cpp` with calls to any SPI or I2C display library. The rest of the
firmware is display-agnostic.

### Expanding memory

The ATmega328P has 2 KB SRAM. To get more program space:
- Reduce `VM_PROG_LINES` and `VM_LINE_MAX` in `BasicVM.h`
- Move large tables to PROGMEM with `PROGMEM` + `pgm_read_*`
- Consider an Arduino Mega or an STM32 Blue Pill as a drop-in upgrade

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Blank OLED | Check SDA/SCL wiring; confirm I2C address is 0x3C (scan with I2C scanner sketch) |
| No sound | Confirm D9 is connected to speaker; check Timer1 ISR is enabled (`TIMSK1 |= _BV(TOIE1)`) |
| `?SYNTAX ERROR` | Check line number and statement spelling |
| Upload fails | Select correct board/bootloader; try both "Old Bootloader" variants |
| Serial garbage | Make sure baud rate is set to 115200 in Serial Monitor |
| D64 extract error | Verify file size is exactly 174848 bytes (standard 35-track D64) |

---

## License

MIT License — free to use, modify, and distribute. Attribution appreciated.

---

*Nano64 is an original creative project and is not affiliated with or endorsed
by Commodore, MOS Technology, or any rights holders of the original Commodore 64.*
