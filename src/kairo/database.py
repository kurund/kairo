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
        self.conn.commit()

    def add_task(
        self,
        title: str,
        description: str = "",
        week: Optional[int] = None,
        year: Optional[int] = None,
    ) -> Task:
        """Add a new task.

        Args:
            title: Task title
            description: Task description
            week: ISO week number (defaults to current week)
            year: Year (defaults to current year)

        Returns:
            Created task
        """
        if week is None or year is None:
            year, week = get_current_week()

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

        self.conn.commit()
        task_id = cursor.lastrowid

        return Task(
            id=task_id,
            title=title,
            description=description,
            status=TaskStatus.OPEN,
            week=week,
            year=year,
            created_at=created_at,
            completed_at=None,
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
        return Task(
            id=row["id"],
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
        )

    def close(self):
        """Close database connection."""
        self.conn.close()
