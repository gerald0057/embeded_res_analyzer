"""
CLI entry point for esa (Embedded Section Analyzer).

Usage:
    esa section -s .text "build/**/*.o"              # Section analysis (shell script equivalent)
    esa section -s .ram_text --dec "obj/*.o"          # Decimal output
    esa sections build/main.o                          # List all sections of a file
    esa size build/main.o                              # Show text/data/bss sizes
    esa tui                                             # Launch TUI
    esa config list                                     # List toolchains
    esa config add <name> --objdump <path>             # Add a toolchain
    esa config remove <name>                            # Remove a toolchain
    esa config set <name>                               # Set active toolchain
    esa config section list                             # List section presets
    esa config section add .ram_text                   # Add section preset
    esa config section remove .ram_text                # Remove section preset
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .core.analyzer import Analyzer
from .config import load_config, add_toolchain, remove_toolchain, set_current_toolchain, add_section, remove_section
from .core.models import AppConfig

console = Console()


def _get_analyzer(toolchain: Optional[str] = None) -> Analyzer:
    config = load_config()
    if toolchain:
        for tc in config.toolchains:
            if tc.name == toolchain:
                return Analyzer(toolchain=tc)
        console.print(f"[red]Toolchain '{toolchain}' not found[/red]")
        console.print("Available toolchains:")
        for tc in config.toolchains:
            marker = " *" if tc.name == config.current_toolchain else ""
            console.print(f"  - {tc.name}{marker}")
        sys.exit(1)
    return Analyzer().init_from_config(config)


@click.group()
@click.version_option(version="1.0.0", prog_name="esa")
def cli():
    """ESA - Embedded Section Analyzer

    Analyze section sizes of ELF object files for embedded development.
    """
    pass


@cli.command()
@click.option("-s", "--section", required=True, help="Section name to analyze (e.g. .text, .data, .ram_text)")
@click.option("--dec", "mode_dec", is_flag=True, default=False, help="Show sizes in decimal (default: hex)")
@click.option("-t", "--toolchain", default=None, help="Toolchain name to use")
@click.argument("patterns", nargs=-1, required=True)
def section(section, mode_dec, toolchain, patterns):
    """Analyze section sizes across object files (shell script equivalent).

    Equivalent to object_section_stats.sh -s <section> <patterns>

    \b
    Examples:
        esa section -s .text "build/**/*.o"
        esa section -s .ram_text --dec "obj/**/*.o"
        esa section -s .data "foo.o" "bar.o" "build/**/*.o"
    """
    analyzer = _get_analyzer(toolchain)
    files = analyzer.expand_patterns(list(patterns))

    if not files:
        console.print(f"[yellow]No files matched patterns: {patterns}[/yellow]")
        sys.exit(1)

    result = analyzer.analyze_section(files, section)

    console.print(f"\n[bold yellow]Target Section: {section}[/bold yellow]")
    console.rule()

    table = Table(show_footer=True)
    table.add_column("SIZE (hex)" if not mode_dec else "SIZE (dec)", style="cyan", footer="TOTAL")
    table.add_column("FILENAME")

    for f in result.files:
        if f.found:
            size_str = str(f.size) if mode_dec else f.size_hex
            table.add_row(size_str, f.file_path)

    console.print(table)
    console.rule()

    total_str = str(result.total) if mode_dec else f"0x{result.total:x} ({result.total} bytes)"
    console.print(f"[bold green]TOTAL: {total_str}[/bold green]")
    console.print(f"Matched: {result.matched_count}/{len(result.files)} files\n")


@cli.command()
@click.option("-t", "--toolchain", default=None, help="Toolchain name to use")
@click.argument("file_path")
def sections(toolchain, file_path):
    """List all sections in an object file.

    \b
    Example:
        esa sections build/main.o
    """
    analyzer = _get_analyzer(toolchain)

    if not Path(file_path).exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        sys.exit(1)

    section_list = analyzer.list_sections(file_path)

    table = Table(title=f"Sections: {file_path}")
    table.add_column("Idx", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Size (hex)", style="cyan", justify="right")
    table.add_column("Size (dec)", style="green", justify="right")
    table.add_column("VMA", style="dim")

    for s in section_list:
        table.add_row(str(s.index), s.name, f"0x{s.size:x}", str(s.size), s.vma)

    console.print(table)
    total = sum(s.size for s in section_list)
    console.print(f"\nTotal sections: {len(section_list)}, Total size: {total} bytes\n")


@cli.command()
@click.option("-t", "--toolchain", default=None, help="Toolchain name to use")
@click.argument("file_path")
def size(toolchain, file_path):
    """Show text/data/bss size breakdown for an object file.

    \b
    Example:
        esa size build/main.o
    """
    analyzer = _get_analyzer(toolchain)

    if not Path(file_path).exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        sys.exit(1)

    try:
        result = analyzer.analyze_size(file_path)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[dim]Add objdump to your toolchain config to enable size command.[/dim]")
        sys.exit(1)

    table = Table(title=f"Size: {file_path}")
    table.add_column("Segment", style="bold")
    table.add_column("Size", style="cyan", justify="right")
    table.add_column("Size (hex)", style="dim", justify="right")

    table.add_row("text", str(result.text_size), f"0x{result.text_size:x}")
    table.add_row("data", str(result.data_size), f"0x{result.data_size:x}")
    table.add_row("bss", str(result.bss_size), f"0x{result.bss_size:x}")
    table.add_row("[bold]total[/bold]", str(result.total_size), f"0x{result.total_size:x}")
    table.add_row("[bold]flash[/bold]", str(result.flash_usage), f"0x{result.flash_usage:x}")
    table.add_row("[bold]ram[/bold]", str(result.ram_usage), f"0x{result.ram_usage:x}")

    console.print(table)


@cli.command()
def tui():
    """Launch the TUI (Terminal User Interface)."""
    try:
        from .tui.app import SectionAnalyzerApp
        app = SectionAnalyzerApp()
        app.run()
    except ImportError as e:
        console.print(f"[red]TUI dependencies not installed: {e}[/red]")
        console.print("[dim]Install textual: pip install textual[/dim]")
        sys.exit(1)


@cli.group()
def config():
    """Manage toolchain configurations."""
    pass


@config.command("list")
def config_list():
    """List configured toolchains."""
    cfg = load_config()
    if not cfg.toolchains:
        console.print("[yellow]No toolchains configured.[/yellow]")
        console.print("[dim]Add one with: esa config add <name> --objdump <path>[/dim]")
        return

    table = Table(title="Toolchains")
    table.add_column("Active", style="bold")
    table.add_column("Name")
    table.add_column("objdump")
    table.add_column("size")
    table.add_column("readelf")

    for tc in cfg.toolchains:
        active = "★" if tc.name == cfg.current_toolchain else ""
        table.add_row(active, tc.name, tc.objdump, tc.size or "-", tc.readelf or "-")

    console.print(table)


@config.command("add")
@click.argument("name")
@click.option("--objdump", required=True, help="Path to objdump binary")
@click.option("--size", "size_path", default=None, help="Path to size binary (optional)")
@click.option("--readelf", "readelf_path", default=None, help="Path to readelf binary (optional)")
def config_add(name, objdump, size_path, readelf_path):
    """Add a new toolchain configuration.

    \b
    Example:
        esa config add riscv --objdump /opt/.../riscv64-unknown-elf-objdump
    """
    try:
        add_toolchain(name, objdump, size_path, readelf_path)
        console.print(f"[green]Added toolchain: {name}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@config.command("remove")
@click.argument("name")
def config_remove(name):
    """Remove a toolchain configuration."""
    try:
        remove_toolchain(name)
        console.print(f"[green]Removed toolchain: {name}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@config.command("set")
@click.argument("name")
def config_set(name):
    """Set the active toolchain."""
    try:
        set_current_toolchain(name)
        console.print(f"[green]Active toolchain set to: {name}[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@config.group("section")
def config_section():
    """Manage section name presets (used in TUI dropdown)."""
    pass


@config_section.command("list")
def config_section_list():
    """List configured section presets."""
    cfg = load_config()
    if not cfg.sections:
        console.print("[yellow]No section presets configured.[/yellow]")
        return
    console.print("[bold]Section presets:[/bold]")
    for s in cfg.sections:
        console.print(f"  {s}")


@config_section.command("add")
@click.argument("name")
def config_section_add(name):
    """Add a section name preset."""
    cfg = add_section(name)
    console.print(f"[green]Added section preset: {name}[/green]")
    console.print(f"[dim]Current presets: {', '.join(cfg.sections)}[/dim]")


@config_section.command("remove")
@click.argument("name")
def config_section_remove(name):
    """Remove a section name preset."""
    cfg = remove_section(name)
    console.print(f"[green]Removed section preset: {name}[/green]")


def main():
    cli()


if __name__ == "__main__":
    main()