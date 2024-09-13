# Gupje RPi4
This code is built on top of [this repository](https://github.com/ethanfaust/rpi4-baremetal-uart.git) and contains code to run the debugger on a raspberry pi 3/4 and in Qemu.

The goal is to have a software(qemu) and hardware(pi4) code platform to test ``Gupje`` on.

## Usage
Clone with --recursive to also clone the RPI4 code:

```bash
git clone --recursive https://github.com/EljakimHerrewijnen/rpi4_gupje
```

You can test this code using ``qemu.py``, which will start qemu and attach the debugger into it.