"""Modal dialogs for text input and dependent-choice selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Select


class InputDialog(ModalScreen[str | None]):
    """A modal that prompts for a single text value.

    Returns the entered string, or None if cancelled.
    """

    DEFAULT_CSS = """
    InputDialog {
        align: center middle;
    }
    InputDialog > Vertical {
        width: 50;
        height: auto;
        max-height: 10;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    InputDialog Label {
        margin-bottom: 1;
    }
    """

    def __init__(self, prompt: str, placeholder: str = "") -> None:
        super().__init__()
        self._prompt = prompt
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self._prompt)
            yield Input(placeholder=self._placeholder, id="dialog-input")

    def on_mount(self) -> None:
        self.query_one("#dialog-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        self.dismiss(value if value else None)

    def key_escape(self) -> None:
        self.dismiss(None)


class SelectDialog(ModalScreen[tuple[str, str | None] | None]):
    """A modal with a dependent choice list: name → version.

    Returns (name, version) tuple on submit, or None if cancelled.
    The version may be None if no versions are available or "any" is chosen.
    """

    DEFAULT_CSS = """
    SelectDialog {
        align: center middle;
    }
    SelectDialog > Vertical {
        width: 60;
        height: auto;
        max-height: 16;
        border: thick $accent;
        background: $surface;
        padding: 1 2;
    }
    SelectDialog Label {
        margin-bottom: 1;
    }
    SelectDialog Select {
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        title: str,
        choices: dict[str, list[str]],
        name_prompt: str = "Name",
        version_prompt: str = "Version",
    ) -> None:
        """Create a dependent-choice dialog.

        Args:
            title: Dialog title label.
            choices: Mapping of name → list of versions.
                     Empty list means no version selection needed.
        """
        super().__init__()
        self._title = title
        self._choices = choices
        self._name_prompt = name_prompt
        self._version_prompt = version_prompt
        self._selected_name: str | None = None

    def compose(self) -> ComposeResult:
        names = sorted(self._choices.keys())
        with Vertical():
            yield Label(self._title)
            yield Label(self._name_prompt)
            yield Select[str](
                options=[(n, n) for n in names],
                allow_blank=True,
                id="select-name",
                prompt="Choose...",
            )
            yield Label(self._version_prompt)
            yield Select[str](
                options=[],
                allow_blank=True,
                id="select-version",
                prompt="Any version",
            )

    def on_mount(self) -> None:
        self.query_one("#select-name", Select).focus()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "select-name":
            if event.value == Select.BLANK:
                self._selected_name = None
                version_select = self.query_one("#select-version", Select)
                version_select.set_options([])
            else:
                self._selected_name = str(event.value)
                versions = self._choices.get(self._selected_name, [])
                version_select = self.query_one("#select-version", Select)
                version_select.set_options([(v, v) for v in sorted(versions)])

    def key_enter(self) -> None:
        if self._selected_name:
            version_select = self.query_one("#select-version", Select)
            version = (
                str(version_select.value)
                if version_select.value != Select.BLANK
                else None
            )
            self.dismiss((self._selected_name, version))

    def key_escape(self) -> None:
        self.dismiss(None)
