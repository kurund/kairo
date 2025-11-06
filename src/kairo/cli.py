"""CLI interface for kairo task management."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .database import Database
from .models import TaskStatus
from .utils import get_current_week, format_week, parse_week, get_next_week


console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="0.1.0")
def cli(ctx):
    """Kairo - Terminal-based task management with weekly planning.

    Run without arguments to launch the interactive TUI.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand provided, launch TUI
        from .tui import run_tui

        run_tui()


@cli.command()
@click.argument("title")
@click.option("-d", "--description", default="", help="Task description")
@click.option(
    "-w", "--week", help="Week number or YYYY-Wnn format (defaults to current week)"
)
def add(title: str, description: str, week: str):
    """Add a new task."""
    db = Database()

    try:
        if week:
            year, week_num = parse_week(week)
        else:
            year, week_num = get_current_week()

        task = db.add_task(
            title=title, description=description, week=week_num, year=year
        )

        console.print(f"\n[green]✓[/green] Task created: [bold]{task.title}[/bold]")
        console.print(f"  ID: {task.id}")
        console.print(f"  Week: {format_week(task.year, task.week)}")
        if description:
            console.print(f"  Description: {task.description}")
        console.print()

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise click.Abort()
    finally:
        db.close()


@cli.command()
@click.option("-w", "--week", help="Week number or YYYY-Wnn format")
@click.option("-a", "--all", "show_all", is_flag=True, help="Show all tasks")
@click.option(
    "-s", "--status", type=click.Choice(["open", "completed"]), help="Filter by status"
)
def list(week: str, show_all: bool, status: str):
    """List tasks."""
    db = Database()

    try:
        if week:
            year, week_num = parse_week(week)
        elif not show_all:
            year, week_num = get_current_week()
        else:
            year, week_num = None, None

        status_filter = TaskStatus(status) if status else None
        tasks = db.list_tasks(
            week=week_num, year=year, status=status_filter, show_all=show_all
        )

        if not tasks:
            if show_all:
                console.print("\n[yellow]No tasks found.[/yellow]\n")
            else:
                console.print(
                    f"\n[yellow]No tasks found for week {format_week(year, week_num)}.[/yellow]\n"
                )
            return

        # Display header
        if show_all:
            header = "[bold]All Tasks[/bold]"
        else:
            header = f"[bold]Tasks for Week {format_week(year, week_num)}[/bold]"

        console.print(f"\n{header}\n")

        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Status", width=10)
        table.add_column("Title", min_width=30)
        table.add_column("Week", width=10)
        table.add_column("Description", style="dim")

        for task in tasks:
            status_display = (
                "✓ Done" if task.status == TaskStatus.COMPLETED else "○ Open"
            )
            status_style = "green" if task.status == TaskStatus.COMPLETED else "yellow"

            table.add_row(
                str(task.id),
                f"[{status_style}]{status_display}[/{status_style}]",
                task.title,
                format_week(task.year, task.week),
                task.description or "-",
            )

        console.print(table)
        console.print()

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise click.Abort()
    finally:
        db.close()


@cli.command()
@click.argument("task_id", type=int)
def complete(task_id: int):
    """Mark a task as completed."""
    db = Database()

    try:
        task = db.get_task(task_id)
        if not task:
            console.print(f"[red]Error:[/red] Task {task_id} not found.", err=True)
            raise click.Abort()

        if task.status == TaskStatus.COMPLETED:
            console.print(f"[yellow]Task {task_id} is already completed.[/yellow]")
            return

        if db.complete_task(task_id):
            console.print(
                f"\n[green]✓[/green] Task completed: [bold]{task.title}[/bold]\n"
            )
        else:
            console.print(
                f"[red]Error:[/red] Failed to complete task {task_id}.", err=True
            )
            raise click.Abort()

    finally:
        db.close()


