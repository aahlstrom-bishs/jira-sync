"""
Comment query operations - fetching from Jira.
"""
from typing import TYPE_CHECKING
from datetime import datetime

from .types import JiraComment
from ..lib.jira_client import get_client

if TYPE_CHECKING:
    from ..config import Config


def fetch_comments(key: str, config: "Config") -> list[JiraComment]:
    """
    Get all comments for a ticket.

    Args:
        key: The Jira issue key
        config: Configuration with Jira credentials

    Returns:
        List of JiraComment objects
    """
    conn = get_client(config)
    issue = conn.client.issue(key)
    comments = []

    for comment in conn.client.comments(issue):
        comments.append(
            JiraComment(
                id=comment.id,
                author=getattr(comment.author, "displayName", "Unknown"),
                body=comment.body or "",
                created=_parse_date(comment.created),
                updated=_parse_date(getattr(comment, "updated", None)),
            )
        )

    return comments


def _parse_date(date_str) -> datetime:
    """Parse Jira date string to datetime."""
    if not date_str:
        return None

    if isinstance(date_str, datetime):
        return date_str

    try:
        clean_date = date_str.split(".")[0]
        return datetime.fromisoformat(clean_date)
    except (ValueError, AttributeError):
        return None
