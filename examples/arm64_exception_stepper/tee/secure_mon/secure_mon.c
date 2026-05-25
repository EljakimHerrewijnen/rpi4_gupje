#include "../include/mock_tee_layout.h"
#include "../include/tee_protocol.h"

typedef tee_response_t (*tee_os_fn_t)(uint64_t, uint64_t, uint64_t);

static volatile tee_log_t *const g_log = (volatile tee_log_t *)SECURE_LOG_ADDR;
static tee_os_fn_t const g_tee_os_entry = (tee_os_fn_t)TEE_OS_ADDR;

/*
 * Secure monitor entry, modeled as EL3 boundary handler.
 * Receives SMC arguments and forwards into the secure EL1 TEE OS kernel.
 */
tee_response_t secure_mon_entry(uint64_t smc_fid, uint64_t arg0, uint64_t arg1) {
    tee_response_t response;

    g_log->cmd_id = smc_fid;
    g_log->arg0 = arg0;
    g_log->arg1 = arg1;
    g_log->app_calls += 1;

    response = g_tee_os_entry(smc_fid, arg0, arg1);

    g_log->status = response.status;
    g_log->result = response.result;
    return response;
}
