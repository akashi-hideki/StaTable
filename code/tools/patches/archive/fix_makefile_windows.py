"""fix_makefile_windows.py"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MK = ROOT / "eclipse_installer" / "templates" / "Makefile.tmpl"
T = "\t"

lines = [
    "# Makefile - StaTable Eclipse project (STM32F405)",
    "# Portable: no find/grep (works on Windows GNU Make)",
    "",
    "PREFIX  = arm-none-eabi-",
    "CC      = $(PREFIX)gcc",
    "AS      = $(PREFIX)gcc",
    "OBJCOPY = $(PREFIX)objcopy",
    "SIZE    = $(PREFIX)size",
    "",
    "TARGET  = firmware",
    "BUILD   = build",
    "",
    "C_SOURCES   := $(wildcard *.c) $(wildcard src/*.c) $(wildcard src/*/*.c) $(wildcard src/*/*/*.c)",
    "ASM_SOURCES := $(wildcard *.s) $(wildcard src/*.s)",
    "",
    "OBJECTS := $(addprefix $(BUILD)/,$(notdir $(C_SOURCES:.c=.o)))",
    "OBJECTS += $(addprefix $(BUILD)/,$(notdir $(ASM_SOURCES:.s=.o)))",
    "",
    "MCU = -mcpu=cortex-m4 -mthumb",
    "",
    "INCLUDES = -I. -Isrc -Isrc/statable_generated",
    "INCLUDES += $(addprefix -I,$(sort $(dir $(wildcard src/statable_generated/*/))))",
    "",
    "CFLAGS  = $(MCU) $(INCLUDES) -std=c99 -Wall -Wextra -ffunction-sections -fdata-sections -Og -g3",
    "ASFLAGS = $(MCU) -g3",
    "LDFLAGS = $(MCU) -specs=nano.specs -specs=nosys.specs -Tlinker_stm32f405.ld -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(TARGET).map",
    "LIBS    = -lc -lm",
    "",
    "VPATH := . src $(sort $(dir $(wildcard src/*/))) $(sort $(dir $(wildcard src/*/*/)))",
    "",
    ".PHONY: all clean size",
    "",
    "all: $(BUILD)/$(TARGET).elf $(BUILD)/$(TARGET).bin size",
    "",
    "$(BUILD)/%.o: %.c",
    T + "@mkdir -p $(BUILD)",
    T + "$(CC) -c $(CFLAGS) $< -o $@",
    "",
    "$(BUILD)/%.o: %.s",
    T + "@mkdir -p $(BUILD)",
    T + "$(AS) -x assembler-with-cpp -c $(ASFLAGS) $< -o $@",
    "",
    "$(BUILD)/$(TARGET).elf: $(OBJECTS)",
    T + "@mkdir -p $(BUILD)",
    T + "$(CC) $(OBJECTS) $(LDFLAGS) $(LIBS) -o $@",
    "",
    "$(BUILD)/$(TARGET).bin: $(BUILD)/$(TARGET).elf",
    T + "$(OBJCOPY) -O binary $< $@",
    "",
    "size: $(BUILD)/$(TARGET).elf",
    T + "$(SIZE) $<",
    "",
    "clean:",
    T + "rm -f $(BUILD)/*.o $(BUILD)/*.elf $(BUILD)/*.bin $(BUILD)/*.map",
    "",
]

MK.write_text("\n".join(lines), encoding="utf-8")
print(f"[OK] {MK}")
print(f"[INFO] tab bytes: {MK.read_bytes().count(9)}")
