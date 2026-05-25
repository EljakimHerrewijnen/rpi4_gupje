.text
.align 2
.global smc_call
.type smc_call, %function
smc_call:
    smc #0
    ret