@cli.command()
@click.option(
    "-w", "--week", help="Week number or YYYY-Wnn format (defaults to current week)"
)
def plan(week: str):
    """Show weekly planning report."""
    db = Database()

    try:
        if week:
            year, week_num = parse_week(week)
        else:
            year, week_num = get_current_week()

        tasks = db.list_tasks(week=week_num, year=year, status=TaskStatus.OPEN)
        stats = db.get_week_stats(year, week_num)

        # Header
        week_str = format_week(year, week_num)
        console.print(f"\n[bold cyan]Weekly Plan - {week_str}[/bold cyan]\n")

        # Stats
        console.print(f"Total tasks planned: {stats['total']}")
        console.print(f"Open tasks: {stats['open']}")
        console.print(f"Completed tasks: {stats['completed']}\n")

        if not tasks:
            console.print("[yellow]No open tasks for this week.[/yellow]\n")
            return

        # Open tasks table
        table = Table(show_header=True, header_style="bold")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Title", min_width=30)
        table.add_column("Description", style="dim")

        for task in tasks:
            table.add_row(
                str(task.id),
                task.title,
                task.description or "-",
            )

        console.print(table)
        console.print()

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise click.Abort()
    finally:
        db.close()


@cli.command()
@click.option(
    "-w", "--week", help="Week number or YYYY-Wnn format (defaults to current week)"
)
def report(week: str):
    """Show weekly completion report."""
    db = Database()

    try:
        if week:
            year, week_num = parse_week(week)
        else:
            year, week_num = get_current_week()

        stats = db.get_week_stats(year, week_num)
        all_tasks = db.list_tasks(week=week_num, year=year)

        # Header
        week_str = format_week(year, week_num)
        console.print(f"\n[bold cyan]Weekly Report - {week_str}[/bold cyan]\n")

        # Calculate completion rate
        completion_rate = 0
        if stats["total"] > 0:
            completion_rate = (stats["completed"] / stats["total"]) * 100

        # Stats panel
        stats_text = Text()
        stats_text.append(f"Total tasks: {stats['total']}\n")
        stats_text.append(f"Completed: {stats['completed']}\n", style="green")
        stats_text.append(f"Open: {stats['open']}\n", style="yellow")
        stats_text.append(f"Completion rate: {completion_rate:.1f}%\n", style="bold")

        console.print(Panel(stats_text, title="Statistics", border_style="cyan"))
        console.print()

        if not all_tasks:
            console.print("[yellow]No tasks for this week.[/yellow]\n")
            return

        # Split tasks by status
        completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
        open_tasks = [t for t in all_tasks if t.status == TaskStatus.OPEN]

        # Completed tasks
        if completed_tasks:
            console.print("[bold green]Completed Tasks[/bold green]\n")
            for task in completed_tasks:
                console.print(f"  [green]✓[/green] {task.title}")
            console.print()

        # Open tasks
        if open_tasks:
            console.print("[bold yellow]Open Tasks[/bold yellow]\n")
            for task in open_tasks:
                console.print(f"  [yellow]○[/yellow] {task.title}")
            console.print()

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise click.Abort()
    finally:
        db.close()


@cli.command()
@click.option("-f", "--from-week", help="Source week (defaults to current week)")
@click.option("-t", "--to-week", help="Target week (defaults to next week)")
@click.confirmation_option(prompt="Are you sure you want to rollover incomplete tasks?")
def rollover(from_week: str, to_week: str):
    """Move incomplete tasks to next week."""
    db = Database()

    try:
        # Parse source week
        if from_week:
            from_year, from_week_num = parse_week(from_week)
        else:
            from_year, from_week_num = get_current_week()

        # Parse target week
        if to_week:
            to_year, to_week_num = parse_week(to_week)
        else:
            to_year, to_week_num = get_next_week(from_year, from_week_num)

        # Perform rollover
        count = db.rollover_tasks(from_year, from_week_num, to_year, to_week_num)

        from_str = format_week(from_year, from_week_num)
        to_str = format_week(to_year, to_week_num)

        if count > 0:
            console.print(
                f"\n[green]✓[/green] Rolled over {count} task(s) from {from_str} to {to_str}\n"
            )
        else:
            console.print(
                f"\n[yellow]No open tasks to rollover from {from_str}.[/yellow]\n"
            )

    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}", err=True)
        raise click.Abort()
    finally:
        db.close()


if __name__ == "__main__":
    cli()
