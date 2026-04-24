"""
Path/glob completion input — thin subclass of CompletionInput.

Special behavior:
- _get_completions(): filesystem path/glob autocomplete with **/*.o suffix suggestions
- _format_item(): prefix directories with 📂 for glob suggestions, append / for dirs
- key_tab(): falls back to cycling completion when no dropdown is shown
- Posts PathChanged message on commit
"""
from __future__ import annotations

import glob
import os
from pathlib import Path

from textual.message import Message
from textual.widgets import Input

from .completion_input import CompletionInput


_GLOB_SUFFIX = "/**/*.o"


class PathInput(CompletionInput):
    """Path/glob input with filesystem completion and **/*.o suggestions."""

    _input_id = "path-inner-input"
    _options_id = "path-options"

    class PathChanged(Message):
        def __init__(self, path: str) -> None:
            super().__init__()
            self.path = path

    @property
    def has_glob(self) -> bool:
        return any(c in self._value for c in ("*", "?", "["))

    # ------------------------------------------------------------------ completions
    def _get_completions(self, text: str) -> list[str]:
        if not text:
            return []

        is_glob = any(c in text for c in ("*", "?", "["))

        if is_glob:
            return sorted(glob.glob(text, recursive=True))[:50]

        path = Path(text)
        if text.endswith(os.sep) or (path.is_dir() and path.exists()):
            base = str(path)
            prefix = ""
        else:
            base = str(path.parent) if str(path.parent) != "." else "."
            prefix = path.name

        try:
            entries = sorted(os.listdir(base))
        except (OSError, FileNotFoundError):
            entries = []

        if prefix:
            matches = [e for e in entries if e.startswith(prefix)]
        else:
            matches = entries

        results = []
        seen = set()
        for m in matches:
            full = os.path.join(base, m)
            if os.path.isdir(full):
                full += os.sep
            results.append(full)
            seen.add(full)

        glob_suggestions = []
        if text.endswith(os.sep) or (path.is_dir() and path.exists()):
            dir_prefix = text.rstrip(os.sep)
            g = dir_prefix + _GLOB_SUFFIX
            if g not in seen:
                glob_suggestions.append(g)
                seen.add(g)
        else:
            for m in matches:
                full = os.path.join(base, m)
                if os.path.isdir(full):
                    g = full + _GLOB_SUFFIX
                    if g not in seen:
                        glob_suggestions.append(g)
                        seen.add(g)

            if base != "." or len(text) > 2:
                g = base.rstrip("/") + _GLOB_SUFFIX
                if g not in seen:
                    glob_suggestions.append(g)
                    seen.add(g)

        results = glob_suggestions + results
        return results[:50]

    def _format_item(self, item: str) -> str:
        if item.endswith(_GLOB_SUFFIX):
            return f"\U0001f4c2 {item}"
        if os.path.isdir(item) and not item.endswith(os.sep):
            return item + os.sep
        return item

    # ------------------------------------------------------------------ tab cycling fallback
    def key_tab(self, event) -> None:
        if self._items:
            idx = self._highlighted_index + 1
            if idx >= len(self._items):
                idx = 0
            self._accept(idx)
            event.stop()
            return
        if self._do_complete_cycling():
            event.stop()

    def _do_complete_cycling(self, direction: int = 1) -> bool:
        text = self._value
        completions = self._get_completions(text)
        if not completions:
            return False

        idx = -1 + direction
        if idx >= len(completions):
            idx = 0
        elif idx < 0:
            idx = len(completions) - 1

        self._value = completions[idx]
        inp = self.query_one(f"#{self._input_id}", Input)
        self._skip_next_change = True
        inp.value = self._value
        inp.cursor_position = len(self._value)
        return True

    # ------------------------------------------------------------------ commit
    def _post_commit_message(self, value: str) -> None:
        self.post_message(self.PathChanged(value))

    # ------------------------------------------------------------------ after accept
    def _after_accept(self, value: str) -> None:
        """After accepting a path completion, show next-level suggestions
        if the value is a directory. Hide dropdown for files/globs."""
        if self.has_glob:
            self._suppress_focus_show = True
            self._hide_dropdown()
            return
        if os.path.isdir(value) or value.endswith(os.sep):
            self._update_suggestions(value)
        else:
            self._suppress_focus_show = True
            self._hide_dropdown()