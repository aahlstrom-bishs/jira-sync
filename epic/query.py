"""
Epic query operations - fetching epics and their children from Jira.
"""
from typing import TYPE_CHECKING

from ..ticket.types import JiraTicket
from ..ticket.query import fetch_ticket, _issue_to_ticket
from ..lib.jira_client import get_client

if TYPE_CHECKING:
    from ..config import Config


def fetch_epic_children(epic_key: str, config: "Config") -> list[JiraTicket]:
    """
    Get all tickets belonging to an epic.

    Args:
        epic_key: The epic's issue key
        config: Configuration with Jira credentials

    Returns:
        List of JiraTicket objects in the epic
    """
    # Standard Jira Software epic link field query
    jql = f'"Epic Link" = {epic_key} OR parent = {epic_key}'

    conn = get_client(config)
    all_tickets = []
    start_at = 0
    batch_size = 50

    while True:
        issues = conn.client.search_issues(
            jql,
            maxResults=batch_size,
            startAt=start_at,
        )
        if not issues:
            break

        for issue in issues:
            all_tickets.append(_issue_to_ticket(issue, conn.base_url))

        start_at += len(issues)
        if len(issues) < batch_size:
            break

    return all_tickets


def fetch_epic(epic_key: str, config: "Config") -> dict:
    """
    Fetch an epic and all its children.

    Args:
        epic_key: The epic's issue key
        config: Configuration with Jira credentials

    Returns:
        Dict with 'epic' (JiraTicket) and 'children' (list of JiraTicket)
    """
    epic = fetch_ticket(epic_key, config)
    children = fetch_epic_children(epic_key, config)

    return {
        "epic": epic,
        "children": children,
    }
