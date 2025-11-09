"""Database layer for task storage using SQLite."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from .models import Task, TaskStatus
from .utils import get_current_week

# Sentinel value to distinguish between "don't update" and "set to None"
_UNSET = object()


class Database:
    """SQLite database for task management."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.

        Args:
            db_path: Path to database file. If None, uses ~/.kairo/tasks.db
        """
        if db_path is None:
            db_path = Path.home() / ".kairo" / "tasks.db"

        # Create directory if it doesn't exist
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'open',
                week INTEGER,
                year INTEGER,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                estimate INTEGER,
                project TEXT
            )
        """
        )

        # Create tags table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """
        )

        # Create task_tags junction table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """
        )

        # Migration: Add estimate column if it doesn't exist
        try:
            cursor.execute("SELECT estimate FROM tasks LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE tasks ADD COLUMN estimate INTEGER")

        # Migration: Add project column if it doesn't exist
        try:
            cursor.execute("SELECT project FROM tasks LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE tasks ADD COLUMN project TEXT")

        # Migration: Add position column if it doesn't exist
        # Position is used for manual task ordering (lower = higher in list)
        try:
            cursor.execute("SELECT position FROM tasks LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE tasks ADD COLUMN position INTEGER DEFAULT 0")

        # Migration: Make week and year nullable (for inbox feature)
        # Check if week/year have NOT NULL constraint by trying to insert NULL
        cursor.execute("PRAGMA table_info(tasks)")
        columns = {row[1]: row for row in cursor.fetchall()}

        # If week column has notnull=1, we need to recreate the table
        if columns.get("week") and columns["week"][3] == 1:  # notnull column is at index 3
            # Recreate table without NOT NULL constraints on week/year
            cursor.execute("""
                CREATE TABLE tasks_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'open',
                    week INTEGER,
                    year INTEGER,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    estimate INTEGER,
                    project TEXT,
                    position INTEGER DEFAULT 0
                )
            """)

            # Copy data
            cursor.execute("""
                INSERT INTO tasks_new (id, title, description, status, week, year, created_at, completed_at, estimate, project, position)
                SELECT id, title, description, status, week, year, created_at, completed_at, estimate, project, 0
                FROM tasks
            """)

            # Drop old table and rename new one
            cursor.execute("DROP TABLE tasks")
            cursor.execute("ALTER TABLE tasks_new RENAME TO tasks")

        # One-time migration: Assign positions to existing tasks based on created_at
        # Use a marker table to track if this migration has run
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)

        cursor.execute("SELECT name FROM migrations WHERE name = 'assign_positions'")
        migration_done = cursor.fetchone()

        if not migration_done:
            # Get all unique week/year combinations (including NULL for inbox)
            cursor.execute("""
                SELECT DISTINCT week, year
                FROM tasks
                ORDER BY year, week
            """)
            week_year_groups = cursor.fetchall()

            for group in week_year_groups:
                week = group[0]
                year = group[1]

                # Get ALL tasks for this week/year ordered by created_at
                if week is not None and year is not None:
                    cursor.execute("""
                        SELECT id FROM tasks
                        WHERE week = ? AND year = ?
                        ORDER BY created_at ASC
                    """, (week, year))
                else:
                    # Handle inbox tasks (NULL week/year)
                    cursor.execute("""
                        SELECT id FROM tasks
                        WHERE week IS NULL AND year IS NULL
                        ORDER BY created_at ASC
                    """)

                task_ids = [row[0] for row in cursor.fetchall()]

                # Reassign sequential positions starting from 1 (overwrites existing positions)
                for idx, task_id in enumerate(task_ids, start=1):
                    cursor.execute(
                        "UPDATE tasks SET position = ? WHERE id = ?",
                        (idx, task_id)
                    )

            # Mark migration as done
            cursor.execute(
                "INSERT INTO migrations (name, applied_at) VALUES ('assign_positions', ?)",
                (datetime.now().isoformat(),)
            )

        self.conn.commit()

    def add_task(
        self,
        title: str,
        description: str = "",
        week: Optional[int] = None,
        year: Optional[int] = None,
        tags: list[str] = None,
        estimate: Optional[int] = None,
        project: Optional[str] = None,
        schedule: bool = True,
    ) -> Task:
        """Add a new task.

        Args:
            title: Task title
            description: Task description
            week: ISO week number (used if schedule=True, defaults to current week)
            year: Year (used if schedule=True, defaults to current year)
            tags: List of tag names
            estimate: Estimated time in hours
            project: Project name
            schedule: If True, schedule for a week; if False, add to inbox (week/year=NULL)

        Returns:
            Created task
        """
        if schedule:
            if week is None or year is None:
                year, week = get_current_week()
        else:
            # Inbox task - unscheduled
            week = None
            year = None

        if tags is None:
            tags = []

        created_at = datetime.now()
        cursor = self.conn.cursor()

        # Auto-assign position: Find max position for this week/year and add 1
        # For inbox tasks (week/year = NULL), use separate numbering
        if week is not None and year is not None:
            cursor.execute(
                "SELECT MAX(position) FROM tasks WHERE week = ? AND year = ?",
                (week, year)
            )
        else:
            cursor.execute(
                "SELECT MAX(position) FROM tasks WHERE week IS NULL AND year IS NULL"
            )

        max_position = cursor.fetchone()[0]
        position = (max_position or 0) + 1

        cursor.execute(
            """
            INSERT INTO tasks (title, description, status, week, year, created_at, estimate, project, position)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                title,
                description,
                TaskStatus.OPEN.value,
                week,
                year,
                created_at.isoformat(),
                estimate,
                project,
                position,
            ),
        )

        task_id = cursor.lastrowid

        # Add tags
        for tag_name in tags:
            self._add_tag_to_task(task_id, tag_name)

        self.conn.commit()

        return Task(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.OPEN,
            week=week,
            year=year,
            created_at=created_at,
            completed_at=None,
            tags=tags,
            estimate=estimate,
            project=project,
            position=position,
        )

    def get_task(self, task_id: int) -> Optional[Task]:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_task(row)

    def list_tasks(
        self,
        week: Optional[int] = None,
        year: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        show_all: bool = False,
    ) -> list[Task]:
        """List tasks with optional filters.

        Args:
            week: Filter by week number
            year: Filter by year
            status: Filter by status
            show_all: If True, show all scheduled tasks regardless of week

        Returns:
            List of tasks (excludes inbox tasks with NULL week/year)
        """
        query = "SELECT * FROM tasks WHERE week IS NOT NULL AND year IS NOT NULL"
        params = []

        if not show_all:
            if week is None or year is None:
                year, week = get_current_week()
            query += " AND week = ? AND year = ?"
            params.extend([week, year])

        if status is not None:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY position ASC, created_at ASC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_task(row) for row in rows]

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed.

        Args:
            task_id: Task ID

        Returns:
            True if task was found and updated, False otherwise
        """
        completed_at = datetime.now()
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE tasks
            SET status = ?, completed_at = ?
            WHERE id = ? AND status = ?
        """,
            (
                TaskStatus.COMPLETED.value,
                completed_at.isoformat(),
                task_id,
                TaskStatus.OPEN.value,
            ),
        )

        self.conn.commit()
        return cursor.rowcount > 0

    def reopen_task(self, task_id: int) -> bool:
        """Mark a completed task as open again.

        Args:
            task_id: Task ID

        Returns:
            True if task was found and updated, False otherwise
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE tasks
            SET status = ?, completed_at = NULL
            WHERE id = ? AND status = ?
        """,
            (
                TaskStatus.OPEN.value,
                task_id,
                TaskStatus.COMPLETED.value,
            ),
        )

        self.conn.commit()
        return cursor.rowcount > 0

    def delete_task(self, task_id: int) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if task was found and deleted, False otherwise
        """
        cursor = self.conn.cursor()

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

        self.conn.commit()
        return cursor.rowcount > 0

    def update_task(
        self,
        task_id: int,
        title: Any = _UNSET,
        description: Any = _UNSET,
        tags: Any = _UNSET,
        estimate: Any = _UNSET,
        project: Any = _UNSET,
        position: Any = _UNSET,
        week: Any = _UNSET,
        year: Any = _UNSET,
    ) -> bool:
        """Update task fields.

        Args:
            task_id: Task ID
            title: New title (pass _UNSET to not update, None to clear, or value to set)
            description: New description (pass _UNSET to not update, None to clear, or value to set)
            tags: New list of tags (pass _UNSET to not update, empty list to clear, or value to set)
            estimate: Estimated time in hours (pass _UNSET to not update, None to clear, or value to set)
            project: Project name (pass _UNSET to not update, None to clear, or value to set)
            position: Position in task list (pass _UNSET to not update, or value to set)
            week: Week number (pass _UNSET to not update, None for inbox, or value to schedule)
            year: Year (pass _UNSET to not update, None for inbox, or value to schedule)

        Returns:
            True if task was found and updated, False otherwise
        """
        cursor = self.conn.cursor()

        # Update title and/or description and/or estimate and/or project and/or week/year
        updates = []
        params = []

        if title is not _UNSET:
            updates.append("title = ?")
            params.append(title)

        if description is not _UNSET:
            updates.append("description = ?")
            params.append(description)

        if estimate is not _UNSET:
            updates.append("estimate = ?")
            params.append(estimate)

        if project is not _UNSET:
            updates.append("project = ?")
            params.append(project)

        if position is not _UNSET:
            updates.append("position = ?")
            params.append(position)

        if week is not _UNSET:
            updates.append("week = ?")
            params.append(week)

        if year is not _UNSET:
            updates.append("year = ?")
            params.append(year)

        if updates:
            params.append(task_id)
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

        # Update tags if provided
        if tags is not _UNSET:
            # Remove existing tags
            cursor.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))

            # Add new tags
            for tag_name in tags:
                self._add_tag_to_task(task_id, tag_name)

        self.conn.commit()
        return cursor.rowcount > 0 or tags is not _UNSET

    def rollover_tasks(
        self, from_year: int, from_week: int, to_year: int, to_week: int
    ) -> int:
        """Move incomplete tasks from one week to another.

        Args:
            from_year: Source year
            from_week: Source week
            to_year: Target year
            to_week: Target week

        Returns:
            Number of tasks rolled over
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE tasks
            SET week = ?, year = ?
            WHERE week = ? AND year = ? AND status = ?
        """,
            (to_week, to_year, from_week, from_year, TaskStatus.OPEN.value),
        )

        self.conn.commit()
        return cursor.rowcount

    def rollback_tasks(
        self, from_year: int, from_week: int, to_year: int, to_week: int
    ) -> int:
        """Move incomplete tasks back from next week to previous week.

        Args:
            from_year: Source year (next week)
            from_week: Source week (next week)
            to_year: Target year (previous week)
            to_week: Target week (previous week)

        Returns:
            Number of tasks rolled back
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            UPDATE tasks
            SET week = ?, year = ?
            WHERE week = ? AND year = ? AND status = ?
        """,
            (to_week, to_year, from_week, from_year, TaskStatus.OPEN.value),
        )

        self.conn.commit()
        return cursor.rowcount

    def get_week_stats(self, year: int, week: int) -> dict:
        """Get statistics for a given week.

        Args:
            year: Year
            week: Week number

        Returns:
            Dictionary with task counts and estimate totals
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN estimate IS NOT NULL THEN estimate ELSE 0 END) as total_estimate,
                SUM(CASE WHEN status = ? AND estimate IS NOT NULL THEN estimate ELSE 0 END) as completed_estimate,
                SUM(CASE WHEN status = ? AND estimate IS NOT NULL THEN estimate ELSE 0 END) as open_estimate
            FROM tasks
            WHERE year = ? AND week = ?
        """,
            (TaskStatus.COMPLETED.value, TaskStatus.OPEN.value, TaskStatus.COMPLETED.value, TaskStatus.OPEN.value, year, week),
        )

        row = cursor.fetchone()
        return {
            "total": row["total"],
            "completed": row["completed"],
            "open": row["open"],
            "total_estimate": row["total_estimate"] or 0,
            "completed_estimate": row["completed_estimate"] or 0,
            "open_estimate": row["open_estimate"] or 0,
        }

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert database row to Task object.

        Args:
            row: Database row

        Returns:
            Task object
        """
        task_id = row["id"]
        tags = self._get_task_tags(task_id)

        return Task(
            id=task_id,
            title=row["title"],
            description=row["description"],
            status=TaskStatus(row["status"]),
            week=row["week"],
            year=row["year"],
            created_at=datetime.fromisoformat(row["created_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            tags=tags,
            estimate=row["estimate"] if row["estimate"] else None,
            project=row["project"] if row["project"] else None,
            position=row["position"] if "position" in row.keys() and row["position"] else 0,
        )

    def _get_or_create_tag(self, tag_name: str) -> int:
        """Get or create a tag by name.

        Args:
            tag_name: Tag name

        Returns:
            Tag ID
        """
        cursor = self.conn.cursor()

        # Try to get existing tag
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
        row = cursor.fetchone()

        if row:
            return row["id"]

        # Create new tag
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
        return cursor.lastrowid

    def _add_tag_to_task(self, task_id: int, tag_name: str) -> None:
        """Add a tag to a task.

        Args:
            task_id: Task ID
            tag_name: Tag name
        """
        tag_id = self._get_or_create_tag(tag_name)
        cursor = self.conn.cursor()

        # Add to task_tags (ignore if already exists)
        cursor.execute(
            "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
            (task_id, tag_id),
        )

    def _get_task_tags(self, task_id: int) -> list[str]:
        """Get tags for a task.

        Args:
            task_id: Task ID

        Returns:
            List of tag names
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT tags.name
            FROM tags
            JOIN task_tags ON tags.id = task_tags.tag_id
            WHERE task_tags.task_id = ?
            ORDER BY tags.name
        """,
            (task_id,),
        )

        return [row["name"] for row in cursor.fetchall()]

    def get_all_tags(self) -> list[str]:
        """Get all unique tags.

        Returns:
            List of tag names
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM tags ORDER BY name")
        return [row["name"] for row in cursor.fetchall()]

    def get_all_projects(self) -> list[str]:
        """Get all unique projects.

        Returns:
            List of project names
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT DISTINCT project FROM tasks WHERE project IS NOT NULL ORDER BY project"
        )
        return [row["project"] for row in cursor.fetchall()]

    def list_tasks_by_tag(
        self,
        tag: str,
        week: Optional[int] = None,
        year: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        show_all: bool = False,
    ) -> list[Task]:
        """List tasks filtered by tag.

        Args:
            tag: Tag name to filter by
            week: Filter by week number
            year: Filter by year
            status: Filter by status
            show_all: If True, show all tasks regardless of week

        Returns:
            List of tasks
        """
        query = """
            SELECT DISTINCT tasks.*
            FROM tasks
            JOIN task_tags ON tasks.id = task_tags.task_id
            JOIN tags ON task_tags.tag_id = tags.id
            WHERE tags.name = ?
        """
        params = [tag]

        if not show_all:
            if week is None or year is None:
                year, week = get_current_week()
            query += " AND tasks.week = ? AND tasks.year = ?"
            params.extend([week, year])

        if status is not None:
            query += " AND tasks.status = ?"
            params.append(status.value)

        query += " ORDER BY tasks.position ASC, tasks.created_at ASC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_task(row) for row in rows]

    def list_tasks_by_project(
        self,
        project: str,
        week: Optional[int] = None,
        year: Optional[int] = None,
        status: Optional[TaskStatus] = None,
        show_all: bool = False,
    ) -> list[Task]:
        """List tasks filtered by project.

        Args:
            project: Project name to filter by
            week: Filter by week number
            year: Filter by year
            status: Filter by status
            show_all: If True, show all tasks regardless of week

        Returns:
            List of tasks
        """
        query = "SELECT * FROM tasks WHERE project = ?"
        params = [project]

        if not show_all:
            if week is None or year is None:
                year, week = get_current_week()
            query += " AND week = ? AND year = ?"
            params.extend([week, year])

        if status is not None:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY position ASC, created_at ASC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_task(row) for row in rows]

    def list_inbox_tasks(self, status: Optional[TaskStatus] = None) -> list[Task]:
        """List inbox tasks (unscheduled tasks with week/year = NULL).

        Args:
            status: Filter by status (optional)

        Returns:
            List of inbox tasks
        """
        query = "SELECT * FROM tasks WHERE week IS NULL AND year IS NULL"
        params = []

        if status is not None:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY position ASC, created_at ASC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_task(row) for row in rows]

    def swap_task_positions(self, task_id1: int, task_id2: int) -> bool:
        """Swap positions of two tasks.

        Args:
            task_id1: First task ID
            task_id2: Second task ID

        Returns:
            True if swap was successful, False otherwise
        """
        cursor = self.conn.cursor()

        # Get current positions
        cursor.execute("SELECT position FROM tasks WHERE id = ?", (task_id1,))
        row1 = cursor.fetchone()
        if not row1:
            return False
        pos1 = row1[0]

        cursor.execute("SELECT position FROM tasks WHERE id = ?", (task_id2,))
        row2 = cursor.fetchone()
        if not row2:
            return False
        pos2 = row2[0]

        # Swap positions
        cursor.execute("UPDATE tasks SET position = ? WHERE id = ?", (pos2, task_id1))
        cursor.execute("UPDATE tasks SET position = ? WHERE id = ?", (pos1, task_id2))

        self.conn.commit()
        return True

    def close(self):
        """Close database connection."""
        self.conn.close()
