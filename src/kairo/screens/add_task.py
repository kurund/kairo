"""Add task screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, TextArea
from textual.screen import ModalScreen

from ..database import Database
from ..utils import format_week


class AddTaskScreen(ModalScreen[bool]):
    """Modal screen for adding a new task."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+s", "save", "Save", show=False),
    ]

    CSS = """
    AddTaskScreen {
        align: center middle;
    }

    #add_dialog {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #add_dialog Label {
        margin: 1 0;
    }

    #add_dialog Input {
        margin-bottom: 1;
    }

    #add_dialog TextArea {
        height: 5;
        margin-bottom: 1;
    }

    #add_dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #add_dialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, year: int, week: int):
        super().__init__()
        self.year = year
        self.week = week

    def compose(self) -> ComposeResult:
        """Compose the add task dialog."""
        with Vertical(id="add_dialog"):
            yield Label(
                f"[bold]Add New Task - Week {format_week(self.year, self.week)}[/bold]"
            )
            yield Label("Title:")
            yield Input(placeholder="Enter task title", id="title_input")
            yield Label("Description (optional):")
            yield TextArea(id="desc_input")
            yield Label("Tags (comma-separated, e.g., work,urgent):")
            yield Input(placeholder="work, personal", id="tags_input")
            with Horizontal():
                yield Button("Add", variant="primary", id="add_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    def _save_task(self) -> None:
        """Save the task."""
        title_input = self.query_one("#title_input", Input)
        desc_input = self.query_one("#desc_input", TextArea)
        tags_input = self.query_one("#tags_input", Input)

        if title_input.value.strip():
            # Parse tags from comma-separated input
            tag_list = [
                tag.strip() for tag in tags_input.value.split(",") if tag.strip()
            ]

            db = Database()
            try:
                db.add_task(
                    title=title_input.value.strip(),
                    description=desc_input.text.strip(),
                    week=self.week,
                    year=self.year,
                    tags=tag_list,
                )
                self.dismiss(True)
            finally:
                db.close()
        else:
            title_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add_btn":
            self._save_task()
        else:
            self.dismiss(False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in title input."""
        if event.input.id == "title_input":
            # Move focus to description
            desc_input = self.query_one("#desc_input", TextArea)
            desc_input.focus()

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)

    def action_save(self) -> None:
        """Save the task (Ctrl+S shortcut)."""
        self._save_task()
