from __future__ import annotations

import argparse
import os
import struct
import subprocess
import sys
from pathlib import Path


EXAMPLE_DIR = Path(__file__).resolve().parent
sys.path.append(str((EXAMPLE_DIR / "../../").resolve()))

ghidra_src = (EXAMPLE_DIR / "../../../../../ghidra_assistant/src").resolve()
if ghidra_src.exists():
    sys.path.append(str(ghidra_src))


EL1_VBAR_ADDR = 0x90000
EL2_VBAR_ADDR = 0x90800
SECURE_STACK_TOP = 0x91800
SECURE_STATE_ADDR = 0x91A00
SECURE_LOG_ADDR = 0x92000
SECURE_MON_ADDR = 0x92C00
TEE_OS_ADDR = 0x93000
EL1_DEBUG_BRIDGE_ADDR = 0x94100
KERNEL_ENTRY_ADDR = 0x94200
KERNEL_SMC_SHIM_ADDR = 0x94400

VBAR_ENTRY_SIZE = 0x80
VBAR_TABLE_SIZE = 0x800
EL1_CURRENT_SPX_SYNC_SLOT = 4
EL2_LOWER_A64_SYNC_SLOT = 8
EL1H_SPSR = 0x3C5

CMD_ECHO_U64 = 3

LOG_EXCEPTION_ID_OFFSET = 0x00
LOG_ELR_OFFSET = 0x08
LOG_SMC_COUNT_OFFSET = 0x10
LOG_APP_CALL_COUNT_OFFSET = 0x18
LOG_CMD_ID_OFFSET = 0x20
LOG_ARG0_OFFSET = 0x28
LOG_ARG1_OFFSET = 0x30
LOG_STATUS_OFFSET = 0x38
LOG_RESULT_OFFSET = 0x40
LOG_KERNEL_PROCESSED_OFFSET = 0x48


def _tool_env() -> dict[str, str]:
    env = dict(os.environ)
    path = env.get("PATH", "")
    if not path:
        env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    return env


def run_cmd(args: list[str]) -> None:
    subprocess.run(args, cwd=EXAMPLE_DIR, check=True, env=_tool_env())


def compile_all() -> dict[str, Path]:
    run_cmd(["make", "-C", "tee", "all"])
    build = EXAMPLE_DIR / "tee" / "build"
    return {
        "secure_mon": build / "secure_mon.bin",
        "tee_os": build / "tee_os.bin",
        "kernel": build / "kernel.bin",
        "kernel_smc": build / "kernel_smc.bin",
    }


def get_runtime():
    import qemu as qemu_env

    return qemu_env


def assemble(ks, source: str, address: int) -> bytes:
    return ks.asm(source, addr=address, as_bytes=True)[0]


