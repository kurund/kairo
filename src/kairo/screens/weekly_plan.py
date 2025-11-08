"""Weekly plan screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static
from textual.screen import ModalScreen

from ..models import Task, TaskStatus
from ..utils import format_week


class WeeklyPlanScreen(ModalScreen[None]):
    """Modal screen for viewing and copying weekly plan."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("ctrl+c", "copy", "Copy", show=False),
    ]

    CSS = """
    WeeklyPlanScreen {
        align: center middle;
    }

    #plan_dialog {
        width: 90;
        height: auto;
        max-height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #plan_content {
        height: auto;
        max-height: 70vh;
        overflow-y: auto;
        border: solid $accent;
        background: $panel;
        padding: 1;
        margin: 1 0;
    }

    #plan_dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #plan_dialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, tasks: list[Task], year: int, week: int):
        self._tasks = tasks
        self._year = year
        self._week = week
        self._plan_text = self._generate_plan_text()
        super().__init__()

    def _generate_plan_text(self) -> str:
        """Generate formatted plan text - simple list of planned tasks."""
        lines = []
        lines.append(f"Weekly Plan - Week {format_week(self._year, self._week)}")
        lines.append("=" * 60)
        lines.append("")

        # Calculate total estimate
        total_estimate = sum(t.estimate for t in self._tasks if t.estimate)

        lines.append(f"Total Tasks Planned: {len(self._tasks)}")
        if total_estimate > 0:
            lines.append(f"Total Estimated Hours: {total_estimate}h")
        lines.append("")

        # Group tasks by project
        projects = {}
        unassigned = []

        for task in self._tasks:
            if task.project:
                if task.project not in projects:
                    projects[task.project] = []
                projects[task.project].append(task)
            else:
                unassigned.append(task)

        # Display tasks by project
        if projects:
            for project, project_tasks in sorted(projects.items()):
                lines.append(f"{project}:")
                for task in project_tasks:
                    estimate_str = f" ({task.estimate}h)" if task.estimate else ""
                    tags_str = f" [{', '.join(task.tags)}]" if task.tags else ""
                    lines.append(f"  • {task.title}{estimate_str}{tags_str}")
                lines.append("")

        # Display unassigned tasks
        if unassigned:
            if projects:  # Only add header if we had projects
                lines.append("Other:")
            for task in unassigned:
                estimate_str = f" ({task.estimate}h)" if task.estimate else ""
                tags_str = f" [{', '.join(task.tags)}]" if task.tags else ""
                lines.append(f"  • {task.title}{estimate_str}{tags_str}")

        return "\n".join(lines)

    def compose(self) -> ComposeResult:
        """Compose the weekly plan dialog."""
        with Vertical(id="plan_dialog"):
            yield Static(
                f"[bold]Weekly Plan - Week {format_week(self._year, self._week)}[/bold]"
            )
            yield Static(
                "[dim]Copy this plan to share with your team (Ctrl+C to copy to clipboard)[/dim]"
            )
            with Vertical(id="plan_content"):
                yield Static(self._plan_text, id="plan_text")
            with Horizontal():
                yield Button("Copy to Clipboard", variant="primary", id="copy_btn")
                yield Button("Close", variant="default", id="close_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "copy_btn":
            self.action_copy()
        else:
            self.dismiss()

    def action_copy(self) -> None:
        """Copy plan to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(self._plan_text)
            self.notify("Weekly plan copied to clipboard!")
        except ImportError:
            # Fallback if pyperclip is not available
            self.notify(
                "Could not copy to clipboard. Please install pyperclip: pip install pyperclip",
                severity="warning",
            )
        except Exception as e:
            self.notify(
                f"Error copying to clipboard: {str(e)}", severity="error"
            )

    def action_close(self) -> None:
        """Close the dialog."""
        self.dismiss()
