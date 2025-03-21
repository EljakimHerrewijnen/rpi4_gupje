import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))
from qemu import *

if TYPE_CHECKING:
    from ghidra_assistant.utils.debugger.debugger_archs.ga_arm64 import GA_arm64_debugger
    from ghidra_assistant.utils.archs.arm64.arm64_processor_state import ARM64_Concrete_State

    cd.arch_dbg = GA_arm64_debugger(0, 0, 0)
    cd.arch_dbg.state = ARM64_Concrete_State()

from ghidra_assistant.utils.archs.arm64.misc.sctlr_el1 import SCTLR_EL1

# https://gist.github.com/leiradel/67059c4aceea8fa564a5bc33b505f887

BASE = 0x0
RAM_SIZE = 1 * GB

new_sctrl_el1 = SCTLR_EL1(cd.arch_dbg.state.SCTLR_EL1)
new_sctrl_el1.mmu = 1



# And write them back
cd.arch_dbg.state.sctlr_el1 = new_sctrl_el1.value


pass
