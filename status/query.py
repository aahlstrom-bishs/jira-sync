"""
Status query operations - fetching transitions from Jira.
"""
from typing import TYPE_CHECKING

from .types import Transition
from ..lib.jira_client import get_client

if TYPE_CHECKING:
    from ..config import Config


def fetch_transitions(key: str, config: "Config") -> list[Transition]:
    """
    Get available status transitions for a ticket.

    Args:
        key: The Jira issue key
        config: Configuration with Jira credentials

    Returns:
        List of Transition objects with id, name, and target status
    """
    conn = get_client(config)
    issue = conn.client.issue(key)
    transitions = conn.client.transitions(issue)

    return [
        Transition(
            id=t["id"],
            name=t["name"],
            to_status=t.get("to", {}).get("name"),
        )
        for t in transitions
    ]
