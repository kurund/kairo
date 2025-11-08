"""Task data models."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskStatus(Enum):
    """Task status enumeration."""

    OPEN = "open"
    COMPLETED = "completed"


@dataclass
class Task:
    """Task model."""

    id: int
    title: str
    description: str
    status: TaskStatus
    week: int  # ISO week number
    year: int  # Year for the week
    created_at: datetime
    completed_at: Optional[datetime] = None
    tags: list[str] = None  # List of tag names
    estimate: Optional[int] = None  # Estimated time in hours
    project: Optional[str] = None  # Project name

    def __post_init__(self):
        """Initialize tags to empty list if None."""
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> dict:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "week": self.week,
            "year": self.year,
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "tags": self.tags,
            "estimate": self.estimate,
            "project": self.project,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            status=TaskStatus(data["status"]),
            week=data["week"],
            year=data["year"],
            created_at=datetime.fromisoformat(data["created_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data["completed_at"]
                else None
            ),
            tags=data.get("tags", []),
            estimate=data.get("estimate"),
            project=data.get("project"),
        )
