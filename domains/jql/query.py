"""
JQL query operations - executing custom JQL queries.
"""
from typing import TYPE_CHECKING

from ..ticket.types import JiraTicket
from ..ticket.query import _issue_to_ticket
from ...lib.jira_client import get_client

if TYPE_CHECKING:
    from ...config import Config


def execute_jql(
    jql: str,
    config: "Config",
    max_results: int = 50,
    start_at: int = 0,
) -> list[JiraTicket]:
    """
    Search for tickets using JQL.

    Args:
        jql: JQL query string
        config: Configuration with Jira credentials
        max_results: Maximum number of results to return
        start_at: Starting index for pagination

    Returns:
        List of JiraTicket objects
    """
    conn = get_client(config)
    issues = conn.client.search_issues(
        jql,
        maxResults=max_results,
        startAt=start_at,
    )

    return [_issue_to_ticket(issue, conn.base_url) for issue in issues]


def execute_jql_all(jql: str, config: "Config", batch_size: int = 50) -> list[JiraTicket]:
    """
    Search for all tickets matching JQL (handles pagination).

    Args:
        jql: JQL query string
        config: Configuration with Jira credentials
        batch_size: Number of results per API call

    Returns:
        List of all matching JiraTicket objects
    """
    all_tickets = []
    start_at = 0

    while True:
        batch = execute_jql(jql, config, max_results=batch_size, start_at=start_at)
        if not batch:
            break

        all_tickets.extend(batch)
        start_at += len(batch)

        if len(batch) < batch_size:
            break

    return all_tickets
