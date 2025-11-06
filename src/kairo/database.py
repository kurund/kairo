"""Database layer for task storage using SQLite."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Task, TaskStatus
from .utils import get_current_week


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
                week INTEGER NOT NULL,
                year INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT
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

        self.conn.commit()

    def add_task(
        self,
        title: str,
        description: str = "",
        week: Optional[int] = None,
        year: Optional[int] = None,
        tags: list[str] = None,
    ) -> Task:
        """Add a new task.

        Args:
            title: Task title
            description: Task description
            week: ISO week number (defaults to current week)
            year: Year (defaults to current year)
            tags: List of tag names

        Returns:
            Created task
        """
        if week is None or year is None:
            year, week = get_current_week()

        if tags is None:
            tags = []

        created_at = datetime.now()
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO tasks (title, description, status, week, year, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                title,
                description,
                TaskStatus.OPEN.value,
                week,
                year,
                created_at.isoformat(),
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
            show_all: If True, show all tasks regardless of week

        Returns:
            List of tasks
        """
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if not show_all:
            if week is None or year is None:
                year, week = get_current_week()
            query += " AND week = ? AND year = ?"
            params.extend([week, year])

        if status is not None:
            query += " AND status = ?"
            params.append(status.value)

        query += " ORDER BY created_at DESC"

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
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Update task fields.

        Args:
            task_id: Task ID
            title: New title (optional)
            description: New description (optional)
            tags: New list of tags (optional, replaces existing tags)

        Returns:
            True if task was found and updated, False otherwise
        """
        cursor = self.conn.cursor()

        # Update title and/or description
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if updates:
            params.append(task_id)
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)

        # Update tags if provided
        if tags is not None:
            # Remove existing tags
            cursor.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))

            # Add new tags
            for tag_name in tags:
                self._add_tag_to_task(task_id, tag_name)

        self.conn.commit()
        return cursor.rowcount > 0 or tags is not None

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
            Dictionary with task counts
        """
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) as open
            FROM tasks
            WHERE year = ? AND week = ?
        """,
            (TaskStatus.COMPLETED.value, TaskStatus.OPEN.value, year, week),
        )

        row = cursor.fetchone()
        return {
            "total": row["total"],
            "completed": row["completed"],
            "open": row["open"],
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

        query += " ORDER BY tasks.created_at DESC"

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_task(row) for row in rows]

    def close(self):
        """Close database connection."""
        self.conn.close()
