"""Type definitions for status domain."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Transition:
    """Available status transition."""
    id: str
    name: str
    to_status: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "to_status": self.to_status,
        }
