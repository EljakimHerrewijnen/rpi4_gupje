MEMORY {
    ROM (rwx): ORIGIN = 0x0000000000081000, LENGTH = 0x1000
}

SECTIONS
{
     . = 0x0000000000081000;
     .text . : {
          *(.text*)
          *(.data*)
          *(.rodata*)
     } >ROM

}