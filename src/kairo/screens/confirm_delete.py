"""Confirm delete screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label
from textual.screen import ModalScreen

from ..models import Task


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Modal screen for confirming task deletion."""

    CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }

    #confirm_dialog {
        width: 60;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }

    #confirm_dialog Label {
        margin: 1 0;
    }

    #confirm_dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #confirm_dialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, task: Task):
        self._task_data = task
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Vertical(id="confirm_dialog"):
            yield Label("[bold red]Delete Task?[/bold red]")
            yield Label(f"\n[bold]{self._task_data.title}[/bold]")
            yield Label("\nThis action cannot be undone.")
            with Horizontal():
                yield Button("Delete", variant="error", id="delete_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "delete_btn":
            self.dismiss(True)
        else:
            self.dismiss(False)
