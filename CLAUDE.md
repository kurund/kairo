# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kairo is a terminal-based task management tool focused on weekly planning using ISO week numbers. It features both an interactive TUI (Textual) and a CLI interface (Click).

**IMPORTANT**: This is an experimental project built using Claude Code for testing AI coding. Use at your own risk.

## Development Commands

```bash
# Install dependencies (recommended)
uv sync

# Run the TUI (default mode)
uv run kairo

# Run CLI commands
uv run kairo add "Task title"
uv run kairo list
uv run kairo --help

# Activate virtual environment (optional)
source .venv/bin/activate
kairo --help
```

## Architecture

### Dual Interface Pattern

The application has two entry points that share the same database layer:

1. **TUI Mode** (default): Interactive terminal UI using Textual framework
   - Launched when running `kairo` without arguments
   - Entry point: `tui.py::run_tui()` → `KairoApp`

2. **CLI Mode**: Command-line interface using Click
   - Launched with subcommands like `kairo add`, `kairo list`
   - Entry point: `cli.py::cli()`

### Core Components

#### Database Layer (`database.py`)
- SQLite database stored at `~/.kairo/tasks.db`
- `Database` class handles all data operations
- **Position-based ordering**: Tasks are ordered by `position` field (NOT priority)
  - Auto-assigned: New tasks get `MAX(position) + 1` per week/year group
  - Tasks are sorted: `ORDER BY position ASC, created_at ASC`
  - Separate numbering for inbox tasks (where week/year IS NULL)
- **Migrations tracking**: Uses `migrations` table to track one-time schema changes
- Important methods:
  - `add_task()`: Auto-assigns position
  - `swap_task_positions()`: Exchanges positions between two tasks
  - `rollover_tasks()`: Moves incomplete tasks between weeks
  - `rollback_tasks()`: Moves tasks to previous week

#### Models (`models.py`)
- `Task` dataclass with fields:
  - `week` and `year`: ISO week number (None = inbox/unscheduled)
  - `position`: Integer for manual ordering within week/year groups
  - `tags`: List of tag names
  - `estimate`: Estimated time in hours
  - `project`: Project name
  - `status`: TaskStatus enum (OPEN/COMPLETED)

#### TUI Application (`tui.py`)
- Main app class: `KairoApp` extends Textual's `App`
- **Reactive properties**: `current_year` and `current_week` represent the VIEWED week (not necessarily today's week)
  - These change when user navigates with arrow keys
  - All operations (rollover, rollback) use the viewed week
- **Filter persistence**: Filters are saved to `~/.kairo/tui_state.json` and restored on launch
  - Separate filters for weekly view vs inbox view
- **Modal screens**: All dialogs are ModalScreen subclasses in `screens/` directory
- **Layout**: Two-panel design - left panel (stats/navigation), right panel (task table)

#### Screens (`screens/`)
Modal screens for various interactions:
- `TaskFormScreen`: Unified form for adding AND editing tasks
  - Edit mode: Determined by `task` parameter (None = add, Task = edit)
  - Schedule checkbox: Changes behavior based on edit mode
- `FilterTagScreen`, `FilterProjectScreen`: Filter selection with autocomplete
- `FilterSelectScreen`: Main filter menu (tag/project/clear)
- `ConfirmDeleteScreen`: Delete confirmation dialog
- `TaskDetailScreen`: View full task details
- `WeeklyPlanScreen`, `WeeklyReportScreen`: Report displays

## Key Patterns and Conventions

### Week Handling
- All weeks use ISO 8601 week numbers (Monday start, 1-53)
- Week format: `2025-W45`
- Utilities in `utils.py`: `get_current_week()`, `parse_week()`, `format_week()`
- Week navigation calculates previous/next week using `get_week_range()` and date arithmetic

### Task Positioning System
**DO NOT implement a priority field** - the app uses position-based ordering:
- Each task has a `position` integer field
- New tasks auto-assign `position = MAX(position) + 1` for their week/year
- Users manually reorder with J/K keys (calls `swap_task_positions()`)
- Inbox tasks have separate position sequence (week=NULL, year=NULL)

### Inbox vs Scheduled Tasks
- Inbox: Tasks with `week=None` and `year=None`
- Scheduled: Tasks with specific week/year values
- Toggle: Press `t` key or uncheck "Schedule for this week" in task form

### Filter Persistence
- Weekly view filters: `current_tag_filter`, `current_project_filter`
- Inbox view filters: `inbox_tag_filter`, `inbox_project_filter`
- Saved to `~/.kairo/tui_state.json` via `_save_state()` on every filter change
- Loaded on startup via `_load_state()`

### Keyboard Shortcuts (Important Bindings)
- Lowercase keys: Non-destructive actions (a=add, e=edit, c=complete, v=view)
- Uppercase keys: Move/destructive actions (J=move down, K=move up, vim-style)
- Navigation: j/k (vim), h/l (vim), arrow keys
- Special: d=delete, t=toggle schedule, f=filter, i=inbox, g=goto current week
- Reports: w=weekly plan, **r**=weekly report (NOTE: Changed from 's' to 'r')

### Database Migrations
Use the migrations table pattern:
```python
cursor.execute("SELECT name FROM migrations WHERE name = 'migration_name'")
if not cursor.fetchone():
    # Perform migration
    cursor.execute("INSERT INTO migrations (name, applied_at) VALUES (?, ?)",
                   ('migration_name', datetime.now().isoformat()))
```

### SQLite Row Objects
Use bracket notation, not `.get()`:
```python
# Correct
position = row["position"] if "position" in row.keys() and row["position"] else 0

# Incorrect - sqlite3.Row doesn't have .get() method
position = row.get("position", 0)  # This will error
```

## Testing and Quality

- Pre-commit hooks configured (ruff)
- Python 3.12+ required
- Dependencies: textual, click, rich, pyperclip

## Data Storage

- Database: `~/.kairo/tasks.db` (SQLite)
- TUI state: `~/.kairo/tui_state.json` (filters)
- Backup: `cp ~/.kairo/tasks.db ~/backup.db`
- Reset: `rm ~/.kairo/tasks.db`
