/* Minimal Cortex-M startup (link-verification only). */
.syntax unified
.cpu cortex-m4
.thumb

.section .isr_vector,"a",%progbits
.global g_pfnVectors
.type g_pfnVectors, %object
g_pfnVectors:
    .word _estack
    .word Reset_Handler
    .rept 14
    .word Default_Handler
    .endr
.size g_pfnVectors, . - g_pfnVectors

.text
.thumb_func
.global Reset_Handler
.type Reset_Handler, %function
Reset_Handler:
    bl main
    b .

.thumb_func
.global Default_Handler
.type Default_Handler, %function
Default_Handler:
    b .