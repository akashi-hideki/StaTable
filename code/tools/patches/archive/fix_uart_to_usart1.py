"""fix_uart_to_usart1.py

QEMU netduinoplus2 maps -serial to USART1 (0x40011000, PA9/PA10),
not USART2. Rewrite syscalls.c accordingly.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SC = ROOT / "eclipse_installer" / "templates" / "syscalls.c"
t = SC.read_text(encoding="utf-8")

# Replace USART2 block with USART1
old_usart = (
    "/* --- USART2 (0x40004400) --- */\n"
    "#define USART2_BASE     0x40004400UL\n"
    "#define USART2_SR       (*(volatile uint32_t *)(USART2_BASE + 0x00UL))\n"
    "#define USART2_DR       (*(volatile uint32_t *)(USART2_BASE + 0x04UL))\n"
    "#define USART2_BRR      (*(volatile uint32_t *)(USART2_BASE + 0x08UL))\n"
    "#define USART2_CR1      (*(volatile uint32_t *)(USART2_BASE + 0x0CUL))\n"
)
new_usart = (
    "/* --- USART1 (0x40011000) --- */\n"
    "#define USART1_BASE     0x40011000UL\n"
    "#define USART1_SR       (*(volatile uint32_t *)(USART1_BASE + 0x00UL))\n"
    "#define USART1_DR       (*(volatile uint32_t *)(USART1_BASE + 0x04UL))\n"
    "#define USART1_BRR      (*(volatile uint32_t *)(USART1_BASE + 0x08UL))\n"
    "#define USART1_CR1      (*(volatile uint32_t *)(USART1_BASE + 0x0CUL))\n"
    "#define RCC_APB2ENR     (*(volatile uint32_t *)(RCC_BASE + 0x44UL))\n"
)
if old_usart not in t:
    raise SystemExit("[FAIL] usart2 block not found")
t = t.replace(old_usart, new_usart, 1)

# Replace uart2_init body
old_init = (
    "void uart2_init(void)\n"
    "{\n"
    "    RCC_AHB1ENR |= (1U << 0);    /* GPIOAEN */\n"
    "    RCC_APB1ENR |= (1U << 17);   /* USART2EN */\n"
    "\n"
    "    /* PA2 = AF7 (USART2_TX), PA3 = AF7 (USART2_RX) */\n"
    "    GPIOA_MODER &= ~((3U << 4) | (3U << 6));\n"
    "    GPIOA_MODER |=  ((2U << 4) | (2U << 6));\n"
    "    GPIOA_AFRL  &= ~((0xFU << 8) | (0xFU << 12));\n"
    "    GPIOA_AFRL  |=  ((7U << 8) | (7U << 12));\n"
    "\n"
    "    USART2_BRR = 16000000UL / 115200UL;  /* ~139 */\n"
    "    USART2_CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE;\n"
    "}\n"
)
new_init = (
    "void uart2_init(void)\n"
    "{\n"
    "    RCC_AHB1ENR |= (1U << 0);    /* GPIOAEN */\n"
    "    RCC_APB2ENR |= (1U << 4);    /* USART1EN */\n"
    "\n"
    "    /* PA9 = AF7 (USART1_TX), PA10 = AF7 (USART1_RX) */\n"
    "    GPIOA_MODER &= ~((3U << 18) | (3U << 20));\n"
    "    GPIOA_MODER |=  ((2U << 18) | (2U << 20));\n"
    "    GPIOA_AFRH  &= ~((0xFU << 4) | (0xFU << 8));\n"
    "    GPIOA_AFRH  |=  ((7U << 4) | (7U << 8));\n"
    "\n"
    "    USART1_BRR = 16000000UL / 115200UL;  /* ~139 */\n"
    "    USART1_CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE;\n"
    "}\n"
)
if old_init not in t:
    raise SystemExit("[FAIL] uart2_init body not found")
t = t.replace(old_init, new_init, 1)

# Replace putc body
old_putc = (
    "void uart2_putc(char c)\n"
    "{\n"
    "    while (!(USART2_SR & USART_SR_TXE)) { }\n"
    "    USART2_DR = (uint32_t)(unsigned char)c;\n"
    "}\n"
)
new_putc = (
    "void uart2_putc(char c)\n"
    "{\n"
    "    while (!(USART1_SR & USART_SR_TXE)) { }\n"
    "    USART1_DR = (uint32_t)(unsigned char)c;\n"
    "}\n"
)
if old_putc not in t:
    raise SystemExit("[FAIL] putc not found")
t = t.replace(old_putc, new_putc, 1)

# Add GPIOA_AFRH define
old_gpio = (
    "#define GPIOA_MODER     (*(volatile uint32_t *)(GPIOA_BASE + 0x00UL))\n"
    "#define GPIOA_AFRL      (*(volatile uint32_t *)(GPIOA_BASE + 0x20UL))\n"
)
new_gpio = (
    "#define GPIOA_MODER     (*(volatile uint32_t *)(GPIOA_BASE + 0x00UL))\n"
    "#define GPIOA_AFRL      (*(volatile uint32_t *)(GPIOA_BASE + 0x20UL))\n"
    "#define GPIOA_AFRH      (*(volatile uint32_t *)(GPIOA_BASE + 0x24UL))\n"
)
if old_gpio not in t:
    raise SystemExit("[FAIL] gpio defines not found")
t = t.replace(old_gpio, new_gpio, 1)

SC.write_text(t, encoding="utf-8")
print(f"[OK] patched {SC} to USART1")
