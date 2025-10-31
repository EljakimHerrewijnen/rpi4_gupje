import sys
sys.path.append("../../") # To find qemu module

from qemu import *

if TYPE_CHECKING:
    from ghidra_assistant.utils.debugger.debugger_archs.ga_arm64 import GA_arm64_debugger
    from ghidra_assistant.utils.archs.arm64.arm64_processor_state import ARM64_Concrete_State

    cd.arch_dbg = GA_arm64_debugger(0, 0, 0)
    cd.arch_dbg.state = ARM64_Concrete_State()


CODE_CAVE = 0x80000 + 0x10000

SHELLCODE = """
    mov x0, 0x10000
    mov x7, #0x77

    mov x1, #5
    mov x2, #5
    cmp x1, x2
    b.eq equal_path
    mov x3, #0xBAD
    b after_eq
equal_path:
    mov x3, #0xACE
after_eq:

    mov x5, #1
    neg x5, x5
    mov x6, #1
    cmp x5, x6
    b.lt signed_lt
    mov x7, #0
    b after_signed
signed_lt:
    mov x7, #7
after_signed:

    mov x8, #0xFFFF
    movk x8, #0xFFFF, lsl #16
    movk x8, #0xFFFF, lsl #32
    movk x8, #0xFFFF, lsl #48
    adds xzr, x8, #1
    b.hs carry_set
    mov x9, #0
    b after_carry
carry_set:
    mov x9, #1
after_carry:

    mov x10, #0
    cbz x10, was_zero
    mov x11, #0
    b after_cbz
was_zero:
    mov x11, #1
after_cbz:

    mov x12, #10
    tbz x12, #1, bit1_zero
    mov x13, #0x11
    b after_tbz
bit1_zero:
    mov x13, #0x22
after_tbz:

    cmp x3, #0
    csel x14, x3, x0, ne

    ccmp x7, #7, #2, eq
    b.ne ccmp_ne
    mov x15, #0x55
    b after_ccmp
ccmp_ne:
    mov x15, #0x66
after_ccmp:

    nop
    nop
"""
shellcode_bin = ks.asm(SHELLCODE, as_bytes=True)[0]
cd.memwrite_region(CODE_CAVE, shellcode_bin)

# cd.restore_stack_and_jump(cd.arch_dbg.debugger_addr)
# cd.read(4) == b"GiAs"

cd.arch_dbg.state.NZCV = 0b0  # Set N and V flags for testing
stepper = ARM64Stepper(cd, CODE_CAVE, True)
stepper.run(stepper.pc, CODE_CAVE + len(shellcode_bin) - 4)
pass