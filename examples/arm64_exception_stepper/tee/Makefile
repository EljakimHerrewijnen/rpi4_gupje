CLANG ?= clang
OBJCOPY ?= objcopy
BUILD_DIR := build
INCLUDE_DIR := include
CFLAGS := --target=aarch64-none-elf -O2 -ffreestanding -fno-stack-protector -fno-builtin -fomit-frame-pointer -fno-pic -nostdlib -I $(INCLUDE_DIR)

SECURE_MON_SRC := secure_mon/secure_mon.c
TEE_OS_SRC := tee_os/tee_os.c
KERNEL_SRC := normalworld_kernel/kernel.c
KERNEL_SMC_SRC := normalworld_kernel/smc_call.S

SECURE_MON_OBJ := $(BUILD_DIR)/secure_mon.o
TEE_OS_OBJ := $(BUILD_DIR)/tee_os.o
KERNEL_OBJ := $(BUILD_DIR)/kernel.o
KERNEL_SMC_OBJ := $(BUILD_DIR)/kernel_smc.o

SECURE_MON_BIN := $(BUILD_DIR)/secure_mon.bin
TEE_OS_BIN := $(BUILD_DIR)/tee_os.bin
KERNEL_BIN := $(BUILD_DIR)/kernel.bin
KERNEL_SMC_BIN := $(BUILD_DIR)/kernel_smc.bin

.PHONY: all clean

all: $(SECURE_MON_BIN) $(TEE_OS_BIN) $(KERNEL_BIN) $(KERNEL_SMC_BIN)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(SECURE_MON_OBJ): $(SECURE_MON_SRC) $(INCLUDE_DIR)/mock_tee_layout.h $(INCLUDE_DIR)/tee_protocol.h | $(BUILD_DIR)
	$(CLANG) $(CFLAGS) -c $< -o $@

$(TEE_OS_OBJ): $(TEE_OS_SRC) $(INCLUDE_DIR)/mock_tee_layout.h $(INCLUDE_DIR)/tee_protocol.h | $(BUILD_DIR)
	$(CLANG) $(CFLAGS) -c $< -o $@

$(KERNEL_OBJ): $(KERNEL_SRC) $(INCLUDE_DIR)/mock_tee_layout.h $(INCLUDE_DIR)/tee_protocol.h | $(BUILD_DIR)
	$(CLANG) $(CFLAGS) -c $< -o $@

$(KERNEL_SMC_OBJ): $(KERNEL_SMC_SRC) | $(BUILD_DIR)
	$(CLANG) --target=aarch64-none-elf -c $< -o $@

$(SECURE_MON_BIN): $(SECURE_MON_OBJ)
	$(OBJCOPY) -I elf64-little -O binary -j .text $< $@

$(TEE_OS_BIN): $(TEE_OS_OBJ)
	$(OBJCOPY) -I elf64-little -O binary -j .text $< $@

$(KERNEL_BIN): $(KERNEL_OBJ)
	$(OBJCOPY) -I elf64-little -O binary -j .text $< $@

$(KERNEL_SMC_BIN): $(KERNEL_SMC_OBJ)
	$(OBJCOPY) -I elf64-little -O binary -j .text $< $@

clean:
	rm -rf $(BUILD_DIR)
