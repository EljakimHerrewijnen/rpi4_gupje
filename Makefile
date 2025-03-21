ifeq ($(ANDROID_NDK_ROOT),)
$(error Error : Set the env variable 'ANDROID_NDK_ROOT' with the path of the Android NDK (version 20))
endif

CC := $(ANDROID_NDK_ROOT)/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android27-clang
AR := $(ANDROID_NDK_ROOT)/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android-ar
OBJCOPY := $(ANDROID_NDK_ROOT)/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android-objcopy
LD := $(ANDROID_NDK_ROOT)/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android-ld.bfd

#==================RPI4b==================
all: rpi4

CFLAGS_RASPBERRYPI4 = -Os -Idevices/rpi4_gupje/ -DGUPJE_BLOCK_SIZE=0x100
rpi4:
	[ -d bin/rpi4 ] || mkdir -p bin/rpi4/
	$(CC) arm64_stub.S -c -o bin/rpi4/entry.o $(CFLAGS_RASPBERRYPI4)
	$(CC) debugger.c -c -o bin/rpi4/debugger.o $(CFLAGS_RASPBERRYPI4)
	$(LD) -T devices/rpi4_gupje/linkscript.ld bin/rpi4/entry.o bin/rpi4/debugger.o -o bin/rpi4/debugger.elf --just-symbols=devices/rpi4_gupje/symbols.txt
	$(OBJCOPY) -O binary bin/rpi4/debugger.elf bin/rpi4/debugger.bin