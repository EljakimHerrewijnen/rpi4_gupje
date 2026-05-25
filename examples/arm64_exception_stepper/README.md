# ARM64 Mock TEE With Compiled C Payloads

This example builds and loads three compiled AArch64 C payloads:

1. `tee/normalworld_kernel/kernel.c`
2. `tee/secure_mon/secure_mon.c`
3. `tee/tee_os/tee_os.c`

The flow is:

1. Kernel runs in normal world and issues a monitor-style trap via `smc_call.S`
2. EL2 handler routes the trap to `secure_mon`, which forwards to secure EL1 TEE OS
3. TEE OS handles command and returns result to secure monitor, then kernel
4. Kernel processes the response
5. Kernel executes `brk` and returns control to debugger

Vector handling is split by exception level:

- EL2 VBAR: handles monitor-call exceptions and dispatches to `secure_mon`
- EL1 VBAR: handles `BRK` and returns directly to debugger

## Single Entry Script

- `load_tee_env.py`

This script does all of the following:

1. Builds C payloads via `tee/Makefile`
2. Extracts flat `.bin` blobs with `objcopy`
3. Loads blobs into target memory
4. Installs EL1 and EL2 VBAR handlers
5. Enters EL1 via debug bridge
6. Runs kernel through secure monitor call path
7. Validates log state

## Run

```bash
python3 load_tee_env.py
```

Stepper preview mode:

```bash
python3 load_tee_env.py --use-stepper
```

This steps a scratch copy of the kernel with the exception stepper, then runs
the verified direct flow.

Compile-only mode:

```bash
python3 load_tee_env.py --compile-only
```

Manual build mode:

```bash
make -C tee all
```

## Required Host Tools

- `clang`
- `objcopy` (GNU binutils)

## Tee Layout

- `tee/include/mock_tee_layout.h` shared addresses and protocol offsets
- `tee/include/tee_protocol.h` request/response/log structures
- `tee/secure_mon/secure_mon.c` secure monitor forwarder
- `tee/tee_os/tee_os.c` secure EL1 TEE OS kernel handler
- `tee/normalworld_kernel/kernel.c` normal-world caller
- `tee/normalworld_kernel/smc_call.S` monitor-call instruction shim
- `tee/Makefile` standalone build pipeline

## Notes

- This is intentionally a mock educational environment with no signing/verification.
- The platform starts in EL2 and uses an EL2->EL1 trampoline before stepping.