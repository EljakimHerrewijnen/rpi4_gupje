# Gupje RPi4
This code is built on top of [this repository](https://github.com/ethanfaust/rpi4-baremetal-uart.git) and contains code to run ``Gupje`` on a raspberry pi 3/4 and in Qemu.

The goal is to have a software(qemu) and hardware(pi4) code platform to test ``Gupje`` on.

## Setup
Install ``qemu`` and setup a python venv:
```bash
$ sudo apt install qemu-system-arm
$ python3 -m venv venv/
$ source venv/bin/activate
4 pip install -r requirements.txt
```

Build the raspberry pi baremetal code:

```bash
$ cd rpi4-baremetal-uart
$ make
```

## Usage
You can test this code using ``qemu.py``, which will start qemu and attach the debugger into it. I recommend using vscode for stepping through the python code.

```bash
$ python3 qemu.py
```