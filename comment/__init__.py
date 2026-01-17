"""Comment domain - comment operations."""
from .types import JiraComment
from .query import fetch_comments

__all__ = [
    "JiraComment",
    "fetch_comments",
]
