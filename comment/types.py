"""Type definitions for comment domain."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class JiraComment:
    """Comment data structure."""
    id: str
    author: str
    body: str
    created: datetime
    updated: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "author": self.author,
            "body": self.body,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }
