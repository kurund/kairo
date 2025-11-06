"""Interactive TUI for Kairo task management."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    Static,
    Button,
    Input,
    TextArea,
    Label,
)
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.reactive import reactive

from .database import Database
from .models import Task, TaskStatus
from .utils import get_current_week, format_week, get_next_week


class AddTaskScreen(ModalScreen[bool]):
    """Modal screen for adding a new task."""

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
            with Horizontal():
                yield Button("Add", variant="primary", id="add_btn")
                yield Button("Cancel", variant="default", id="cancel_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add_btn":
            title_input = self.query_one("#title_input", Input)
            desc_input = self.query_one("#desc_input", TextArea)

            if title_input.value.strip():
                db = Database()
                try:
                    db.add_task(
                        title=title_input.value.strip(),
                        description=desc_input.text.strip(),
                        week=self.week,
                        year=self.year,
                    )
                    self.dismiss(True)
                finally:
                    db.close()
            else:
                title_input.focus()
        else:
            self.dismiss(False)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in title input."""
        if event.input.id == "title_input":
            # Move focus to description
            desc_input = self.query_one("#desc_input", TextArea)
            desc_input.focus()


class TaskDetailScreen(ModalScreen[None]):
    """Modal screen for viewing task details."""

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
            yield Label(f"Week: {format_week(self._task_data.year, self._task_data.week)}")
            yield Label(f"Created: {self._task_data.created_at.strftime('%Y-%m-%d %H:%M')}")
            if self._task_data.completed_at:
                yield Label(
                    f"Completed: {self._task_data.completed_at.strftime('%Y-%m-%d %H:%M')}"
                )
            if self._task_data.description:
                yield Label(f"\nDescription:\n{self._task_data.description}")
            with Horizontal():
                yield Button("Close", variant="primary", id="close_btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        self.dismiss()


class KairoApp(App):
    """Main Kairo TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #status_bar {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        content-align: center middle;
    }

    #main_container {
        height: 1fr;
        layout: horizontal;
    }

    #left_panel {
        width: 30%;
        border-right: solid $primary;
        padding: 1;
    }

    #right_panel {
        width: 70%;
        padding: 1;
    }

    #stats_container {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    #nav_container {
        height: auto;
        margin-bottom: 1;
    }

    #nav_container Horizontal {
        height: auto;
        align: center middle;
    }

    #nav_container Button {
        margin: 0 1;
        min-width: 12;
    }

    #actions_container {
        height: auto;
        border: solid $primary;
        padding: 1;
    }

    #actions_container Button {
        width: 100%;
        margin-bottom: 1;
    }

    DataTable {
        height: 100%;
    }

    .stat_label {
        margin: 0 0 1 0;
    }
    """

    BINDINGS = [
        Binding("a", "add_task", "Add Task", key_display="A"),
        Binding("c", "complete_task", "Complete", key_display="C"),
        Binding("d", "show_details", "Details", key_display="D"),
        Binding("r", "refresh", "Refresh", key_display="R"),
        Binding("left", "prev_week", "Prev Week", key_display="←"),
        Binding("right", "next_week", "Next Week", key_display="→"),
        Binding("q", "quit", "Quit", key_display="Q"),
    ]

    current_year = reactive(0)
    current_week = reactive(0)

    def __init__(self):
        super().__init__()
        self.db = Database()

    def compose(self) -> ComposeResult:
        """Compose the main app UI."""
        yield Header()

        # Status bar
        yield Static("", id="status_bar")

        # Main container
        with Horizontal(id="main_container"):
            # Left panel - stats and navigation
            with Vertical(id="left_panel"):
                with Container(id="stats_container"):
                    yield Static("", id="stats_display")

                with Container(id="nav_container"):
                    yield Static("[bold]Week Navigation[/bold]")
                    with Horizontal():
                        yield Button("◄ Prev", id="prev_week_btn", variant="default")
                        yield Button("Next ►", id="next_week_btn", variant="default")
                    with Horizontal():
                        yield Button(
                            "Current", id="current_week_btn", variant="primary"
                        )
                        yield Button("Rollover", id="rollover_btn", variant="warning")

                with Container(id="actions_container"):
                    yield Static("[bold]Actions[/bold]", classes="stat_label")
                    yield Button("➕ Add Task", id="add_task_btn", variant="success")
                    yield Button("✓ Complete", id="complete_btn", variant="primary")
                    yield Button("ℹ Details", id="details_btn", variant="default")

            # Right panel - task table
            with Vertical(id="right_panel"):
                yield DataTable(id="task_table")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        table = self.query_one("#task_table", DataTable)
        table.add_columns("ID", "Status", "Title", "Description")
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Set current week after mounting to avoid watcher issues
        year, week = get_current_week()
        self.current_year = year
        self.current_week = week

    def watch_current_year(self, year: int) -> None:
        """Watch for changes to current year."""
        self.load_tasks()

    def watch_current_week(self, week: int) -> None:
        """Watch for changes to current week."""
        self.load_tasks()

    def load_tasks(self) -> None:
        """Load and display tasks for current week."""
        tasks = self.db.list_tasks(week=self.current_week, year=self.current_year)
        stats = self.db.get_week_stats(self.current_year, self.current_week)

        # Update status bar
        week_str = format_week(self.current_year, self.current_week)
        status_bar = self.query_one("#status_bar", Static)
        status_bar.update(f"[bold]Kairo - Week {week_str}[/bold]")

        # Update stats
        stats_display = self.query_one("#stats_display", Static)
        completion_rate = 0
        if stats["total"] > 0:
            completion_rate = (stats["completed"] / stats["total"]) * 100

        stats_text = f"""[bold]Week Statistics[/bold]

Total: {stats['total']}
[green]Completed: {stats['completed']}[/green]
[yellow]Open: {stats['open']}[/yellow]
Completion: {completion_rate:.0f}%"""
        stats_display.update(stats_text)

        # Update table
        table = self.query_one("#task_table", DataTable)
        table.clear()

        for task in tasks:
            status_icon = "✓" if task.status == TaskStatus.COMPLETED else "○"
            status_color = "green" if task.status == TaskStatus.COMPLETED else "yellow"

            table.add_row(
                str(task.id),
                f"[{status_color}]{status_icon}[/{status_color}]",
                task.title,
                task.description or "-",
                key=str(task.id),
            )

    def action_add_task(self) -> None:
        """Show add task dialog."""

        def handle_result(result: bool) -> None:
            if result:
                self.load_tasks()

        self.push_screen(
            AddTaskScreen(self.current_year, self.current_week), handle_result
        )

    def action_complete_task(self) -> None:
        """Mark selected task as complete."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        if self.db.complete_task(task_id):
            self.load_tasks()

    def action_show_details(self) -> None:
        """Show task details."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        task = self.db.get_task(task_id)
        if task:
            self.push_screen(TaskDetailScreen(task))

    def action_prev_week(self) -> None:
        """Go to previous week."""
        # Get the start of current week and subtract 7 days
        from .utils import get_week_range

        week_start, _ = get_week_range(self.current_year, self.current_week)
        prev_date = week_start - __import__("datetime").timedelta(days=7)
        iso = prev_date.isocalendar()
        self.current_year = iso.year
        self.current_week = iso.week

    def action_next_week(self) -> None:
        """Go to next week."""
        self.current_year, self.current_week = get_next_week(
            self.current_year, self.current_week
        )

    def action_refresh(self) -> None:
        """Refresh task list."""
        self.load_tasks()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add_task_btn":
            self.action_add_task()
        elif event.button.id == "complete_btn":
            self.action_complete_task()
        elif event.button.id == "details_btn":
            self.action_show_details()
        elif event.button.id == "prev_week_btn":
            self.action_prev_week()
        elif event.button.id == "next_week_btn":
            self.action_next_week()
        elif event.button.id == "current_week_btn":
            year, week = get_current_week()
            self.current_year = year
            self.current_week = week
        elif event.button.id == "rollover_btn":
            self.rollover_tasks()

    def rollover_tasks(self) -> None:
        """Rollover incomplete tasks to next week."""
        next_year, next_week = get_next_week(self.current_year, self.current_week)
        count = self.db.rollover_tasks(
            self.current_year, self.current_week, next_year, next_week
        )
        self.load_tasks()
        self.notify(
            f"Rolled over {count} task(s) to {format_week(next_year, next_week)}"
        )

    def on_shutdown(self) -> None:
        """Clean up when app shuts down."""
        self.db.close()


def run_tui() -> None:
    """Run the Kairo TUI application."""
    app = KairoApp()
    app.run()
