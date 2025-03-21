from qemu import *

if TYPE_CHECKING:
    from ghidra_assistant.utils.debugger.debugger_archs.ga_arm64 import GA_arm64_debugger
    from ghidra_assistant.utils.archs.arm64.arm64_processor_state import ARM64_Concrete_State

    cd.arch_dbg = GA_arm64_debugger(0, 0, 0)
    cd.arch_dbg.state = ARM64_Concrete_State()

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