def pad_slot(blob: bytes, nop_ins: bytes) -> bytes:
    if len(blob) > VBAR_ENTRY_SIZE:
        raise ValueError(f"Vector slot is too large: {len(blob)} bytes")
    return blob + (nop_ins * ((VBAR_ENTRY_SIZE - len(blob)) // 4))


def build_debugger_slot(cd, ks, slot_addr: int) -> bytes:
    return assemble(
        ks,
        f"""
            ldr x15, DEBUGGER_addr
            br x15
            DEBUGGER_addr: .quad {hex(cd.arch_dbg.debugger_addr)}
        """,
        slot_addr,
    )


def build_el1_brk_slot(cd, ks, slot_addr: int) -> bytes:
    # Shellcode region: EL1 synchronous trap slot used only for BRK.
    # Any EL1 exception in this flow should return directly to the debugger.
    return assemble(
        ks,
        f"""
            ldr x15, DEBUGGER_addr
            br x15

            DEBUGGER_addr: .quad {hex(cd.arch_dbg.debugger_addr)}
        """,
        slot_addr,
    )


def build_el2_smc_slot(cd, ks, slot_addr: int, slot_id: int) -> bytes:
    # Shellcode region: EL2 monitor trap slot for real SMC forwarding.
    # The handler logs the call, forwards to secure_mon, fixes ELR_EL2,
    # and then returns back to the kernel after the SMC instruction.
    return assemble(
        ks,
        f"""
            sub sp, sp, #16
            str x30, [sp]
            mrs x17, ESR_EL2
            lsr x17, x17, #26
            cmp x17, #0x17
            b.ne handle_brk

            ldr x15, LOG_addr
            mov x16, #{slot_id}
            str x16, [x15, #{LOG_EXCEPTION_ID_OFFSET}]
            mrs x16, ELR_EL2
            str x16, [x15, #{LOG_ELR_OFFSET}]
            ldr x16, [x15, #{LOG_SMC_COUNT_OFFSET}]
            add x16, x16, #1
            str x16, [x15, #{LOG_SMC_COUNT_OFFSET}]
            ldr x16, SEC_MON_addr
            blr x16
            mrs x16, ELR_EL2
            add x16, x16, #4
            msr ELR_EL2, x16
            ldr x30, [sp]
            add sp, sp, #16
            eret

        handle_brk:
            ldr x30, [sp]
            add sp, sp, #16
            ldr x15, DEBUGGER_addr
            br x15

            LOG_addr: .quad {hex(SECURE_LOG_ADDR)}
            SEC_MON_addr: .quad {hex(SECURE_MON_ADDR)}
            DEBUGGER_addr: .quad {hex(cd.arch_dbg.debugger_addr)}
        """,
        slot_addr,
    )


def write_blob(cd, address: int, blob: bytes) -> None:
    cd.memwrite_region(address, blob)


def read_u64(cd, address: int) -> int:
    return struct.unpack("<Q", cd.memdump_region(address, 8))[0]


def clear_secure_state(cd) -> None:
    cd.memwrite_region(SECURE_STATE_ADDR, b"\x00" * 0x100)
    cd.memwrite_region(SECURE_LOG_ADDR, b"\x00" * 0x100)


def read_secure_log(cd) -> dict[str, int]:
    return {
        "exception_id": read_u64(cd, SECURE_LOG_ADDR + LOG_EXCEPTION_ID_OFFSET),
        "elr": read_u64(cd, SECURE_LOG_ADDR + LOG_ELR_OFFSET),
        "smc_count": read_u64(cd, SECURE_LOG_ADDR + LOG_SMC_COUNT_OFFSET),
        "app_calls": read_u64(cd, SECURE_LOG_ADDR + LOG_APP_CALL_COUNT_OFFSET),
        "cmd_id": read_u64(cd, SECURE_LOG_ADDR + LOG_CMD_ID_OFFSET),
        "arg0": read_u64(cd, SECURE_LOG_ADDR + LOG_ARG0_OFFSET),
        "arg1": read_u64(cd, SECURE_LOG_ADDR + LOG_ARG1_OFFSET),
        "status": read_u64(cd, SECURE_LOG_ADDR + LOG_STATUS_OFFSET),
        "result": read_u64(cd, SECURE_LOG_ADDR + LOG_RESULT_OFFSET),
        "kernel_processed": read_u64(cd, SECURE_LOG_ADDR + LOG_KERNEL_PROCESSED_OFFSET),
    }


def get_scratch_addr(cd) -> int:
    if hasattr(cd, "ga_stack_location"):
        return cd.ga_stack_location + 0x400
    return cd.arch_dbg.storage_addr + 0x400


def run_scratch_blob(cd, blob: bytes, failure_message: str) -> None:
    scratch_addr = get_scratch_addr(cd)
    original_blob = cd.memdump_region(scratch_addr, len(blob))
    cd.memwrite_region(scratch_addr, blob)
    try:
        cd.restore_stack_and_jump(scratch_addr)
        assert cd.read(4) == b"GiAs", failure_message
    finally:
        cd.memwrite_region(scratch_addr, original_blob)


def find_instruction_addr(cd, blob: bytes, start_addr: int, mnemonic: str) -> int:
    for offset in range(0, len(blob), 4):
        insn = next(cd.arch_dbg.sc.cs.disasm(blob[offset : offset + 4], start_addr + offset))
        if insn.mnemonic == mnemonic:
            return start_addr + offset
    raise RuntimeError(f"Could not find {mnemonic} in kernel blob")


def run_kernel_with_stepper(cd, kernel_start: int, kernel_size: int) -> None:
    from ghidra_assistant.utils.archs.arm64.arm64_exception_stepper import ARM64ExceptionStepper

    scratch_addr = get_scratch_addr(cd)
    kernel_blob = cd.memdump_region(kernel_start, kernel_size)
    original_blob = cd.memdump_region(scratch_addr, len(kernel_blob))
    cd.memwrite_region(scratch_addr, kernel_blob)

    try:
        # Step a scratch copy of the kernel so the exception stepper is exercised
        # without changing the actual secure-call flow that follows.
        stepper = ARM64ExceptionStepper(
            cd,
            scratch_addr,
            emulate_exceptions_as_nop=True,
            debug=True
        )
        while True:
            if stepper.next_instruction().mnemonic == "smc":
                pass
            stepper.step()
    finally:
        cd.memwrite_region(scratch_addr, original_blob)


def enter_el1(cd, ks, entry_addr: int) -> None:
    cd.fetch_special_regs()
    current_el = cd.arch_dbg.state.R_CURRENT_EL.get_exception_level()
    if current_el != 2:
        raise RuntimeError(f"Expected to start from EL2, got EL{current_el}")

    # Shellcode region: EL2 -> EL1 handoff trampoline.
    # It programs the execution context for the secure EL1 payload and then ERET
    # into the bridge that returns control to the debugger.
    transition = assemble(
        ks,
        f"""
            sub sp, sp, #16
            str x15, [sp]
            str x16, [sp, #8]
            ldr x15, HCR_addr
            msr HCR_EL2, x15
            ldr x15, VBAR2_addr
            msr VBAR_EL2, x15
            ldr x15, VBAR_addr
            msr VBAR_EL1, x15
            ldr x15, STACK2_addr
            mov sp, x15
            ldr x15, STACK_addr
            msr SP_EL1, x15
            ldr x15, SPSR_addr
            msr SPSR_EL2, x15
            ldr x15, ENTRY_addr
            msr ELR_EL2, x15
            isb
            ldr x16, [sp, #8]
            ldr x15, [sp]
            add sp, sp, #16
            eret
            HCR_addr: .quad {hex(cd.arch_dbg.state.HCR_EL2 | (1 << 31) | (1 << 19))}
            VBAR2_addr: .quad {hex(EL2_VBAR_ADDR)}
            VBAR_addr: .quad {hex(EL1_VBAR_ADDR)}
            STACK2_addr: .quad {hex(SECURE_STACK_TOP - 0x200)}
            STACK_addr: .quad {hex(SECURE_STACK_TOP)}
            SPSR_addr: .quad {hex(EL1H_SPSR)}
            ENTRY_addr: .quad {hex(entry_addr)}
        """,
        get_scratch_addr(cd),
    )
    run_scratch_blob(cd, transition, "Failed EL2->EL1 transition")


def install_el1_vbar(cd, ks) -> None:
    slot_count = VBAR_TABLE_SIZE // VBAR_ENTRY_SIZE
    default_slot = pad_slot(build_debugger_slot(cd, ks, EL1_VBAR_ADDR), cd.arch_dbg.sc.nop_ins)
    vbar = default_slot * slot_count
    brk_slot = pad_slot(build_el1_brk_slot(cd, ks, EL1_VBAR_ADDR + (EL1_CURRENT_SPX_SYNC_SLOT * VBAR_ENTRY_SIZE)), cd.arch_dbg.sc.nop_ins)
    vbar = vbar[: EL1_CURRENT_SPX_SYNC_SLOT * VBAR_ENTRY_SIZE] + brk_slot + vbar[(EL1_CURRENT_SPX_SYNC_SLOT + 1) * VBAR_ENTRY_SIZE :]
    write_blob(cd, EL1_VBAR_ADDR, vbar)


def install_el2_vbar(cd, ks) -> None:
    slot_count = VBAR_TABLE_SIZE // VBAR_ENTRY_SIZE
    default_slot = pad_slot(build_debugger_slot(cd, ks, EL2_VBAR_ADDR), cd.arch_dbg.sc.nop_ins)
    vbar = default_slot * slot_count
    smc_slot = pad_slot(build_el2_smc_slot(cd, ks, EL2_VBAR_ADDR + (EL2_LOWER_A64_SYNC_SLOT * VBAR_ENTRY_SIZE), EL2_LOWER_A64_SYNC_SLOT), cd.arch_dbg.sc.nop_ins)
    vbar = vbar[: EL2_LOWER_A64_SYNC_SLOT * VBAR_ENTRY_SIZE] + smc_slot + vbar[(EL2_LOWER_A64_SYNC_SLOT + 1) * VBAR_ENTRY_SIZE :]
    write_blob(cd, EL2_VBAR_ADDR, vbar)


def run_debug_flow(use_stepper: bool = False) -> dict[str, int]:
    qemu_env = get_runtime()
    cd = qemu_env.cd
    ks = qemu_env.ks

    artifacts = compile_all()
    kernel_blob = artifacts["kernel"].read_bytes()

    clear_secure_state(cd)
    write_blob(cd, SECURE_MON_ADDR, artifacts["secure_mon"].read_bytes())
    write_blob(cd, TEE_OS_ADDR, artifacts["tee_os"].read_bytes())
    write_blob(cd, KERNEL_ENTRY_ADDR, kernel_blob)
    write_blob(cd, KERNEL_SMC_SHIM_ADDR, artifacts["kernel_smc"].read_bytes())
    write_blob(cd, EL1_DEBUG_BRIDGE_ADDR, cd.arch_dbg.sc.branch_absolute(cd.arch_dbg.debugger_addr))
    install_el1_vbar(cd, ks)
    install_el2_vbar(cd, ks)

    # Enter EL1 and return to debugger before running kernel payload.
    enter_el1(cd, ks, EL1_DEBUG_BRIDGE_ADDR)

    # Functional mode: optionally preview the kernel via the exception stepper,
    # then run the real payload directly so the secure monitor path stays intact.
    if use_stepper:
        run_kernel_with_stepper(cd, KERNEL_ENTRY_ADDR, len(kernel_blob))
    cd.restore_stack_and_jump(KERNEL_ENTRY_ADDR)
    assert cd.read(4) == b"GiAs", "Did not return to debugger"
    cd.fetch_special_regs()

    log = read_secure_log(cd)
    assert log["smc_count"] == 1, f"Expected one SMC, got {log['smc_count']}"
    assert log["app_calls"] == 1, f"Expected one secure monitor forward, got {log['app_calls']}"
    assert log["cmd_id"] == CMD_ECHO_U64, f"Expected cmd {CMD_ECHO_U64}, got {log['cmd_id']}"
    assert log["status"] == 0, f"Expected status 0, got {log['status']}"
    assert log["kernel_processed"] == log["result"] + 1, (
        f"Kernel did not process secure response: kernel_processed={log['kernel_processed']:#x}, "
        f"result={log['result']:#x}"
    )
    return log


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile and run mock TEE C payload flow")
    parser.add_argument("--compile-only", action="store_true", help="Only compile C payloads")
    parser.add_argument("--use-stepper", action="store_true", help="Run the kernel through ARM64ExceptionStepper")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.compile_only:
        artifacts = compile_all()
        print("Compilation complete:")
        for name, path in artifacts.items():
            print(f"  {name}: {path}")
        return

    try:
        log = run_debug_flow(use_stepper=args.use_stepper)
    except FileNotFoundError as exc:
        if str(exc).find("qemu-system-aarch64") >= 0:
            print("qemu-system-aarch64 was not found in PATH.")
            print("Compile still works with: --compile-only")
            raise
        raise

    print("Mock TEE C payload flow complete")
    print(f"  cmd={log['cmd_id']} arg0={log['arg0']:#x} arg1={log['arg1']:#x}")
    print(f"  status={log['status']} result={log['result']:#x}")
    print(f"  kernel_processed={log['kernel_processed']:#x}")


if __name__ == "__main__":
    main()
