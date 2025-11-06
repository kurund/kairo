# Kairo

**Kairo** (Greek: kairos - "the right moment") is a terminal-based task management tool focused on weekly planning. Stay organized with an interactive TUI and automatic task rollover.

## Features

- **Interactive TUI**: Full-featured terminal user interface with keyboard shortcuts
- **Weekly planning**: Organize tasks by ISO week numbers
- **Tags system**: Categorize tasks with tags (e.g., work, personal, urgent)
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
- **E** - Edit selected task
- **C** - Complete selected task
- **O** - Reopen completed task (mark as open)
- **X** - Delete selected task (with confirmation)
- **D** - View task details
- **F** - Filter tasks by tag (persisted across sessions)
- **R** - Refresh task list
- **←/→** or **H/L** - Navigate between weeks (vim style)
- **↑/↓** or **J/K** - Navigate task list (vim style)
- **Q** - Quit

#### TUI Buttons

**Week Navigation:**
- **◄ Prev** - Go to previous week
- **📍 This Week** - Jump to current week
- **Next ►** - Go to next week

**Actions:**
- **➡️  Move to Next Week** - Move incomplete tasks from current week to next week
- **⬅️  Move to Prev Week** - Move incomplete tasks from next week back to current week

### CLI Commands (For Scripting)

#### Add a task

```bash
# Add task to current week
kairo add "Review pull requests"

# Add with description
kairo add "Deploy new feature" -d "Deploy to production after QA approval"

# Add with tags
kairo add "Team meeting" -t "work,urgent"
kairo add "Buy groceries" -t "personal"

# Add to specific week
kairo add "Quarterly review" -w 46
kairo add "Year-end planning" -w 2025-W52

# Combine options
kairo add "Sprint planning" -d "Q4 planning session" -t "work,planning" -w 46
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

# Filter by tag
kairo list --tag work
kairo list --tag personal --status open
kairo list --tag urgent --all
```

#### Edit a task

```bash
# Edit task title
kairo edit 3 --title "New title"

# Edit task description
kairo edit 3 -d "New description"

# Edit task tags
kairo edit 3 -t "work,urgent"

# Edit multiple fields at once
kairo edit 3 --title "Updated title" -d "Updated description" -t "work,important"

# Clear tags (empty string)
kairo edit 3 -t ""
```

#### Complete a task

```bash
# Mark task as done
kairo complete 3
```

#### Reopen a task

```bash
# Mark completed task as open again
kairo reopen 3
```

#### Delete a task

```bash
# Delete a task permanently (requires confirmation)
kairo delete 3

# Skip confirmation prompt
kairo delete 3 --yes
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
3. Press **F** to filter by tag (e.g., "work", "personal")
4. Navigate with arrow keys or **J/K** (vim style)
5. Press **C** to complete tasks as you finish them
6. Press **E** to edit task details
7. Check weekly statistics in the left panel
8. Press **←/→** to move between weeks
9. Filter persists - reopening Kairo maintains your tag filter
10. Press **Q** to quit

### CLI Workflow

```bash
# Monday: Plan your week
kairo plan

# Add new tasks throughout the week with tags
kairo add "Fix authentication bug" -d "Users unable to login with SSO" -t "work,urgent"
kairo add "Update documentation" -t "work"
kairo add "Team meeting prep" -t "work,meeting"
kairo add "Dentist appointment" -t "personal"

# Check your tasks
kairo list

# View work tasks only
kairo list --tag work

# Complete tasks as you finish them
kairo complete 1
kairo complete 3

# Reopen task if completed by mistake
kairo reopen 2

# Friday: Review your week
kairo report

# Sunday: Move incomplete tasks to next week
kairo rollover
```

## Tags

Tags help you organize and filter tasks by context. You can assign multiple tags to any task.

### Common Tag Examples

- **Context**: `work`, `personal`, `home`
- **Priority**: `urgent`, `important`, `low-priority`
- **Type**: `meeting`, `coding`, `review`, `planning`
- **Projects**: `project-alpha`, `maintenance`, `documentation`

### Using Tags in TUI

1. Press **A** to add a new task
2. Fill in the title and description
3. In the "Tags" field, enter comma-separated tags: `work, urgent`
4. Tags appear in the task table and details view
5. Press **F** to filter tasks by tag
   - Shows list of all available tags
   - Enter a tag name to filter (e.g., "work")
   - Press "Clear" to show all tasks
   - Filter persists when you close and reopen Kairo

### Using Tags in CLI

```bash
# Add task with tags
kairo add "Sprint planning" -t "work,meeting,planning"

# Filter by tag
kairo list --tag work
kairo list --tag urgent --status open

# View all tasks (tags shown in table)
kairo list --all
```

Tags are case-sensitive and stored as lowercase. They're automatically created when first used.

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

GPL-3.0 license - See LICENSE file for details

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Caution

This is an experimental project built using Claude Code for testing AI coding. Use at your own risk.
