import sys

sys.path.append("../../")

from qemu import *


CODE_CAVE = 0x80000 + 0x12000

SHELLCODE = """
    mov x0, #1
    mov x1, #2
    add x2, x0, x1
    nop
    nop
    nop
"""


def main() -> None:
    shellcode_bin = ks.asm(SHELLCODE, as_bytes=True)[0]
    cd.memwrite_region(CODE_CAVE, shellcode_bin)

    stepper = ARM64Stepper(cd, CODE_CAVE, True)
    stepper.step()
    stepper.step()
    stepper.step()


if __name__ == "__main__":
    main()