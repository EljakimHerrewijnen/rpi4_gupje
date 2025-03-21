import serial, time
from typing import cast
import subprocess
from keystone import *
from ghidra_assistant.concrete_device import ConcreteDevice
from ghidra_assistant.utils.debugger.debugger_archs.ga_arm64 import GA_arm64_debugger
from qiling.const import *
from ghidra_assistant.utils.utils import *
from ghidra_assistant.utils.archs.arm64.arm64_stepper import ARM64Stepper

ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)

# qemu = subprocess.run(['make', 'qemu_debugger'], shell=True) # Will run qemu
qemu = subprocess.Popen("qemu-system-aarch64 -smp 4 -M raspi3b -kernel rpi4-baremetal-uart/kernel8.img -serial pty -display none".split(" "),  stdout=subprocess.PIPE, universal_newlines=True) # Will run qemu

device = ""
while True:
    line = qemu.stdout.readline()
    if "redirected" in line:
        device = line.split(" ")
        for d in device:
            if "pts" in d:
                device = d
        break
ser = serial.Serial(device, timeout=.001)
ser.write(b"a")
data = b""
while True:
    data += ser.read_all()
    if b"SEND DEBUGGER" in data:
        break
    
# UART_SEND = data.decode().split("\n")[0].strip().split(": ")[1]
# UART_RECV = data.decode().split("\n")[1].strip().split(": ")[1]

DEBUGGER_PATH = "../../bin/rpi4/debugger.bin"
debugger = open(DEBUGGER_PATH, "rb").read()

# Test shellcode
shellcode = """
    ret
"""

# debugger = ks.asm(shellcode, as_bytes=True)[0]
debugger = debugger + ((0x2000 - len(debugger)) * b"\xcc")
assert ser.write(debugger) == 0x2000, "Failed to write the debugger"


def recv_uart_data(timeout=100, length=0):
    '''
    Read data until timeout (in ms) is reached and  no more data is received
    '''
    dat = b""
    t1 = time.time()
    while True:
        if length > 0 and len(dat) == length:
            return dat # Do not receive more
        d = ser.read(1)
        if len(d) == 0:
            if time.time() - t1 > timeout / 1000:
                break
            t1 = time.time() # Reset the timer
        else:
            t1 = time.time()
            dat += d
    return dat       

assert recv_uart_data(length=4) == b"JUMP", "Could not jump in debugger"
assert recv_uart_data(length=4) == b"GiAs", "Could not jump in debugger"

class RaspberryPi4():
    def __init__(self, serial_device) -> None:
        self.ser = serial_device
        # self.read = ser.read
        # self.write = ser.write
        
    def read(self, length):
        remaining = length
        d = b""
        # Download byte by byte
        while remaining > 0:
            d2 = self.ser.read_all()
            d += d2
            remaining -= len(d2)
        # self.ser.
        # self.ser.flush()
        assert len(d) == length, f"Failed to read {length} bytes, got {len(d)} bytes"
        return d
    
    def write(self, data):
        self.ser.write(data)
    
    def setup_concrete_device(self, concrete_device : ConcreteDevice):
        #Setup architecture
        concrete_device.arch = QL_ARCH.ARM64
        concrete_device.ga_debugger_location = 0x81000  # TODO, not used yet
        concrete_device.ga_vbar_location = 0x81000 + 0x1000
        concrete_device.ga_storage_location = 0x85000
        concrete_device.ga_stack_location = 0x83000
        
        concrete_device.arch_dbg = GA_arm64_debugger(concrete_device.ga_vbar_location, concrete_device.ga_debugger_location, concrete_device.ga_storage_location)
        concrete_device.arch_dbg.read = self.read
        concrete_device.arch_dbg.write = self.write
        

        #Overwrite all calls to make the concrete target function properly
        concrete_device.copy_functions()
        
        return concrete_device

pi4 = RaspberryPi4(ser)
cd = ConcreteDevice(None, False)
cd = pi4.setup_concrete_device(cd)

cast(GA_arm64_debugger, cd.arch_dbg) # type hinting

cd.memdump_region(0x80000, 0x100)
cd.memdump_region(0x80000, 0x2000) # TODO fix big chunks
cd.memwrite_region(0x10000, b"\xee" * 0x10)

CODE_CAVE = 0x80000 + 0x10000

SHELLCODE = """
    mov x0, 0x10000
    NOP
    NOP
    mov x1, 0x10
    cmp x0, x1
    bne 0x84000
    ret
"""
cd.memwrite_region(CODE_CAVE, ks.asm(SHELLCODE, as_bytes=True)[0])

# cd.restore_stack_and_jump(cd.arch_dbg.debugger_addr)
# cd.read(4) == b"GiAs"


stepper = ARM64Stepper(cd, CODE_CAVE, False)
stepper.run(stepper.pc)
pass