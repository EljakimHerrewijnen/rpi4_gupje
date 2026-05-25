#ifndef TEE_PROTOCOL_H
#define TEE_PROTOCOL_H

#include <stdint.h>

typedef struct {
    uint64_t cmd_id;
    uint64_t arg0;
    uint64_t arg1;
} tee_request_t;

typedef struct {
    uint64_t status;
    uint64_t result;
} tee_response_t;

typedef struct {
    uint64_t app_call_count;
} tee_state_t;

typedef struct {
    uint64_t exception_id;
    uint64_t elr;
    uint64_t smc_count;
    uint64_t app_calls;
    uint64_t cmd_id;
    uint64_t arg0;
    uint64_t arg1;
    uint64_t status;
    uint64_t result;
    uint64_t kernel_processed;
} tee_log_t;

#endif