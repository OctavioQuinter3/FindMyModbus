# FindMyModbus

Modbus RTU/TCP device scanner built with Python + CustomTkinter.

## Features

- RTU scan via RS-485 (auto-baud, slave IDs 1-247)
- TCP scan (unit IDs 1-247)
- Function codes: Coils (01), Discrete Inputs (02), Holding Registers (03), Input Registers (04)
- Persistent connection mode
- Auto-detect COM ports
- Export CSV / JSON
- Portable .exe for Windows

## Recommended hardware

USB-to-RS-485 converter (CH340 + MAX485 + protection)

### Wiring

`
USB-485 dongle                Bus RS-485
-----------------             ------------------
  A (D+) ---------------------- A --- slave
  B (D-) ---------------------- B --- slave
  GND   ---------------------- GND
`

- Twisted-pair shielded cable
- 120 Ohm termination at bus ends
- Max distance: ~1200 m @ 9600 baud

## Quick start

Download the latest release from GitHub:
https://github.com/OctavioQuinter3/FindMyModbus/releases/tag/v1.0.0

Extract the `.zip` and run `FindMyModbus.exe`

## From source

`
pip install -r requirements.txt
python main.py
`

## Usage

1. Tab RTU -> select COM port, baudrate -> Connect
2. Tab TCP -> enter host:port -> Test TCP
3. Set slave range, function codes, registers/slave
4. Start Scan -> results populate live
5. Export CSV or JSON

## Build .exe

`
.\build_exe.ps1
`

## Requirements

Python 3.10+ | customtkinter | pymodbus | pyserial

## Disclaimer

This software is provided "as is", without warranty of any kind.
We are not responsible for any damage or data loss.
Use at your own risk.

