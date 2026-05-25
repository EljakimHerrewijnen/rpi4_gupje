import argparse
import sys

sys.path.append("../../")

from qemu import cd

from ghidra_assistant.utils.debugger.gdb_rsp import (
    AArch64ConcreteGDBTarget,
    GDBRemoteServer,
)
from ghidra_assistant.utils.utils import info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expose the Raspberry Pi 4 Gupje session as a host-side GDB RSP endpoint."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address for the GDB server")
    parser.add_argument("--port", type=int, default=9000, help="Bind port for the GDB server")
    parser.add_argument(
        "--entry",
        type=lambda value: int(value, 0),
        default=None,
        help="Initial PC to expose to GDB before the target has reported a real stop address",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    target = AArch64ConcreteGDBTarget(cd, start_pc=args.entry)
    server = GDBRemoteServer(target)

    info(
        "Starting Raspberry Pi 4 GDB bridge on "
        f"{args.host}:{args.port}. Current implementation supports register and memory access plus "
        "continue, single-step, and software breakpoints."
    )
    if args.entry is not None:
        info(f"Using configured initial PC {args.entry:#x}")
    info("In GDB: target remote {}:{}".format(args.host, args.port))
    server.serve_forever(args.host, args.port)


if __name__ == "__main__":
    main()