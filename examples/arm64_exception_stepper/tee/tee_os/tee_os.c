#include "../include/mock_tee_layout.h"
#include "../include/tee_protocol.h"

static volatile tee_state_t *const g_state = (volatile tee_state_t *)SECURE_STATE_ADDR;

/*
 * TEE OS kernel handler running in secure EL1 context.
 * It processes commands forwarded by the secure monitor.
 */
tee_response_t tee_os_entry(uint64_t cmd_id, uint64_t arg0, uint64_t arg1) {
    tee_response_t response = {.status = 0xFF, .result = 0};

    g_state->app_call_count += 1;

    if (cmd_id == CMD_GET_VERSION) {
        response.status = 0;
        response.result = 0x20260522;
        return response;
    }

    if (cmd_id == CMD_GET_COUNTER) {
        response.status = 0;
        response.result = g_state->app_call_count;
        return response;
    }

    if (cmd_id == CMD_ECHO_U64) {
        response.status = 0;
        response.result = (arg0 ^ arg1) + g_state->app_call_count;
        return response;
    }

    return response;
}