# Kairo

**Kairo** (Greek: kairos - "the right moment") is a terminal-based task management tool focused on weekly planning. Stay organized with an interactive TUI and automatic task rollover.

## Features

- **Interactive TUI**: Full-featured terminal user interface with keyboard shortcuts
- **Weekly planning**: Organize tasks by ISO week numbers
- **Auto-rollover**: Incomplete tasks automatically move to next week
- **Beautiful output**: Rich terminal formatting with tables and colors
- **Weekly statistics**: Real-time stats and completion tracking
- **CLI commands**: Alternative command-line interface for scripting
- **Simple storage**: SQLite database stored in `~/.kairo/tasks.db`

## Installation

### With UV (recommended)

```bash
# Clone or navigate to the project
cd kairo

# Install with uv
uv sync

# Run directly
uv run kairo --help

# Or activate the virtual environment
source .venv/bin/activate
kairo --help
```

### With pip

```bash
cd kairo
pip install -e .
kairo --help
```

## Usage

### Interactive TUI (Default)

Simply run `kairo` to launch the interactive terminal UI:

```bash
kairo
```

#### TUI Keyboard Shortcuts

- **A** - Add new task
- **C** - Complete selected task
- **D** - View task details
- **R** - Refresh task list
- **←/→** - Navigate between weeks
- **↑/↓** - Navigate task list
- **Q** - Quit

#### TUI Buttons

- **◄ Prev / Next ►** - Navigate weeks
- **Current** - Jump to current week
- **Rollover** - Move incomplete tasks to next week
- **➕ Add Task** - Create new task
- **✓ Complete** - Mark selected task complete
- **ℹ Details** - View task details

### CLI Commands (For Scripting)

#### Add a task

```bash
# Add task to current week
kairo add "Review pull requests"

# Add with description
kairo add "Deploy new feature" -d "Deploy to production after QA approval"

# Add to specific week
kairo add "Quarterly review" -w 46
kairo add "Year-end planning" -w 2025-W52
```

#### List tasks

```bash
# List current week's tasks
kairo list

# List specific week
kairo list -w 45
kairo list -w 2025-W45

# List all tasks
kairo list --all

# Filter by status
kairo list --status open
kairo list --status completed
```

#### Complete a task

```bash
# Mark task as done
kairo complete 3
```

#### Weekly planning report

```bash
# Current week's plan
kairo plan

# Specific week
kairo plan -w 46
```

#### Weekly completion report

```bash
# Current week's report
kairo report

# Specific week
kairo report -w 45
```

#### Rollover incomplete tasks

```bash
# Move current week's incomplete tasks to next week
kairo rollover

# Rollover from specific week to another
kairo rollover -f 45 -t 46
```

## Examples

### Interactive TUI Workflow

1. Launch Kairo: `kairo`
2. Press **A** to add tasks for the week
3. Navigate with arrow keys
4. Press **C** to complete tasks as you finish them
5. Check weekly statistics in the left panel
6. Press **Rollover** button or use **←/→** to move between weeks
7. Press **Q** to quit

### CLI Workflow

```bash
# Monday: Plan your week
kairo plan

# Add new tasks throughout the week
kairo add "Fix authentication bug" -d "Users unable to login with SSO"
kairo add "Update documentation"
kairo add "Team meeting prep"

# Check your tasks
kairo list

# Complete tasks as you finish them
kairo complete 1
kairo complete 3

# Friday: Review your week
kairo report

# Sunday: Move incomplete tasks to next week
kairo rollover
```

## Data Storage

Tasks are stored in `~/.kairo/tasks.db` (SQLite database).

To backup your tasks:

```bash
cp ~/.kairo/tasks.db ~/backups/tasks-backup.db
```

To reset (delete all tasks):

```bash
rm ~/.kairo/tasks.db
```

## Development

```bash
# Install dependencies
uv sync

# Run tests (when available)
uv run pytest

# Run the CLI
uv run kairo --help
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Caution

This is an experimental project built using Claude Code for testing AI coding. Use at your own risk.
