"""
Section name input — thin subclass of CompletionInput.

Special behavior:
- _get_completions(): loads section presets from config, shows all on empty
  input, filters on non-empty input
- Posts SectionSelected message on commit
- Public _load_sections() for app-level refresh after config changes
"""
from __future__ import annotations

from textual.message import Message

from .completion_input import CompletionInput


class SectionInput(CompletionInput):
    """Section name input with filtered preset suggestions from config."""

    _input_id = "section-inner-input"
    _options_id = "section-options"

    class SectionSelected(Message):
        def __init__(self, section: str) -> None:
            super().__init__()
            self.section = section

    def __init__(
        self,
        placeholder: str = "",
        id: str | None = None,
        sections: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(placeholder=placeholder, id=id, **kwargs)
        self._sections: list[str] = sections or []

    def _load_sections(self) -> None:
        if not self._sections:
            try:
                from embedded_analyzer.config import load_config
                cfg = load_config()
                self._sections = cfg.sections
            except Exception:
                from embedded_analyzer.core.models import DEFAULT_SECTIONS
                self._sections = list(DEFAULT_SECTIONS)

    # ------------------------------------------------------------------ completions
    def _get_completions(self, text: str) -> list[str]:
        self._load_sections()
        text_lower = text.strip().lower()

        if not text_lower:
            return list(self._sections)
        return [
            s for s in self._sections
            if text_lower in s.lower() or s.lower().startswith(text_lower)
        ]

    # ------------------------------------------------------------------ commit
    def _post_commit_message(self, value: str) -> None:
        self.post_message(self.SectionSelected(value))