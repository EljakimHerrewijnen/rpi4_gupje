#include "../include/mock_tee_layout.h"
#include "../include/tee_protocol.h"

static volatile tee_log_t *const g_log = (volatile tee_log_t *)SECURE_LOG_ADDR;
typedef tee_response_t (*smc_call_fn_t)(uint64_t, uint64_t, uint64_t);
static smc_call_fn_t const g_smc_call = (smc_call_fn_t)KERNEL_SMC_SHIM_ADDR;

void kernel_entry(void) {
    (void)g_smc_call(CMD_ECHO_U64, 0x33, 0x55);

    g_log->kernel_processed = g_log->result + 1;

    /* End in a synchronous trap so the debugger can regain control. */
    __builtin_trap();
}