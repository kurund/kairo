# Kairo

**Kairo** (Greek: kairos - "the right moment") is a terminal-based task management tool focused on weekly planning. Stay organized with an interactive TUI and automatic task rollover.

## Features

- **Interactive TUI**: Full-featured terminal user interface with keyboard shortcuts
- **Weekly planning**: Organize tasks by ISO week numbers
- **Inbox support**: Collect unscheduled tasks and schedule them when ready
- **Tags & Projects**: Categorize tasks with tags and organize by projects
- **Filtering**: Filter tasks by tag or project (filters persist across sessions)
- **Time estimates**: Track estimated hours for tasks
- **Auto-rollover**: Incomplete tasks automatically move to next week
- **Beautiful output**: Rich terminal formatting with tables and colors
- **Weekly statistics**: Real-time stats and completion tracking with estimates
- **Weekly reports**: Generate planning and completion reports
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

**Task Management:**
- **a** - Add new task
- **e** - Edit selected task
- **c** - Toggle complete/reopen task
- **t** - Toggle task between inbox and current week
- **x** - Delete selected task (with confirmation)
- **d** - View task details

**Filtering & Views:**
- **f** - Show filter menu (filter by tag, project, or clear all filters)
- **i** - Toggle between inbox view and weekly view

**Navigation:**
- **g** - Go to current week
- **←/→** or **h/l** - Navigate between weeks (vim style)
- **↑/↓** or **j/k** - Navigate task list (vim style)

**Reports:**
- **w** - Show weekly plan
- **s** - Show weekly report

**Other:**
- **q** - Quit

All filters persist across sessions.

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
2. Press **a** to add tasks for the week
3. Add tasks with title, description, tags, project, and time estimate
4. Press **i** to toggle to inbox view for unscheduled tasks
5. Press **t** to move tasks between inbox and current week
6. Press **f** to filter by tag or project
7. Navigate with arrow keys or **j/k** (vim style)
8. Press **c** to toggle task completion
9. Press **e** to edit task details
10. Press **g** to jump to current week
11. Press **w** or **s** to view weekly plan/report
12. Check weekly statistics in the left panel
13. Press **←/→** to move between weeks
14. All filters persist across sessions
15. Press **q** to quit

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

## Tags & Projects

Tags and projects help you organize and filter tasks.

### Tags

Tags help you categorize tasks by context. You can assign multiple tags to any task.

**Common Tag Examples:**
- **Context**: `work`, `personal`, `home`
- **Priority**: `urgent`, `important`, `low-priority`
- **Type**: `meeting`, `coding`, `review`, `planning`

**Using Tags in TUI:**
1. Press **a** to add a new task
2. Fill in the title and description
3. In the "Tags" field, enter comma-separated tags: `work, urgent`
4. Tags appear in the task table and details view
5. Press **f** → Select "Filter by Tag"
   - Shows list of all available tags
   - Enter a tag name to filter (e.g., "work")
   - Filter persists when you close and reopen Kairo

**Using Tags in CLI:**
```bash
# Add task with tags
kairo add "Sprint planning" -t "work,meeting,planning"

# Filter by tag
kairo list --tag work
kairo list --tag urgent --status open
```

### Projects

Projects help you group related tasks together. Each task can belong to one project.

**Project Examples:**
- Website Redesign
- API Migration
- Documentation Update
- Q4 Planning

**Using Projects in TUI:**
1. Press **a** to add a new task
2. Enter a project name in the "Project" field
3. Press **f** → Select "Filter by Project"
   - Shows list of all available projects
   - Select a project to filter
   - Filter persists across sessions

**Using Projects in CLI:**
Projects are managed through the TUI. Use tags in CLI for similar functionality.

### Inbox

The inbox is for unscheduled tasks that you want to track but haven't assigned to a specific week yet.

**Using Inbox:**
1. Press **i** to view inbox tasks
2. Press **a** to add tasks (uncheck "Schedule for this week")
3. Press **t** on any inbox task to schedule it to the current week
4. Press **t** on any scheduled task to move it to inbox
5. Press **f** to filter inbox tasks by tag or project

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
