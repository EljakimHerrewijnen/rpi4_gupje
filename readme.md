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

Get the usb_send and usb_recv symbols from the built kernel8.elf:
```bash
➜  rpi4_gupje git:(paging_example) ✗ readelf -a prebuild/kernel8.elf | grep uart_puts
    34: 0000000000080204    88 FUNC    GLOBAL DEFAULT    1 uart_puts
➜  rpi4_gupje git:(paging_example) ✗ readelf -a prebuild/kernel8.elf | grep uart_getc
    39: 00000000000801d0    52 FUNC    GLOBAL DEFAULT    1 uart_getc
```

Build gupje. First download an NDK and set it to your environment:
```bash
cd /tmp && wget wget https://dl.google.com/android/repository/android-ndk-r21e-linux-x86_64.zip
unzip android-ndk-r21e-linux-x86_64.zip
export ANDROID_NDK_ROOT=/tmp/android-ndk-r21e
```

Navigate to the gupje source directory and build it:
```bash
cd ../../
make -f devices/rpi4_gupje/Makefile
```

## Usage
You can test this code using ``qemu.py``, which will start qemu and attach the debugger into it. I recommend using vscode for stepping through the python code.

```bash
$ python3 qemu.py
```