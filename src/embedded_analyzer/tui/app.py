"""
Main TUI application for embedded resource analyzer.
"""
from __future__ import annotations

import glob
from pathlib import Path
from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Static,
)
from textual.reactive import reactive

from embedded_analyzer.core.analyzer import Analyzer
from embedded_analyzer.core.models import SectionAnalysisResult
from embedded_analyzer.config import load_config
from embedded_analyzer.tui.widgets.path_input import PathInput
from embedded_analyzer.tui.widgets.section_input import SectionInput
from .screens.config_screen import ConfigScreen


class SectionAnalyzerApp(App):
    """Interactive TUI for analyzing embedded resource sections."""

    TITLE = "ESA"
    SUB_TITLE = "Embedded Section Analyzer"

    CSS = """
    #input-bar {
        layout: horizontal;
        height: auto;
        border-bottom: solid $primary;
        padding: 0 1;
    }

    #input-bar PathInput {
        width: 2fr;
        margin-right: 1;
    }

    #input-bar SectionInput {
        width: 1fr;
        margin-right: 1;
    }

    #input-bar Button {
        min-width: 10;
        margin-right: 1;
    }

    #main-container {
        layout: vertical;
        height: 1fr;
    }

    #status-bar {
        height: auto;
        background: $primary-background;
        color: $text;
        padding: 0 1;
    }

    #help-hint {
        color: $text-disabled;
        padding: 0 1;
        height: auto;
    }

    DataTable {
        height: 1fr;
    }

    #results-panel {
        height: 1fr;
    }

    #summary {
        height: auto;
        padding: 0 1;
        background: $boost;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("c", "config", "Config"),
        Binding("a", "analyze", "Analyze"),
        Binding("l", "list_sections", "List Sections"),
        Binding("h", "toggle_hex", "Hex/Dec"),
    ]

    mode_hex: reactive[bool] = reactive(True)

    def __init__(self, toolchain_name: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._toolchain_name = toolchain_name
        self._analyzer: Optional[Analyzer] = None
        self._last_result: Optional[SectionAnalysisResult] = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="input-bar"):
            yield PathInput(
                placeholder="Path or glob  (e.g. build/**/*.o or /path/to/dir)",
                id="path-input",
            )
            yield SectionInput(
                placeholder="Section  (.text .data .bss ...)",
                id="section-input",
            )
            yield Button("Analyze", variant="success", id="analyze-btn")
            yield Button("Sections", variant="default", id="list-sections-btn")
            yield Button("Hex/Dec", variant="default", id="toggle-hex-btn")
            yield Button("Config", variant="primary", id="config-btn")

        with VerticalScroll(id="main-container"):
            yield Static(self._status_text(), id="status-bar")
            yield Static(
                "[dim]Type path + section, press Analyze (or 'a'). "
                "Tab/\u2191\u2193 autocompletes paths & sections. "
                "Directories auto-suggest **//*.o glob. "
                "'c' = config, 'l' = list sections, 'h' = hex/dec.[/dim]",
                id="help-hint",
            )

            with Container(id="results-panel"):
                yield DataTable(id="results-table")
                yield Static("", id="summary")

        yield Footer()

    def _status_text(self) -> str:
        if self._analyzer and self._analyzer._toolchain:
            tc = self._analyzer._toolchain
            return (
                f"[bold green]Toolchain:[/bold green] {tc.name}  "
                f"[bold green]objdump:[/bold green] {tc.objdump}"
            )
        return "[bold red]No toolchain configured[/bold red] - press 'c' to configure"

    def on_mount(self) -> None:
        self._init_analyzer()
        table = self.query_one("#results-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("File", "Size", "Found")

    def _init_analyzer(self):
        self._analyzer = None
        try:
            config = load_config()
            if not config.toolchains:
                return
            target_name = self._toolchain_name or config.current_toolchain
            for tc in config.toolchains:
                if tc.name == target_name:
                    self._analyzer = Analyzer(toolchain=tc)
                    self._analyzer._init_parsers()
                    break
            if self._analyzer is None and config.toolchains:
                tc = config.toolchains[0]
                self._analyzer = Analyzer(toolchain=tc)
                self._analyzer._init_parsers()
        except Exception as e:
            self.notify(f"Toolchain init error: {e}", severity="error")
            self._analyzer = None
        self._update_status()

    def _update_status(self):
        try:
            self.query_one("#status-bar", Static).update(self._status_text())
        except Exception:
            pass

    def _resolve_files(self) -> list[str]:
        raw = self.query_one("#path-input", PathInput).value.strip()
        if not raw:
            return []

        if any(c in raw for c in ("*", "?", "[")):
            return self._analyzer.expand_patterns([raw]) if self._analyzer else sorted(glob.glob(raw, recursive=True))

        p = Path(raw)
        if p.is_dir():
            return sorted(str(f) for f in p.rglob("*.o"))
        elif p.is_file():
            return [str(p)]
        else:
            return self._analyzer.expand_patterns([raw]) if self._analyzer else sorted(glob.glob(raw, recursive=True))

    @work(thread=True)
    def _do_analyze(self, files: list[str], section: str) -> None:
        try:
            result = self._analyzer.analyze_section(files, section)
            self._last_result = result
            self.call_from_thread(self._update_table, result)
        except Exception as e:
            self.call_from_thread(
                lambda: self.notify(f"Analysis error: {e}", severity="error")
            )

    @work(thread=True)
    def _do_list_sections(self, file_path: str) -> None:
        try:
            sections = self._analyzer.list_sections(file_path)
            self.call_from_thread(lambda: self._show_sections(file_path, sections))
        except Exception as e:
            self.call_from_thread(
                lambda: self.notify(f"Error: {e}", severity="error")
            )

    def _update_table(self, result: SectionAnalysisResult) -> None:
        table = self.query_one("#results-table", DataTable)
        table.clear(columns=True)
        col_size = "Size (hex)" if self.mode_hex else "Size (dec)"
        table.add_columns("File", col_size, "Found")
        for f in result.files:
            size_str = f.size_hex if self.mode_hex else str(f.size)
            table.add_row(f.file_path, size_str, "\u2713" if f.found else "\u2717")

        total_str = result.total_hex if self.mode_hex else str(result.total)
        self.query_one("#summary", Static).update(
            f"Section: [bold]{result.section_name}[/bold] | "
            f"Matched: {result.matched_count}/{len(result.files)} | "
            f"Total: [bold cyan]{total_str}[/bold cyan] ({result.total} bytes)"
        )

    def _show_sections(self, file_path: str, sections) -> None:
        table = self.query_one("#results-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Idx", "Name", "Size (hex)", "Size (dec)", "VMA")

        for s in sections:
            table.add_row(
                str(s.index), s.name, f"0x{s.size:x}", str(s.size), s.vma,
            )

        total = sum(s.size for s in sections)
        self.query_one("#summary", Static).update(
            f"File: [bold]{file_path}[/bold] | "
            f"Sections: {len(sections)} | Total: {total} bytes"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "analyze-btn":
            self.action_analyze()
        elif btn_id == "list-sections-btn":
            self.action_list_sections()
        elif btn_id == "toggle-hex-btn":
            self.action_toggle_hex()
        elif btn_id == "config-btn":
            self.action_config()

    def on_path_input_path_changed(self, event: PathInput.PathChanged) -> None:
        section = self.query_one("#section-input", SectionInput).value.strip()
        if section:
            self.action_analyze()

    def on_section_input_section_selected(self, event: SectionInput.SectionSelected) -> None:
        path = self.query_one("#path-input", PathInput).value.strip()
        if path:
            self.action_analyze()

    def action_analyze(self) -> None:
        section = self.query_one("#section-input", SectionInput).value.strip()

        if not section:
            self.notify("Enter a section name (e.g. .text)", severity="warning")
            return

        if not self._analyzer:
            self.notify("No toolchain configured. Press 'c' to configure.", severity="error")
            return

        files = self._resolve_files()

        if not files:
            self.notify("No files found. Enter a path, glob pattern, or directory.", severity="warning")
            return

        self.notify(f"Analyzing {len(files)} files for section '{section}'...")
        self._do_analyze(files, section)

    def action_list_sections(self) -> None:
        if not self._analyzer:
            self.notify("No toolchain configured. Press 'c' to configure.", severity="error")
            return

        raw = self.query_one("#path-input", PathInput).value.strip()

        file_path = raw
        if not raw:
            self.notify("Enter a file path to list sections", severity="warning")
            return

        if any(c in raw for c in ("*", "?", "[")):
            matches = sorted(glob.glob(raw, recursive=True))
            if matches:
                file_path = matches[0]
            else:
                self.notify("No files matched glob pattern", severity="warning")
                return

        if not Path(file_path).exists():
            self.notify(f"File not found: {file_path}", severity="warning")
            return

        self.notify(f"Listing sections: {file_path}")
        self._do_list_sections(file_path)

    def action_toggle_hex(self) -> None:
        self.mode_hex = not self.mode_hex
        state = "Hex" if self.mode_hex else "Dec"
        self.notify(f"Display mode: {state}")
        if self._last_result:
            self._update_table(self._last_result)

    def action_config(self) -> None:
        self.push_screen(ConfigScreen(), self._on_config_closed)

    def _on_config_closed(self, result) -> None:
        self._init_analyzer()
        si = self.query_one("#section-input", SectionInput)
        si._load_sections()