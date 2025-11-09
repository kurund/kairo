"""Unified task form screen for adding and editing tasks."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, TextArea

from ..database import Database
from ..models import Task
from ..utils import format_week, get_current_week


class TaskFormScreen(ModalScreen[bool]):
    """Modal screen for adding or editing a task."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("ctrl+s", "save", "Save", show=False),
    ]

    CSS = """
    TaskFormScreen {
        align: center middle;
    }

    #task_dialog {
        width: 90;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }

    #task_dialog > Label {
        margin-bottom: 0;
    }

    #task_dialog Label {
        margin: 0;
        padding: 0;
    }

    #task_dialog Input {
        margin: 0;
        height: 3;
    }

    #task_dialog TextArea {
        height: 2;
        margin: 0;
    }

    #task_dialog .field-row {
        height: auto;
        margin-bottom: 1;
    }

    #task_dialog .two-col {
        width: 1fr;
        height: auto;
    }

    #task_dialog .two-col Label {
        height: 1;
    }

    #task_dialog .two-col:last-child {
        margin-left: 1;
    }

    #task_dialog .button-row {
        height: 3;
        align: center middle;
        margin-top: 0;
    }

    #task_dialog Button {
        margin: 0 1;
        min-width: 12;
        height: 3;
    }

    #task_dialog Checkbox {
        margin: 0;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        year: int,
        week: int,
        task: Task | None = None,
        default_tag: str = "",
        default_project: str = "",
    ):
        """Initialize task form.

        Args:
            year: Current year
            week: Current week
            task: Task to edit (None for new task)
            default_tag: Default tag value
            default_project: Default project value
        """
        super().__init__()
        self.year = year
        self.week = week
        self._task_data = task
        self.is_edit = task is not None
        self.default_tag = default_tag
        self.default_project = default_project

    def compose(self) -> ComposeResult:
        """Compose the task form dialog."""
        # Determine values based on edit mode
        if self.is_edit:
            title_text = f"[bold]Edit Task - {self._task_data.id}[/bold]"
            title_value = self._task_data.title
            desc_value = self._task_data.description or ""
            tags_value = ", ".join(self._task_data.tags) if self._task_data.tags else ""
            project_value = self._task_data.project if self._task_data.project else ""
            estimate_value = (
                str(self._task_data.estimate) if self._task_data.estimate else ""
            )
            is_scheduled = (
                self._task_data.week is not None and self._task_data.year is not None
            )
            button_text = "Save"
            checkbox_label = "Scheduled (uncheck for Inbox)"
        else:
            title_text = (
                f"[bold]Add New Task - Week {format_week(self.year, self.week)}[/bold]"
            )
            title_value = ""
            desc_value = ""
            tags_value = self.default_tag
            project_value = self.default_project
            estimate_value = ""
            is_scheduled = True
            button_text = "Add"
            checkbox_label = "Schedule for this week"

        with Vertical(id="task_dialog"):
            yield Label(title_text)

            # Title field
            with Vertical(classes="field-row"):
                yield Label("Title:")
                yield Input(
                    value=title_value,
                    placeholder="Enter task title",
                    id="title_input",
                )

            # Description field (compact)
            with Vertical(classes="field-row"):
                yield Label("Description:")
                yield TextArea(desc_value, id="desc_input")

            # Tags and Project on same row
            with Horizontal(classes="field-row"):
                with Vertical(classes="two-col"):
                    yield Label("Tags:")
                    yield Input(
                        value=tags_value,
                        placeholder="work, urgent",
                        id="tags_input",
                    )
                with Vertical(classes="two-col"):
                    yield Label("Project:")
                    yield Input(
                        value=project_value,
                        placeholder="Website Redesign",
                        id="project_input",
                    )

            # Estimate and Schedule on same row
            with Horizontal(classes="field-row"):
                with Vertical(classes="two-col"):
                    yield Label("Estimate (hours):")
                    yield Input(
                        value=estimate_value,
                        placeholder="2",
                        id="estimate_input",
                        type="integer",
                    )
                with Vertical(classes="two-col"):
                    yield Checkbox(
                        checkbox_label, value=is_scheduled, id="schedule_checkbox"
                    )

            # Buttons
            with Horizontal(classes="button-row"):
                yield Button(button_text, variant="primary", id="save_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    def _save_task(self) -> None:
        """Save the task (add or update)."""
        title_input = self.query_one("#title_input", Input)
        desc_input = self.query_one("#desc_input", TextArea)
        tags_input = self.query_one("#tags_input", Input)
        project_input = self.query_one("#project_input", Input)
        estimate_input = self.query_one("#estimate_input", Input)
        schedule_checkbox = self.query_one("#schedule_checkbox", Checkbox)

        if not title_input.value.strip():
            title_input.focus()
            return

        # Parse tags from comma-separated input
        tag_list = [tag.strip() for tag in tags_input.value.split(",") if tag.strip()]

        # Get project value
        project = project_input.value.strip() if project_input.value.strip() else None

        # Parse estimate (convert to int if provided)
        estimate = None
        if estimate_input.value.strip():
            try:
                estimate = int(estimate_input.value.strip())
            except ValueError:
                pass  # Ignore invalid input

        db = Database()
        try:
            if self.is_edit:
                # Update existing task
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
            else:
                # Add new task
                db.add_task(
                    title=title_input.value.strip(),
                    description=desc_input.text.strip(),
                    week=self.week,
                    year=self.year,
                    tags=tag_list,
                    estimate=estimate,
                    project=project,
                    schedule=schedule_checkbox.value,
                )

            self.dismiss(True)
        finally:
            db.close()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save_btn":
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
