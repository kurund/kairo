"""Edit task screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Checkbox, Input, Label, TextArea
from textual.screen import ModalScreen

from ..database import Database
from ..models import Task
from ..utils import get_current_week


class EditTaskScreen(ModalScreen[bool]):
    """Modal screen for editing a task."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+s", "save", "Save", show=False),
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
        # Check if task is currently scheduled
        is_scheduled = self._task_data.week is not None and self._task_data.year is not None

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
            yield Label("Project (optional):")
            yield Input(
                value=self._task_data.project if self._task_data.project else "",
                placeholder="e.g., Website Redesign",
                id="project_input",
            )
            yield Label("Estimate (hours, optional):")
            yield Input(
                value=str(self._task_data.estimate) if self._task_data.estimate else "",
                placeholder="e.g., 2",
                id="estimate_input",
                type="integer",
            )
            yield Checkbox("Scheduled (uncheck to move to Inbox)", value=is_scheduled, id="schedule_checkbox")
            with Horizontal():
                yield Button("Save", variant="primary", id="save_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    def _save_task(self) -> None:
        """Save the task changes."""
        title_input = self.query_one("#title_input", Input)
        desc_input = self.query_one("#desc_input", TextArea)
        tags_input = self.query_one("#tags_input", Input)
        project_input = self.query_one("#project_input", Input)
        estimate_input = self.query_one("#estimate_input", Input)
        schedule_checkbox = self.query_one("#schedule_checkbox", Checkbox)

        if title_input.value.strip():
            # Parse tags from comma-separated input
            tag_list = [
                tag.strip() for tag in tags_input.value.split(",") if tag.strip()
            ]

            # Get project value
            project = project_input.value.strip() if project_input.value.strip() else None

            # Parse estimate (convert to int if provided)
            estimate = None
            if estimate_input.value.strip():
                try:
                    estimate = int(estimate_input.value.strip())
                except ValueError:
                    pass  # Ignore invalid input

            # Determine week/year based on schedule checkbox
            if schedule_checkbox.value:
                # Schedule to current week if moving from inbox
                if self._task_data.week is None or self._task_data.year is None:
                    year, week = get_current_week()
                else:
                    # Keep existing schedule
                    week = self._task_data.week
                    year = self._task_data.year
            else:
                # Move to inbox (unschedule)
                week = None
                year = None

            db = Database()
            try:
                db.update_task(
                    self._task_data.id,
                    title=title_input.value.strip(),
                    description=desc_input.text.strip(),
                    tags=tag_list,
                    estimate=estimate,
                    project=project,
                    week=week,
                    year=year,
                )
                self.dismiss(True)
            finally:
                db.close()
        else:
            title_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save_btn":
            self._save_task()
        else:
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Cancel and close the dialog."""
        self.dismiss(False)

    def action_save(self) -> None:
        """Save the task (Ctrl+S shortcut)."""
        self._save_task()
