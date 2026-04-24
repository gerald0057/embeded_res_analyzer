# ESA - Embedded Section Analyzer

CLI & TUI tool for analyzing ELF object file section sizes, targeted at embedded development workflows.

Replaces the `object_section_stats.sh` script with a more powerful interactive interface.

## Features

- **Section analysis**: Find how much each `.o` file contributes to a specific section (`.text`, `.data`, `.ram_text`, etc.)
- **Multi-toolchain support**: Configure multiple toolchains (RISC-V, ARM, etc.) and switch between them
- **CLI mode**: Drop-in replacement for the shell script, with richer output via Rich tables
- **TUI mode**: Interactive terminal UI with file tree browsing, glob pattern input, and live results
- **Three tools**: `objdump -h` (section-level), `size` (text/data/bss breakdown), `readelf -S` (detailed)

## Installation

```bash
pip install -e .
# Or with TUI support (included by default):
pip install -e ".[dev]"
```

## Quick Start

### 1. Add a toolchain

```bash
esa config add riscv --objdump /opt/Xuantie-900-gcc-elf-newlib-x86_64-V2.10.2/bin/riscv64-unknown-elf-objdump
# Optional: add size and readelf paths
esa config add riscv --objdump ... --size /path/to/riscv-size --readelf /path/to/riscv-readelf
```

### 2. Analyze section sizes (shell script equivalent)

```bash
# Equivalent to: object_section_stats.sh -s .ram_text "obj/subsys/**/*.o"
esa section -s .ram_text "obj/**/*.o"

# Decimal output
esa section -s .text --dec "build/**/*.o"

# Multiple patterns
esa section -s .data "foo.o" "bar.o" "build/**/*.o"
```

### 3. Other commands

```bash
# List all sections in a file
esa sections build/main.o

# Show text/data/bss size breakdown
esa size build/main.o

# List configured toolchains
esa config list

# Set active toolchain
esa config set riscv
```

### 4. TUI Mode

```bash
esa tui
```

Interactive interface with:
- Glob pattern input for file selection
- File tree browser
- Section name input
- Hex/decimal toggle
- "List Sections" to inspect a single file
- Config management via `c` key

## Commands Reference

| Command | Description |
|---------|-------------|
| `esa section -s <name> <patterns>` | Analyze section size across files |
| `esa sections <file>` | List all sections in a file |
| `esa size <file>` | Show text/data/bss breakdown |
| `esa tui` | Launch interactive TUI |
| `esa config list` | List toolchains |
| `esa config add <name> --objdump <path>` | Add toolchain |
| `esa config remove <name>` | Remove toolchain |
| `esa config set <name>` | Set active toolchain |

## Configuration

Config stored at `~/.config/embedded-analyzer/config.yaml`:

```yaml
current_toolchain: riscv
toolchains:
  - name: riscv
    objdump: /opt/.../riscv64-unknown-elf-objdump
    size: /opt/.../riscv64-unknown-elf-size
    readelf: /opt/.../riscv64-unknown-elf-readelf
  - name: arm
    objdump: /usr/bin/arm-none-eabi-objdump
```

## Architecture

```
src/embedded_analyzer/
├── cli.py              # Click CLI entry point
├── config.py           # Multi-toolchain YAML config
├── core/
│   ├── analyzer.py     # Orchestrates objdump/size/readelf
│   ├── models.py       # Dataclasses for results
│   ├── exceptions.py   # Custom exceptions
│   ├── objdump_parser.py  # Core: objdump -h section parsing
│   └── parsers/
│       ├── base_parser.py  # subprocess command runner
│       ├── size_parser.py   # size command output
│       └── readelf_parser.py # readelf -S output
└── tui/
    ├── app.py          # Textual main app
    └── screens/
        └── config_screen.py  # Toolchain config modal
```