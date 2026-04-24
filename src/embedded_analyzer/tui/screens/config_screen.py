"""
Configuration screen for managing toolchains.
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Input,
    Label,
    Static,
)

from embedded_analyzer.config import (
    load_config,
    add_toolchain,
    remove_toolchain,
    set_current_toolchain,
    get_default_config_path,
)


class ConfigScreen(ModalScreen):
    """Modal screen for toolchain configuration."""

    CSS = """
    ConfigScreen {
        align: center middle;
    }

    #config-dialog {
        width: 80;
        max-height: 32;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    DataTable {
        height: auto;
        max-height: 10;
        margin-bottom: 1;
    }

    #form-area {
        height: auto;
        margin-bottom: 1;
    }

    #form-area Input {
        margin-bottom: 0;
    }

    #form-area Label {
        text-style: bold;
    }

    #status {
        color: $text-muted;
        margin-top: 1;
    }

    .title-label {
        text-style: bold;
        margin-bottom: 1;
    }

    #btn-row {
        height: auto;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="config-dialog"):
            yield Label("Toolchain Configuration", classes="title-label")
            yield Label(f"Config file: {get_default_config_path()}", id="status")
            yield DataTable(id="config-list")
            with Vertical(id="form-area"):
                yield Label("Add Toolchain:")
                yield Input(placeholder="Name (e.g. riscv, arm)", id="tc-name")
                yield Input(placeholder="objdump path (required)", id="tc-objdump")
                yield Input(placeholder="size path (optional)", id="tc-size")
                yield Input(placeholder="readelf path (optional)", id="tc-readelf")
            with Horizontal(id="btn-row"):
                yield Button("Add", variant="success", id="add-btn")
                yield Button("Delete Selected", variant="error", id="del-btn")
                yield Button("Set Active", variant="primary", id="set-btn")
                yield Button("Close", variant="default", id="close-btn")

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        table = self.query_one("#config-list", DataTable)
        table.clear(columns=True)
        table.add_columns("Active", "Name", "objdump", "size", "readelf")
        config = load_config()
        for tc in config.toolchains:
            active = "\u2605" if tc.name == config.current_toolchain else ""
            table.add_row(active, tc.name, tc.objdump, tc.size or "-", tc.readelf or "-")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id == "add-btn":
            name = self.query_one("#tc-name", Input).value.strip()
            objdump = self.query_one("#tc-objdump", Input).value.strip()
            size = self.query_one("#tc-size", Input).value.strip() or None
            readelf_ = self.query_one("#tc-readelf", Input).value.strip() or None
            if not name or not objdump:
                self.notify("Name and objdump path are required", severity="warning")
                return
            try:
                add_toolchain(name, objdump, size, readelf_)
                self.notify(f"Added toolchain: {name}")
                self._refresh_list()
                for input_id in ("tc-name", "tc-objdump", "tc-size", "tc-readelf"):
                    self.query_one(f"#{input_id}", Input).value = ""
            except Exception as e:
                self.notify(f"Error: {e}", severity="error")

        elif btn_id == "del-btn":
            table = self.query_one("#config-list", DataTable)
            if table.cursor_row is not None and table.cursor_row >= 0:
                config = load_config()
                if table.cursor_row < len(config.toolchains):
                    name = config.toolchains[table.cursor_row].name
                    remove_toolchain(name)
                    self.notify(f"Removed: {name}")
                    self._refresh_list()

        elif btn_id == "set-btn":
            table = self.query_one("#config-list", DataTable)
            if table.cursor_row is not None and table.cursor_row >= 0:
                config = load_config()
                if table.cursor_row < len(config.toolchains):
                    name = config.toolchains[table.cursor_row].name
                    set_current_toolchain(name)
                    self.notify(f"Set active: {name}")
                    self._refresh_list()

        elif btn_id == "close-btn":
            self.action_close()

    def action_close(self) -> None:
        self.dismiss(None)