"""
Project query operations - fetching project tickets from Jira.
"""
from typing import Optional, TYPE_CHECKING

from ..ticket.types import JiraTicket
from ..ticket.query import _issue_to_ticket
from ...lib.jira_client import get_client

if TYPE_CHECKING:
    from ...config import Config


def fetch_project_tickets(
    project_key: str,
    config: "Config",
    status: Optional[str] = None,
    issue_type: Optional[str] = None,
    summary: Optional[str] = None,
    max_results: int = 50,
    excluded_statuses: Optional[list[str]] = None,
    assignee: Optional[str] = None,
) -> list[JiraTicket]:
    """
    Get tickets from a project with optional filters.

    Args:
        project_key: The project key (e.g., "SR")
        config: Configuration with Jira credentials
        status: Optional status filter
        issue_type: Optional issue type filter
        max_results: Maximum number of results to return
        excluded_statuses: List of statuses to exclude from results
        assignee: User filter - "currentUser()" for JQL function, user ID string, or None for no filter

    Returns:
        List of JiraTicket objects
    """
    jql_parts = [f"project = {project_key}"]

    if status:
        jql_parts.append(f'status = "{status}"')
    if issue_type:
        jql_parts.append(f'issuetype = "{issue_type}"')
    if summary:
        jql_parts.append(f'summary ~ "{summary}"')
    if assignee:
        if assignee == "currentUser()":
            jql_parts.append("assignee = currentUser()")
        else:
            jql_parts.append(f'assignee = "{assignee}"')
    if excluded_statuses:
        quoted = ', '.join(f'"{s}"' for s in excluded_statuses)
        jql_parts.append(f"status NOT IN ({quoted})")

    jql = " AND ".join(jql_parts) + " ORDER BY created DESC"

    conn = get_client(config)
    issues = conn.client.search_issues(jql, maxResults=max_results)

    return [_issue_to_ticket(issue, conn.base_url) for issue in issues]
