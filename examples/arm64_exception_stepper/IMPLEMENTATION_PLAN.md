# Mock TEE End-to-End Rewrite Plan

## Goal
Build a clean example that demonstrates a full mock secure flow:
normal-world kernel -> secure TEE OS handler -> secure TEE app -> return to kernel,
with debugger-driven setup and end-to-end stepping/inspection.

## Scope
1. Full rewrite of current staged Python demo scripts.
2. Add `tee/tee_os/` with a simple secure exception handler/dispatcher.
3. Add `tee/tee_app/` with a small app command implementation.
4. Add `tee/normalworld_kernel/` with a caller that queries secure data.
5. Add `setup_mock_tee.py` to configure memory maps and load all components.
6. Add debugger hook-through flow to trace callsite -> secure handling -> kernel response processing.

## Deliverables
- `tee/common/` shared constants, protocol, and assembly helpers.
- `tee/tee_os/handler.py` secure vector/dispatcher logic.
- `tee/tee_app/app.py` secure app logic and command handlers.
- `tee/normalworld_kernel/kernel.py` normal-world caller payload.
- `setup_mock_tee.py` loading/setup orchestration.
- `run_end_to_end_demo.py` debugger stepping/hook-through orchestration.
- Legacy `part*.py` scripts rewritten as thin wrappers to the new flow.
- README updated with architecture and execution instructions.

## Execution Sequence
1. Build and load secure TEE app code blob.
2. Build and install secure TEE OS VBAR/handler.
3. Build and load normal-world kernel code blob.
4. Transition from EL2 to EL1 entry bridge.
5. Step kernel to secure call instruction.
6. Let secure handler + app execute natively.
7. Return to debugger and validate logs/state.

## Validation Criteria
- Secure handler `svc_count` increments.
- App invocation count increments.
- Kernel receives and processes secure return values.
- Trace proves the flow from kernel callsite to secure app and back.

## Notes
- This remains a mock educational flow with no signing/verification chain.
- Uses known-good scratch-VBAR stepping behavior on current QEMU target.
