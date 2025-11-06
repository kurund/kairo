"""Interactive TUI for Kairo task management."""

import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, DataTable, Static, Button
from textual.binding import Binding
from textual.reactive import reactive

from .database import Database
from .models import TaskStatus
from .utils import get_current_week, format_week, get_next_week
from .screens import (
    AddTaskScreen,
    EditTaskScreen,
    FilterTagScreen,
    ConfirmDeleteScreen,
    TaskDetailScreen,
)


class KairoApp(App):
    """Main Kairo TUI application."""

    STATE_FILE = Path.home() / ".kairo" / "tui_state.json"

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

    #nav_container .week_nav_btn {
        margin: 0 1;
        min-width: 8;
        height: 3;
    }

    #nav_container Horizontal.action_row {
        width: 100%;
        height: auto;
    }

    #nav_container .action_btn {
        width: 1fr;
        height: 3;
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
        Binding("e", "edit_task", "Edit", key_display="E"),
        Binding("c", "complete_task", "Complete", key_display="C"),
        Binding("o", "reopen_task", "Reopen", key_display="O"),
        Binding("x", "delete_task", "Delete", key_display="X"),
        Binding("d", "show_details", "Details", key_display="D"),
        Binding("f", "filter_by_tag", "Filter", key_display="F"),
        Binding("r", "refresh", "Refresh", key_display="R"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("h", "prev_week", "Prev Week", show=False),
        Binding("l", "next_week", "Next Week", show=False),
        Binding("left", "prev_week", "Prev Week", key_display="←"),
        Binding("right", "next_week", "Next Week", key_display="→"),
        Binding("q", "quit", "Quit", key_display="Q"),
    ]

    current_year = reactive(0)
    current_week = reactive(0)
    current_tag_filter = reactive("")

    def __init__(self):
        super().__init__()
        self.db = Database()
        self._loaded_tag_filter = None
        self._load_state()

    def _load_state(self):
        """Load persisted state from file."""
        try:
            if self.STATE_FILE.exists():
                with open(self.STATE_FILE) as f:
                    state = json.load(f)
                    self._loaded_tag_filter = state.get("tag_filter", "")
        except Exception:
            # Ignore errors loading state
            pass

    def _save_state(self):
        """Save current state to file."""
        try:
            self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.STATE_FILE, "w") as f:
                json.dump(
                    {
                        "tag_filter": self.current_tag_filter,
                    },
                    f,
                )
        except Exception:
            # Ignore errors saving state
            pass

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
                    yield Static("[bold]📅 Week Navigation[/bold]")
                    with Horizontal():
                        yield Button(
                            "◄ Prev",
                            id="prev_week_btn",
                            variant="default",
                            classes="week_nav_btn",
                        )
                        yield Button(
                            "📍 This Week",
                            id="this_week_btn",
                            variant="primary",
                            classes="week_nav_btn",
                        )
                        yield Button(
                            "Next ►",
                            id="next_week_btn",
                            variant="default",
                            classes="week_nav_btn",
                        )
                    yield Static("")  # Spacer
                    yield Static("[bold]⚡ Actions[/bold]")
                    with Horizontal(classes="action_row"):
                        yield Button(
                            "Move to Next Week",
                            id="rollover_btn",
                            variant="warning",
                            classes="action_btn",
                        )
                        yield Button(
                            "Move to Prev Week",
                            id="rollback_btn",
                            variant="error",
                            classes="action_btn",
                        )

            # Right panel - task table
            with Vertical(id="right_panel"):
                yield DataTable(id="task_table")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        table = self.query_one("#task_table", DataTable)
        table.add_columns("ID", "Status", "Title", "Tags", "Description")
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Set current week after mounting to avoid watcher issues
        year, week = get_current_week()
        self.current_year = year
        self.current_week = week

        # Apply loaded tag filter if any
        if self._loaded_tag_filter:
            self.current_tag_filter = self._loaded_tag_filter

        # Set focus to task table
        table.focus()

    def watch_current_year(self, _year: int) -> None:
        """Watch for changes to current year."""
        self.load_tasks()

    def watch_current_week(self, _week: int) -> None:
        """Watch for changes to current week."""
        self.load_tasks()

    def watch_current_tag_filter(self, _tag_filter: str) -> None:
        """Watch for changes to tag filter."""
        self.load_tasks()
        self._save_state()

    def load_tasks(self) -> None:
        """Load and display tasks for current week."""
        # Load tasks with optional tag filter
        if self.current_tag_filter:
            tasks = self.db.list_tasks_by_tag(
                tag=self.current_tag_filter,
                week=self.current_week,
                year=self.current_year,
            )
        else:
            tasks = self.db.list_tasks(week=self.current_week, year=self.current_year)

        stats = self.db.get_week_stats(self.current_year, self.current_week)

        # Update status bar
        week_str = format_week(self.current_year, self.current_week)
        status_bar = self.query_one("#status_bar", Static)
        filter_text = (
            f" [cyan]| Filter: {self.current_tag_filter}[/cyan]"
            if self.current_tag_filter
            else ""
        )
        status_bar.update(f"[bold]Kairo - Week {week_str}{filter_text}[/bold]")

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
            tags_display = ", ".join(task.tags) if task.tags else "-"

            table.add_row(
                str(task.id),
                f"[{status_color}]{status_icon}[/{status_color}]",
                task.title,
                f"[cyan]{tags_display}[/cyan]",
                task.description or "-",
                key=str(task.id),
            )

    def action_add_task(self) -> None:
        """Show add task dialog."""

        def handle_result(result: bool | None) -> None:
            if result:
                self.load_tasks()

        self.push_screen(
            AddTaskScreen(self.current_year, self.current_week), handle_result
        )

    def action_edit_task(self) -> None:
        """Show edit task dialog."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        task = self.db.get_task(task_id)
        if not task:
            return

        def handle_result(result: bool | None) -> None:
            if result:
                self.load_tasks()
                self.notify(f"Task updated: {task.title}")

        self.push_screen(EditTaskScreen(task), handle_result)

    def action_complete_task(self) -> None:
        """Mark selected task as complete."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        if self.db.complete_task(task_id):
            self.load_tasks()

    def action_reopen_task(self) -> None:
        """Mark selected completed task as open again."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        if self.db.reopen_task(task_id):
            self.load_tasks()

    def action_delete_task(self) -> None:
        """Delete selected task with confirmation."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        task = self.db.get_task(task_id)
        if not task:
            return

        def handle_result(confirmed: bool | None) -> None:
            if confirmed:
                if self.db.delete_task(task_id):
                    self.load_tasks()
                    self.notify(f"Task deleted: {task.title}")

        self.push_screen(ConfirmDeleteScreen(task), handle_result)

    def action_show_details(self) -> None:
        """Show task details."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        task = self.db.get_task(task_id)
        if task:
            self.push_screen(TaskDetailScreen(task))

    def action_filter_by_tag(self) -> None:
        """Show filter by tag dialog."""
        available_tags = self.db.get_all_tags()

        def handle_result(tag_filter: str | None) -> None:
            if tag_filter is not None:  # None means cancelled
                self.current_tag_filter = tag_filter
                if tag_filter:
                    self.notify(f"Filtered by tag: {tag_filter}")
                else:
                    self.notify("Filter cleared - showing all tasks")

        self.push_screen(
            FilterTagScreen(self.current_tag_filter, available_tags), handle_result
        )

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

    def action_cursor_down(self) -> None:
        """Move cursor down in task table (vim j)."""
        table = self.query_one("#task_table", DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in task table (vim k)."""
        table = self.query_one("#task_table", DataTable)
        table.action_cursor_up()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "prev_week_btn":
            self.action_prev_week()
        elif event.button.id == "next_week_btn":
            self.action_next_week()
        elif event.button.id == "this_week_btn":
            year, week = get_current_week()
            self.current_year = year
            self.current_week = week
        elif event.button.id == "rollover_btn":
            self.rollover_tasks()
        elif event.button.id == "rollback_btn":
            self.rollback_tasks()

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

    def rollback_tasks(self) -> None:
        """Rollback incomplete tasks from next week to current week."""
        next_year, next_week = get_next_week(self.current_year, self.current_week)
        count = self.db.rollback_tasks(
            next_year, next_week, self.current_year, self.current_week
        )
        self.load_tasks()
        if count > 0:
            self.notify(
                f"Rolled back {count} task(s) from {format_week(next_year, next_week)}"
            )
        else:
            self.notify("No open tasks to rollback from next week")

    def on_shutdown(self) -> None:
        """Clean up when app shuts down."""
        self.db.close()


def run_tui() -> None:
    """Run the Kairo TUI application."""
    app = KairoApp()
    app.run()
