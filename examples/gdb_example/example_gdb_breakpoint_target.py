import argparse
import sys

sys.path.append("../../")

from qemu import cd

from ghidra_assistant.utils.debugger.gdb_rsp import AArch64ConcreteGDBTarget, GDBRemoteServer
from ghidra_assistant.utils.utils import info


CODE_CAVE = 0x80000 + 0x16000

SHELLCODE = """
start:
    mov x0, #0
    mov x1, #3
loop:
    add x0, x0, #1
    cmp x0, x1
    b.lt loop
    b start
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start the Pi 4 GDB bridge with a small looping ARM64 payload for breakpoint testing."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address for the GDB server")
    parser.add_argument("--port", type=int, default=9001, help="Bind port for the GDB server")
    parser.add_argument(
        "--entry",
        type=lambda value: int(value, 0),
        default=CODE_CAVE,
        help="Initial PC to expose to GDB before the target has reported a real stop address",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    shellcode = cd.arch_dbg.ks.asm(SHELLCODE, as_bytes=True)[0]
    cd.memwrite_region(CODE_CAVE, shellcode)

    target = AArch64ConcreteGDBTarget(cd, start_pc=args.entry)
    server = GDBRemoteServer(target)

    info(f"Loaded breakpoint target at {CODE_CAVE:#x}")
    info(f"Loop body is at {CODE_CAVE + 8:#x}")
    info(f"Using configured initial PC {args.entry:#x}")
    info(
        "In GDB: target remote {}:{}; break *{}; continue; continue".format(
            args.host,
            args.port,
            hex(CODE_CAVE + 8),
        )
    )
    server.serve_forever(args.host, args.port)


if __name__ == "__main__":
    main()