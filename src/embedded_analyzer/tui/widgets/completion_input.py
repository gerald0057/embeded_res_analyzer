"""
Base class for input widgets with inline completion/suggestion dropdown.

Architecture:
- Composes an Input + OptionList inside a vertical layout
- Suggestions are only visible when the widget has focus AND there are items
- on_focus: show suggestions for current text
- on_blur: hide suggestions immediately
- Escape: hide suggestions
- Accept (Tab/Enter on highlighted): set value, hide suggestions
- Commit (Enter with no highlight): hide suggestions, post message
- Subclasses override _get_completions(), _format_item(), _post_commit_message()
"""
from __future__ import annotations

from textual.app import ComposeResult
from textual.events import DescendantBlur, DescendantFocus
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option


class _BlurGuard:
    """Prevents dropdown hide on blur when the user is clicking an option.

    When the user mouse-clicks an OptionList item, the Input loses focus
    (blur fires) *before* OptionSelected fires. If we hide the dropdown
    immediately on blur, the option click is lost.

    Solution: set a flag when an option is selected. Blur handlers check
    this flag and skip the hide if set. The flag is cleared after all
    blur events have been processed.
    """
    __slots__ = ("_active",)

    def __init__(self):
        self._active = False

    def set_guard(self) -> None:
        self._active = True

    @property
    def active(self) -> bool:
        return self._active

    def clear(self) -> None:
        self._active = False


class CompletionInput(Widget):
    """Input with inline suggestion list — show on focus, hide on blur."""

    DEFAULT_CSS = """
    CompletionInput {
        layout: vertical;
        height: auto;
    }

    CompletionInput > Input {
        width: 100%;
    }

    CompletionInput > OptionList {
        width: 100%;
        max-height: 6;
        display: none;
        background: $surface;
        border: tall $primary;
        padding: 0;
        margin-top: 0;
    }
    """

    _input_id: str = "ci-inner-input"
    _options_id: str = "ci-options"

    def __init__(self, placeholder: str = "", id: str | None = None, **kwargs):
        super().__init__(id=id, **kwargs)
        self._placeholder = placeholder
        self._value: str = ""
        self._items: list[str] = []
        self._highlighted_index: int = -1
        self._skip_next_change: bool = False
        self._blur_guard = _BlurGuard()
        self._suppress_focus_show: bool = False

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, val: str) -> None:
        self._value = val
        try:
            inp = self.query_one(f"#{self._input_id}", Input)
            self._skip_next_change = True
            inp.value = val
            inp.cursor_position = len(val)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        yield Input(placeholder=self._placeholder, id=self._input_id)
        yield OptionList(id=self._options_id)

    # ------------------------------------------------------------------ lifecycle
    def on_mount(self) -> None:
        self._hide_dropdown()

    def _on_input_focus(self) -> None:
        """Called when the inner Input gets focus. Show suggestions."""
        if self._suppress_focus_show:
            self._suppress_focus_show = False
            return
        self._update_suggestions(self._value)

    def _on_input_blur(self) -> None:
        """Called when the inner Input loses focus. Hide suggestions."""
        self._hide_dropdown()

    # ------------------------------------------------------------------ input events
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != self._input_id:
            return
        if self._skip_next_change:
            self._skip_next_change = False
            self._value = event.value
            return
        self._value = event.value
        self._update_suggestions(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != self._input_id:
            return
        if self._items and self._highlighted_index >= 0:
            self._accept(self._highlighted_index)
            event.stop()
            return
        if self._value.strip():
            self._hide_dropdown()
            self._post_commit_message(self._value.strip())

    # ------------------------------------------------------------------ focus/blur
    # Textual routes DOM focus to the inner Input widget. The compound widget
    # receives DescendantFocus / DescendantBlur when any descendant gains/loses
    # focus. We also watch Input.Blurred as a safety net for blur.
    def on_descendant_focus(self, event: DescendantFocus) -> None:
        if getattr(event.widget, "id", None) == self._input_id:
            self._on_input_focus()

    def on_descendant_blur(self, event: DescendantBlur) -> None:
        if getattr(event.widget, "id", None) == self._input_id:
            if self._blur_guard.active:
                self._blur_guard.clear()
                return
            self._on_input_blur()

    def on_input_blurred(self, event: Input.Blurred) -> None:
        if event.input.id == self._input_id:
            if self._blur_guard.active:
                self._blur_guard.clear()
                return
            self._on_input_blur()

    # ------------------------------------------------------------------ keyboard
    def key_tab(self, event) -> None:
        if self._items:
            idx = self._highlighted_index + 1
            if idx >= len(self._items):
                idx = 0
            self._accept(idx)
            event.stop()

    def key_down(self, event) -> None:
        if self._items:
            idx = self._highlighted_index + 1
            if idx >= len(self._items):
                idx = 0
            self._highlight(idx)
            event.stop()

    def key_up(self, event) -> None:
        if self._items:
            idx = self._highlighted_index - 1
            if idx < 0:
                idx = len(self._items) - 1
            self._highlight(idx)
            event.stop()

    def key_escape(self, event) -> None:
        self._hide_dropdown()
        event.stop()

    # ------------------------------------------------------------------ option list
    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_list.id == self._options_id:
            idx = event.option_index
            if idx is not None and 0 <= idx < len(self._items):
                self._blur_guard.set_guard()
                self._accept(idx)

    # ------------------------------------------------------------------ core show/hide
    def _update_suggestions(self, text: str) -> None:
        items = self._get_completions(text)
        self._items = items
        self._highlighted_index = -1

        ol = self.query_one(f"#{self._options_id}", OptionList)
        ol.clear_options()
        if items:
            for item in items:
                display = self._format_item(item)
                ol.add_option(Option(display, id=f"{self._options_id}-{item}"))
            ol.display = True
        else:
            ol.display = False

    def _hide_dropdown(self) -> None:
        self._items = []
        self._highlighted_index = -1
        try:
            ol = self.query_one(f"#{self._options_id}", OptionList)
            ol.clear_options()
            ol.display = False
        except Exception:
            pass

    def _highlight(self, idx: int) -> None:
        self._highlighted_index = idx
        ol = self.query_one(f"#{self._options_id}", OptionList)
        if 0 <= idx < len(self._items):
            ol.highlighted = idx

    def _accept(self, idx: int) -> None:
        if 0 <= idx < len(self._items):
            self._value = self._items[idx]
            inp = self.query_one(f"#{self._input_id}", Input)
            self._skip_next_change = True
            inp.value = self._value
            inp.cursor_position = len(self._value)
            self._after_accept(self._value)
            inp.focus()

    # ------------------------------------------------------------------ subclass hooks
    def _get_completions(self, text: str) -> list[str]:
        """Return completion items for the given input text."""
        raise NotImplementedError

    def _format_item(self, item: str) -> str:
        """Return display string for a completion item."""
        return item

    def _post_commit_message(self, value: str) -> None:
        """Post a widget-specific message when the user commits (Enter)."""
        pass

    def _after_accept(self, value: str) -> None:
        """Called after a completion is accepted. Default: hide dropdown.

        Subclasses can override to show next-level suggestions instead.
        If this method does NOT show the dropdown, set _suppress_focus_show
        so the re-focus doesn't immediately re-show suggestions.
        """
        self._suppress_focus_show = True
        self._hide_dropdown()

    def focus(self, scroll_visible: bool = True):
        try:
            self.query_one(f"#{self._input_id}", Input).focus()
        except Exception:
            pass
        return self