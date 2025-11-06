"""Task detail screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label
from textual.screen import ModalScreen

from ..models import Task, TaskStatus
from ..utils import format_week


class TaskDetailScreen(ModalScreen[None]):
    """Modal screen for viewing task details."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
    ]

    CSS = """
    TaskDetailScreen {
        align: center middle;
    }

    #detail_dialog {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #detail_dialog Label {
        margin: 1 0;
    }

    #detail_dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #detail_dialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, task: Task):
        self._task_data = task
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the task detail dialog."""
        with Vertical(id="detail_dialog"):
            yield Label(f"[bold]{self._task_data.title}[/bold]")
            yield Label(f"[dim]ID: {self._task_data.id}[/dim]")
            yield Label(
                f"Status: {'✓ Completed' if self._task_data.status == TaskStatus.COMPLETED else '○ Open'}"
            )
            yield Label(
                f"Week: {format_week(self._task_data.year, self._task_data.week)}"
            )
            if self._task_data.estimate:
                yield Label(f"Estimate: {self._task_data.estimate} hours")
            yield Label(
                f"Created: {self._task_data.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
            if self._task_data.completed_at:
                yield Label(
                    f"Completed: {self._task_data.completed_at.strftime('%Y-%m-%d %H:%M')}"
                )
            if self._task_data.tags:
                yield Label(f"Tags: [cyan]{', '.join(self._task_data.tags)}[/cyan]")
            if self._task_data.description:
                yield Label(f"\nDescription:\n{self._task_data.description}")
            with Horizontal():
                yield Button("Close", variant="primary", id="close_btn")

    def on_button_pressed(self, _event: Button.Pressed) -> None:
        """Handle button press."""
        self.dismiss()

    def action_close(self) -> None:
        """Close the dialog."""
        self.dismiss()
