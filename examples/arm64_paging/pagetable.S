
/*
 * This file was automatically generated using arm64-pgtable-tool.
 * See: https://github.com/ashwio/arm64-pgtable-tool
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * This code programs the following translation table structure:
 *
 *         level 1 table @ 0x808000
 *         [#   0] 0x000000000000-0x00003fffffff, Code, CODE
 *         [#   1] 0x000040000000-0x00007fffffff, Code, CODE
 *         [#   2] 0x000080000000-0x0000bfffffff, Code, CODE
 *         [#   3]-------------------------\
 *                 level 2 table @ 0x809000
 *                 [# 497]-------------------------\
 *                         level 3 table @ 0x80a000
 *                         [#   1] 0x0000fe201000-0x0000fe201fff, Device, UART0
 *
 * The following command line arguments were passed to arm64-pgtable-tool:
 *
 *      -i ../pagetable_layout.txt
 *      -ttb 0x808000
 *      -el 2
 *      -tg 4K
 *      -tsz 32
 *
 * This memory map requires a total of 3 translation tables.
 * Each table occupies 4K of memory (0x1000 bytes).
 * The buffer pointed to by 0x808000 must therefore be 3x 4K = 0x3000 bytes long.
 * It is the programmer's responsibility to guarantee this.
 *
 * The programmer must also ensure that the virtual memory region containing the
 * translation tables is itself marked as NORMAL in the memory map file.
 */

    .section .data.mmu
    .balign 2

    mmu_lock: .4byte 0                   // lock to ensure only 1 CPU runs init
    #define LOCKED 1

    mmu_init: .4byte 0                   // whether init has been run
    #define INITIALISED 1

    .section .text.mmu_on
    .balign 2
    .global mmu_on
    .type mmu_on, @function

mmu_on:

    ADRP    x0, mmu_lock                 // get 4KB page containing mmu_lock
    ADD     x0, x0, :lo12:mmu_lock       // restore low 12 bits lost by ADRP
    MOV     w1, #LOCKED
    SEVL                                 // first pass won't sleep
1:
    WFE                                  // sleep on retry
    LDAXR   w2, [x0]                     // read mmu_lock
    CBNZ    w2, 1b                       // not available, go back to sleep
    STXR    w3, w1, [x0]                 // try to acquire mmu_lock
    CBNZ    w3, 1b                       // failed, go back to sleep

check_already_initialised:

    ADRP    x1, mmu_init                 // get 4KB page containing mmu_init
    ADD     x1, x1, :lo12:mmu_init       // restore low 12 bits lost by ADRP
    LDR     w2, [x1]                     // read mmu_init
    CBNZ    w2, end                      // init already done, skip to the end

zero_out_tables:

    LDR     x2, =0x808000                // address of first table
    LDR     x3, =0x3000                  // combined length of all tables
    LSR     x3, x3, #5                   // number of required STP instructions
    FMOV    d0, xzr                      // clear q0
1:
    STP     q0, q0, [x2], #32            // zero out 4 table entries at a time
    SUBS    x3, x3, #1
    B.NE    1b

load_descriptor_templates:

    LDR     x2, =0x40000000000705        // Device block
    LDR     x3, =0x40000000000707        // Device page
    LDR     x4, =0x40000000000701        // RW data block
    LDR     x5, =0x40000000000703        // RW data page
    LDR     x20, =0x781                  // code block
    LDR     x21, =0x783                  // code page
    

program_table_0:

    LDR     x8, =0x808000                // base address of this table
    LDR     x9, =0x40000000              // chunk size

program_table_0_entry_0_to_2:

    LDR     x10, =0                      // idx
    LDR     x11, =3                      // number of contiguous entries
    LDR     x12, =0x0                    // output address of entry[idx]
1:
    ORR     x12, x12, x20                // merge output address with template
    STR     X12, [x8, x10, lsl #3]       // write entry into table
    ADD     x10, x10, #1                 // prepare for next entry idx+1
    ADD     x12, x12, x9                 // add chunk to address
    SUBS    x11, x11, #1                 // loop as required
    B.NE    1b

program_table_0_entry_3:

    LDR     x10, =3                      // idx
    LDR     x11, =0x809000               // next-level table address
    ORR     x11, x11, #0x3               // next-level table descriptor
    STR     x11, [x8, x10, lsl #3]       // write entry into table
program_table_1:

    LDR     x8, =0x809000                // base address of this table
    LDR     x9, =0x200000                // chunk size

program_table_1_entry_497:

    LDR     x10, =497                    // idx
    LDR     x11, =0x80a000               // next-level table address
    ORR     x11, x11, #0x3               // next-level table descriptor
    STR     x11, [x8, x10, lsl #3]       // write entry into table
program_table_2:

    LDR     x8, =0x80a000                // base address of this table
    LDR     x9, =0x1000                  // chunk size

program_table_2_entry_1:

    LDR     x10, =1                      // idx
    LDR     x11, =1                      // number of contiguous entries
    LDR     x12, =0xfe201000             // output address of entry[idx]
1:
    ORR     x12, x12, x3                 // merge output address with template
    STR     X12, [x8, x10, lsl #3]       // write entry into table
    ADD     x10, x10, #1                 // prepare for next entry idx+1
    ADD     x12, x12, x9                 // add chunk to address
    SUBS    x11, x11, #1                 // loop as required
    B.NE    1b

init_done:

    MOV     w2, #INITIALISED
    STR     w2, [x1]

end:

    LDR     x1, =0x808000                // program ttbr0 on this CPU
    MSR     ttbr0_el2, x1
    LDR     x1, =0xff                    // program mair on this CPU
    MSR     mair_el2, x1
    LDR     x1, =0x80803520              // program tcr on this CPU
    MSR     tcr_el2, x1
    ISB
    MRS     x2, tcr_el2                  // verify CPU supports desired config
    CMP     x2, x1
    B.NE    .
    LDR     x1, =0x1005                  // program sctlr on this CPU
    MSR     sctlr_el2, x1
    ISB                                  // synchronize context on this CPU
    STLR    wzr, [x0]                    // release mmu_lock
    RET                                  // done!
