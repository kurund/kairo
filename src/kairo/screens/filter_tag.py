"""Filter by tag screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label
from textual.screen import ModalScreen


class FilterTagScreen(ModalScreen[str]):
    """Modal screen for filtering tasks by tag."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    CSS = """
    FilterTagScreen {
        align: center middle;
    }

    #filter_dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #filter_dialog Label {
        margin: 1 0;
    }

    #filter_dialog Input {
        margin-bottom: 1;
    }

    #filter_dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #filter_dialog Button {
        margin: 0 1;
    }

    #tag_list {
        height: 10;
        margin: 1 0;
        border: solid $primary;
    }
    """

    def __init__(self, current_filter: str, available_tags: list[str]):
        self._current_filter = current_filter
        self._available_tags = available_tags
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the filter dialog."""
        with Vertical(id="filter_dialog"):
            yield Label("[bold]Filter Tasks by Tag[/bold]")

            if self._current_filter:
                yield Label(f"Current filter: [cyan]{self._current_filter}[/cyan]")
            else:
                yield Label("Current filter: [dim]None (showing all)[/dim]")

            yield Label("\nEnter tag name (or leave empty for all tasks):")
            yield Input(
                value=self._current_filter or "",
                placeholder="Enter tag name",
                id="tag_input",
            )

            if self._available_tags:
                yield Label(
                    f"\nAvailable tags: [cyan]{', '.join(sorted(self._available_tags))}[/cyan]"
                )

            with Horizontal():
                yield Button("Apply", variant="primary", id="apply_btn")
                yield Button("Clear", variant="warning", id="clear_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "apply_btn":
            tag_input = self.query_one("#tag_input", Input)
            self.dismiss(tag_input.value.strip())
        elif event.button.id == "clear_btn":
            self.dismiss("")
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(None)
