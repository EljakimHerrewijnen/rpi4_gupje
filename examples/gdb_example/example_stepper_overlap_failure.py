import sys

sys.path.append("../../")

from qemu import *


CODE_CAVE = 0x80000 + 0x14000

SHELLCODE = """
loop:
    cmp x0, x0
    b.eq loop
    nop
    nop
"""


def main() -> None:
    shellcode_bin = ks.asm(SHELLCODE, as_bytes=True)[0]
    cd.memwrite_region(CODE_CAVE, shellcode_bin)

    stepper = ARM64Stepper(cd, CODE_CAVE, True)

    # First step advances onto the backward branch.
    stepper.step()

    # Second step reproduces the known overlap bug and is expected to raise.
    stepper.step()


if __name__ == "__main__":
    main()