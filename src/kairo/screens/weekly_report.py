"""Weekly report screen for Kairo TUI."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static
from textual.screen import ModalScreen

from ..models import Task, TaskStatus
from ..utils import format_week


class WeeklyReportScreen(ModalScreen[None]):
    """Modal screen for viewing comprehensive weekly report."""

    BINDINGS = [
        Binding("escape", "close", "Close", show=False),
        Binding("ctrl+c", "copy", "Copy", show=False),
    ]

    CSS = """
    WeeklyReportScreen {
        align: center middle;
    }

    #report_dialog {
        width: 90;
        height: auto;
        max-height: 90%;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }

    #report_content {
        height: auto;
        max-height: 70vh;
        overflow-y: auto;
        border: solid $accent;
        background: $panel;
        padding: 1;
        margin: 1 0;
    }

    #report_dialog Horizontal {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    #report_dialog Button {
        margin: 0 1;
    }
    """

    def __init__(self, tasks: list[Task], year: int, week: int):
        self._tasks = tasks
        self._year = year
        self._week = week
        self._report_text = self._generate_report_text()
        super().__init__()

    def _generate_report_text(self) -> str:
        """Generate formatted report text with planned vs done analysis."""
        lines = []
        lines.append(f"Weekly Report - Week {format_week(self._year, self._week)}")
        lines.append("=" * 60)
        lines.append("")

        # Group tasks by status
        open_tasks = [t for t in self._tasks if t.status == TaskStatus.OPEN]
        completed_tasks = [t for t in self._tasks if t.status == TaskStatus.COMPLETED]

        # Calculate estimates
        total_estimate = sum(t.estimate for t in self._tasks if t.estimate)
        completed_estimate = sum(
            t.estimate for t in completed_tasks if t.estimate
        )
        open_estimate = sum(t.estimate for t in open_tasks if t.estimate)

        # SUMMARY SECTION
        lines.append("📊 SUMMARY")
        lines.append("-" * 60)
        lines.append(f"Total Tasks Planned: {len(self._tasks)}")
        lines.append(f"✓ Completed: {len(completed_tasks)}")
        lines.append(f"○ Open/In Progress: {len(open_tasks)}")

        if len(self._tasks) > 0:
            completion_rate = (len(completed_tasks) / len(self._tasks)) * 100
            lines.append(f"Completion Rate: {completion_rate:.0f}%")

        if total_estimate > 0:
            lines.append(f"\nTotal Hours Planned: {total_estimate}h")
            lines.append(f"✓ Hours Completed: {completed_estimate}h")
            lines.append(f"○ Hours Remaining: {open_estimate}h")
            if total_estimate > 0:
                time_completion = (completed_estimate / total_estimate) * 100
                lines.append(f"Time Completion Rate: {time_completion:.0f}%")

        lines.append("")

        # COMPLETED TASKS SECTION
        if completed_tasks:
            lines.append("✅ COMPLETED TASKS")
            lines.append("-" * 60)

            # Group completed by project
            completed_by_project = {}
            completed_unassigned = []

            for task in completed_tasks:
                if task.project:
                    if task.project not in completed_by_project:
                        completed_by_project[task.project] = []
                    completed_by_project[task.project].append(task)
                else:
                    completed_unassigned.append(task)

            # Display completed by project
            if completed_by_project:
                for project, project_tasks in sorted(completed_by_project.items()):
                    lines.append(f"\n{project}:")
                    for task in project_tasks:
                        estimate_str = f" ({task.estimate}h)" if task.estimate else ""
                        tags_str = f" [{', '.join(task.tags)}]" if task.tags else ""
                        lines.append(f"  ✓ {task.title}{estimate_str}{tags_str}")

            # Display completed unassigned
            if completed_unassigned:
                if completed_by_project:
                    lines.append("\nOther:")
                for task in completed_unassigned:
                    estimate_str = f" ({task.estimate}h)" if task.estimate else ""
                    tags_str = f" [{', '.join(task.tags)}]" if task.tags else ""
                    lines.append(f"  ✓ {task.title}{estimate_str}{tags_str}")

            lines.append("")

        # OPEN/IN PROGRESS TASKS SECTION
        if open_tasks:
            lines.append("📝 OPEN/IN PROGRESS")
            lines.append("-" * 60)

            # Group open by project
            open_by_project = {}
            open_unassigned = []

            for task in open_tasks:
                if task.project:
                    if task.project not in open_by_project:
                        open_by_project[task.project] = []
                    open_by_project[task.project].append(task)
                else:
                    open_unassigned.append(task)

            # Display open by project
            if open_by_project:
                for project, project_tasks in sorted(open_by_project.items()):
                    lines.append(f"\n{project}:")
                    for task in project_tasks:
                        estimate_str = f" ({task.estimate}h)" if task.estimate else ""
                        tags_str = f" [{', '.join(task.tags)}]" if task.tags else ""
                        lines.append(f"  ○ {task.title}{estimate_str}{tags_str}")

            # Display open unassigned
            if open_unassigned:
                if open_by_project:
                    lines.append("\nOther:")
                for task in open_unassigned:
                    estimate_str = f" ({task.estimate}h)" if task.estimate else ""
                    tags_str = f" [{', '.join(task.tags)}]" if task.tags else ""
                    lines.append(f"  ○ {task.title}{estimate_str}{tags_str}")

            lines.append("")

        # KEY ACHIEVEMENTS (if any completed tasks)
        if completed_tasks:
            lines.append("🎯 KEY ACHIEVEMENTS")
            lines.append("-" * 60)
            for task in completed_tasks[:5]:  # Show top 5 completed
                estimate_str = f" ({task.estimate}h)" if task.estimate else ""
                lines.append(f"• {task.title}{estimate_str}")
            if len(completed_tasks) > 5:
                lines.append(f"... and {len(completed_tasks) - 5} more")
            lines.append("")

        # NEXT WEEK PRIORITIES (carry-forward open tasks)
        if open_tasks:
            lines.append("⏭️  CARRY FORWARD TO NEXT WEEK")
            lines.append("-" * 60)
            for task in open_tasks[:5]:  # Show top 5 open
                estimate_str = f" ({task.estimate}h)" if task.estimate else ""
                lines.append(f"• {task.title}{estimate_str}")
            if len(open_tasks) > 5:
                lines.append(f"... and {len(open_tasks) - 5} more")

        return "\n".join(lines)

    def compose(self) -> ComposeResult:
        """Compose the weekly report dialog."""
        with Vertical(id="report_dialog"):
            yield Static(
                f"[bold]Weekly Report - Week {format_week(self._year, self._week)}[/bold]"
            )
            yield Static(
                "[dim]Comprehensive report of planned vs completed tasks (Ctrl+C to copy)[/dim]"
            )
            with Vertical(id="report_content"):
                yield Static(self._report_text, id="report_text")
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
        """Copy report to clipboard."""
        try:
            import pyperclip
            pyperclip.copy(self._report_text)
            self.notify("Weekly report copied to clipboard!")
        except ImportError:
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
