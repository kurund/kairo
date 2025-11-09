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
    TaskFormScreen,
    FilterTagScreen,
    FilterProjectScreen,
    FilterSelectScreen,
    ConfirmDeleteScreen,
    TaskDetailScreen,
    WeeklyPlanScreen,
    WeeklyReportScreen,
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
        margin: 0 1;
    }

    DataTable {
        height: 100%;
    }

    .stat_label {
        margin: 0 0 1 0;
    }
    """

    BINDINGS = [
        Binding("a", "add_task", "Add", key_display="a"),
        Binding("e", "edit_task", "Edit", key_display="e"),
        Binding("c", "toggle_complete", "Complete", key_display="c"),
        Binding("t", "toggle_schedule", "Schedule", key_display="t"),
        Binding("d", "delete_task", "Delete", key_display="d"),
        Binding("v", "show_details", "Details", key_display="v"),
        Binding("f", "show_filter", "Filter", key_display="f"),
        Binding("i", "toggle_inbox", "Inbox", key_display="i"),
        Binding("w", "show_weekly_plan", "Plan", key_display="w"),
        Binding("s", "show_weekly_report", "Report", key_display="s"),
        Binding("g", "goto_current_week", "This Week", key_display="g"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("J", "move_task_down", "Move Down", key_display="J"),
        Binding("K", "move_task_up", "Move Up", key_display="K"),
        Binding("h", "prev_week", "Prev Week", show=False),
        Binding("l", "next_week", "Next Week", show=False),
        Binding("left", "prev_week", "Prev Week", key_display="←"),
        Binding("right", "next_week", "Next Week", key_display="→"),
        Binding("q", "quit", "Quit", key_display="q"),
    ]

    current_year = reactive(0)
    current_week = reactive(0)
    current_tag_filter = reactive("")
    current_project_filter = reactive("")
    inbox_tag_filter = reactive("")
    inbox_project_filter = reactive("")
    viewing_inbox = reactive(False)

    def __init__(self):
        super().__init__()
        self.db = Database()
        self._loaded_tag_filter = None
        self._loaded_project_filter = None
        self._loaded_inbox_tag_filter = None
        self._loaded_inbox_project_filter = None
        self._load_state()

    def _load_state(self):
        """Load persisted state from file."""
        try:
            if self.STATE_FILE.exists():
                with open(self.STATE_FILE) as f:
                    state = json.load(f)
                    self._loaded_tag_filter = state.get("tag_filter", "")
                    self._loaded_project_filter = state.get("project_filter", "")
                    self._loaded_inbox_tag_filter = state.get("inbox_tag_filter", "")
                    self._loaded_inbox_project_filter = state.get(
                        "inbox_project_filter", ""
                    )
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
                        "project_filter": self.current_project_filter,
                        "inbox_tag_filter": self.inbox_tag_filter,
                        "inbox_project_filter": self.inbox_project_filter,
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
                            "📍 Current",
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
                            variant="default",
                            classes="action_btn",
                        )
                        yield Button(
                            "Move to Prev Week",
                            id="rollback_btn",
                            variant="default",
                            classes="action_btn",
                        )
                    with Horizontal(classes="action_row"):
                        yield Button(
                            "📋 Weekly Plan",
                            id="weekly_plan_btn",
                            variant="success",
                            classes="action_btn",
                        )
                        yield Button(
                            "📊 Weekly Report",
                            id="weekly_report_btn",
                            variant="success",
                            classes="action_btn",
                        )

            # Right panel - task table
            with Vertical(id="right_panel"):
                yield DataTable(id="task_table")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the app when mounted."""
        table = self.query_one("#task_table", DataTable)
        table.add_column("ID", width=6)
        table.add_column("Status", width=8)
        table.add_column("Title", width=None)  # Takes remaining space
        table.add_column("Project", width=20)
        table.add_column("Tags", width=20)
        table.add_column("Est", width=6)  # Estimate in hours
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Set current week after mounting to avoid watcher issues
        year, week = get_current_week()
        self.current_year = year
        self.current_week = week

        # Apply loaded tag filter if any
        if self._loaded_tag_filter:
            self.current_tag_filter = self._loaded_tag_filter

        # Apply loaded project filter if any
        if self._loaded_project_filter:
            self.current_project_filter = self._loaded_project_filter

        # Apply loaded inbox filters if any
        if self._loaded_inbox_tag_filter:
            self.inbox_tag_filter = self._loaded_inbox_tag_filter

        if self._loaded_inbox_project_filter:
            self.inbox_project_filter = self._loaded_inbox_project_filter

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

    def watch_current_project_filter(self, _project_filter: str) -> None:
        """Watch for changes to project filter."""
        self.load_tasks()
        self._save_state()

    def watch_inbox_tag_filter(self, _tag_filter: str) -> None:
        """Watch for changes to inbox tag filter."""
        self.load_tasks()
        self._save_state()

    def watch_inbox_project_filter(self, _project_filter: str) -> None:
        """Watch for changes to inbox project filter."""
        self.load_tasks()
        self._save_state()

    def watch_viewing_inbox(self, _viewing_inbox: bool) -> None:
        """Watch for changes to inbox viewing mode."""
        self.load_tasks()

    def load_tasks(self) -> None:
        """Load and display tasks for current week or inbox."""
        # Load tasks based on viewing mode
        if self.viewing_inbox:
            # Load inbox tasks (unscheduled) using inbox-specific filters
            tasks = self.db.list_inbox_tasks()
            # Apply inbox filters
            if self.inbox_tag_filter:
                tasks = [t for t in tasks if self.inbox_tag_filter in t.tags]
            if self.inbox_project_filter:
                tasks = [t for t in tasks if t.project == self.inbox_project_filter]
        elif self.current_tag_filter and self.current_project_filter:
            # Both filters: get tag filtered tasks, then filter by project
            tasks = self.db.list_tasks_by_tag(
                tag=self.current_tag_filter,
                week=self.current_week,
                year=self.current_year,
            )
            tasks = [t for t in tasks if t.project == self.current_project_filter]
        elif self.current_tag_filter:
            tasks = self.db.list_tasks_by_tag(
                tag=self.current_tag_filter,
                week=self.current_week,
                year=self.current_year,
            )
        elif self.current_project_filter:
            tasks = self.db.list_tasks_by_project(
                project=self.current_project_filter,
                week=self.current_week,
                year=self.current_year,
            )
        else:
            tasks = self.db.list_tasks(week=self.current_week, year=self.current_year)

        # Calculate stats from filtered tasks
        stats = {
            "total": len(tasks),
            "completed": sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
            "open": sum(1 for t in tasks if t.status == TaskStatus.OPEN),
            "total_estimate": sum(t.estimate for t in tasks if t.estimate),
            "completed_estimate": sum(
                t.estimate
                for t in tasks
                if t.estimate and t.status == TaskStatus.COMPLETED
            ),
            "open_estimate": sum(
                t.estimate for t in tasks if t.estimate and t.status == TaskStatus.OPEN
            ),
        }

        # Update status bar
        status_bar = self.query_one("#status_bar", Static)

        if self.viewing_inbox:
            view_str = "Inbox"
            # Build filter text for inbox
            filters = []
            if self.inbox_tag_filter:
                filters.append(f"Tag: {self.inbox_tag_filter}")
            if self.inbox_project_filter:
                filters.append(f"Project: {self.inbox_project_filter}")
        else:
            week_str = format_week(self.current_year, self.current_week)
            view_str = f"Week {week_str}"
            # Build filter text for weekly view
            filters = []
            if self.current_tag_filter:
                filters.append(f"Tag: {self.current_tag_filter}")
            if self.current_project_filter:
                filters.append(f"Project: {self.current_project_filter}")

        filter_text = f" [cyan]| {' | '.join(filters)}[/cyan]" if filters else ""
        status_bar.update(f"[bold]Kairo - {view_str}{filter_text}[/bold]")

        # Update stats
        stats_display = self.query_one("#stats_display", Static)
        completion_rate = 0
        if stats["total"] > 0:
            completion_rate = (stats["completed"] / stats["total"]) * 100

        # Build stats text with estimates if any exist
        stats_text = f"""[bold]Week Statistics[/bold]

Total: {stats['total']}
[green]Completed: {stats['completed']}[/green]
[yellow]Open: {stats['open']}[/yellow]
Completion: {completion_rate:.0f}%"""

        # Add estimate totals if any tasks have estimates
        if stats["total_estimate"] > 0:
            stats_text += f"""

[bold]Estimates[/bold]
Total: {stats['total_estimate']}h
[green]Completed: {stats['completed_estimate']}h[/green]
[yellow]Remaining: {stats['open_estimate']}h[/yellow]"""

        stats_display.update(stats_text)

        # Update table
        table = self.query_one("#task_table", DataTable)
        table.clear()

        for task in tasks:
            status_icon = "✓" if task.status == TaskStatus.COMPLETED else "○"
            status_color = "green" if task.status == TaskStatus.COMPLETED else "yellow"
            project_display = task.project if task.project else "-"
            tags_display = ", ".join(task.tags) if task.tags else "-"
            estimate_display = f"{task.estimate}h" if task.estimate else "-"

            table.add_row(
                str(task.id),
                f"[{status_color}]{status_icon}[/{status_color}]",
                task.title,
                f"[magenta]{project_display}[/magenta]",
                f"[cyan]{tags_display}[/cyan]",
                f"[dim]{estimate_display}[/dim]",
                key=str(task.id),
            )

    def action_add_task(self) -> None:
        """Show add task dialog."""

        def handle_result(result: bool | None) -> None:
            if result:
                self.load_tasks()

        # Use the appropriate filters based on current view
        if self.viewing_inbox:
            default_tag = self.inbox_tag_filter
            default_project = self.inbox_project_filter
        else:
            default_tag = self.current_tag_filter
            default_project = self.current_project_filter

        self.push_screen(
            TaskFormScreen(
                self.current_year,
                self.current_week,
                task=None,  # None means add new task
                default_tag=default_tag,
                default_project=default_project,
            ),
            handle_result,
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

        self.push_screen(
            TaskFormScreen(
                self.current_year,
                self.current_week,
                task=task,  # Pass task for editing
            ),
            handle_result,
        )

    def action_toggle_complete(self) -> None:
        """Toggle task completion status (complete ↔ reopen)."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        task = self.db.get_task(task_id)
        if not task:
            return

        # Toggle based on current status
        if task.status == TaskStatus.COMPLETED:
            if self.db.reopen_task(task_id):
                self.load_tasks()
        else:
            if self.db.complete_task(task_id):
                self.load_tasks()

    def action_toggle_schedule(self) -> None:
        """Toggle task between inbox and current week."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        task_id = int(table.get_row_at(table.cursor_row)[0])
        task = self.db.get_task(task_id)
        if not task:
            return

        # Toggle based on current schedule status
        if task.week is None or task.year is None:
            # Task is in inbox - schedule it to current week
            self.db.update_task(
                task_id, week=self.current_week, year=self.current_year
            )
            week_str = format_week(self.current_year, self.current_week)
            self.notify(f"Task scheduled to {week_str}: {task.title}")
        else:
            # Task is scheduled - move it to inbox
            self.db.update_task(task_id, week=None, year=None)
            self.notify(f"Task moved to inbox: {task.title}")

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

    def action_show_filter(self) -> None:
        """Show filter selection dialog."""

        def handle_filter_selection(filter_type: str | None) -> None:
            if filter_type is None:
                return  # User cancelled
            elif filter_type == "tag":
                self._filter_by_tag()
            elif filter_type == "project":
                self._filter_by_project()
            elif filter_type == "clear":
                # Clear all filters
                if self.viewing_inbox:
                    self.inbox_tag_filter = ""
                    self.inbox_project_filter = ""
                else:
                    self.current_tag_filter = ""
                    self.current_project_filter = ""
                self.notify("All filters cleared")

        self.push_screen(FilterSelectScreen(), handle_filter_selection)

    def _filter_by_tag(self) -> None:
        """Show filter by tag dialog."""
        available_tags = self.db.get_all_tags()

        def handle_result(tag_filter: str | None) -> None:
            if tag_filter is not None:  # None means cancelled
                if self.viewing_inbox:
                    self.inbox_tag_filter = tag_filter
                else:
                    self.current_tag_filter = tag_filter

                if tag_filter:
                    self.notify(f"Filtered by tag: {tag_filter}")
                else:
                    self.notify("Tag filter cleared")

        # Use the appropriate filter based on current view
        current_filter = (
            self.inbox_tag_filter if self.viewing_inbox else self.current_tag_filter
        )
        self.push_screen(FilterTagScreen(current_filter, available_tags), handle_result)

    def _filter_by_project(self) -> None:
        """Show filter by project dialog."""
        available_projects = self.db.get_all_projects()

        def handle_result(project_filter: str | None) -> None:
            if project_filter is not None:  # None means cancelled
                if self.viewing_inbox:
                    self.inbox_project_filter = project_filter
                else:
                    self.current_project_filter = project_filter

                if project_filter:
                    self.notify(f"Filtered by project: {project_filter}")
                else:
                    self.notify("Project filter cleared")

        # Use the appropriate filter based on current view
        current_filter = (
            self.inbox_project_filter
            if self.viewing_inbox
            else self.current_project_filter
        )
        self.push_screen(
            FilterProjectScreen(current_filter, available_projects),
            handle_result,
        )

    def action_toggle_inbox(self) -> None:
        """Toggle between inbox and weekly view."""
        self.viewing_inbox = not self.viewing_inbox
        if self.viewing_inbox:
            self.notify("Viewing Inbox (unscheduled tasks)")
        else:
            week_str = format_week(self.current_year, self.current_week)
            self.notify(f"Viewing {week_str}")

    def action_show_weekly_plan(self) -> None:
        """Show weekly plan for sharing with team."""
        # Get all tasks for the current week (unfiltered)
        tasks = self.db.list_tasks(week=self.current_week, year=self.current_year)
        self.push_screen(WeeklyPlanScreen(tasks, self.current_year, self.current_week))

    def action_show_weekly_report(self) -> None:
        """Show comprehensive weekly report."""
        # Get all tasks for the current week (unfiltered)
        tasks = self.db.list_tasks(week=self.current_week, year=self.current_year)
        self.push_screen(
            WeeklyReportScreen(tasks, self.current_year, self.current_week)
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

    def action_goto_current_week(self) -> None:
        """Go to current week."""
        year, week = get_current_week()
        self.current_year = year
        self.current_week = week
        week_str = format_week(year, week)
        self.notify(f"Viewing current week: {week_str}")

    def action_cursor_down(self) -> None:
        """Move cursor down in task table (vim j)."""
        table = self.query_one("#task_table", DataTable)
        table.action_cursor_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in task table (vim k)."""
        table = self.query_one("#task_table", DataTable)
        table.action_cursor_up()

    def action_move_task_down(self) -> None:
        """Move selected task down in the list (swap with task below)."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        # Can't move down if already at bottom
        if table.cursor_row >= table.row_count - 1:
            self.notify("Task is already at the bottom")
            return

        # Get current and next task IDs
        current_task_id = int(table.get_row_at(table.cursor_row)[0])
        next_task_id = int(table.get_row_at(table.cursor_row + 1)[0])

        # Swap positions
        if self.db.swap_task_positions(current_task_id, next_task_id):
            # Remember cursor position
            cursor_pos = table.cursor_row
            # Reload tasks
            self.load_tasks()
            # Move cursor down to follow the task
            if cursor_pos + 1 < table.row_count:
                table.move_cursor(row=cursor_pos + 1)
        else:
            self.notify("Failed to move task")

    def action_move_task_up(self) -> None:
        """Move selected task up in the list (swap with task above)."""
        table = self.query_one("#task_table", DataTable)
        if table.cursor_row is None or table.row_count == 0:
            return

        # Can't move up if already at top
        if table.cursor_row <= 0:
            self.notify("Task is already at the top")
            return

        # Get current and previous task IDs
        current_task_id = int(table.get_row_at(table.cursor_row)[0])
        prev_task_id = int(table.get_row_at(table.cursor_row - 1)[0])

        # Swap positions
        if self.db.swap_task_positions(current_task_id, prev_task_id):
            # Remember cursor position
            cursor_pos = table.cursor_row
            # Reload tasks
            self.load_tasks()
            # Move cursor up to follow the task
            if cursor_pos - 1 >= 0:
                table.move_cursor(row=cursor_pos - 1)
        else:
            self.notify("Failed to move task")

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
        elif event.button.id == "weekly_plan_btn":
            self.action_show_weekly_plan()
        elif event.button.id == "weekly_report_btn":
            self.action_show_weekly_report()

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
