"""Edit task screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, Label, TextArea
from textual.screen import ModalScreen

from ..database import Database
from ..models import Task


class EditTaskScreen(ModalScreen[bool]):
    """Modal screen for editing a task."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    CSS = """
    EditTaskScreen {
        align: center middle;
    }

    #edit_dialog {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #edit_dialog Label {
        margin: 1 0;
    }

    #edit_dialog Input {
        margin-bottom: 1;
    }

    #edit_dialog TextArea {
        height: 5;
        margin-bottom: 1;
    }

    #edit_dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #edit_dialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, task: Task):
        self._task_data = task
        super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the edit task dialog."""
        with Vertical(id="edit_dialog"):
            yield Label(f"[bold]Edit Task - {self._task_data.id}[/bold]")
            yield Label("Title:")
            yield Input(
                value=self._task_data.title,
                placeholder="Enter task title",
                id="title_input",
            )
            yield Label("Description:")
            yield TextArea(self._task_data.description or "", id="desc_input")
            yield Label("Tags (comma-separated):")
            yield Input(
                value=", ".join(self._task_data.tags) if self._task_data.tags else "",
                placeholder="work, personal",
                id="tags_input",
            )
            with Horizontal():
                yield Button("Save", variant="primary", id="save_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save_btn":
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
                    db.update_task(
                        self._task_data.id,
                        title=title_input.value.strip(),
                        description=desc_input.text.strip(),
                        tags=tag_list,
                    )
                    self.dismiss(True)
                finally:
                    db.close()
            else:
                title_input.focus()
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)
