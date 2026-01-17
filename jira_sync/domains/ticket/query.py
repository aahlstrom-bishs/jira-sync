"""
Ticket query operations - fetching from Jira.
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from jira.resources import Issue

from .types import JiraTicket
from ...lib.jira_client import get_client

if TYPE_CHECKING:
    from ...config import Config


def fetch_ticket(key: str, config: "Config", expand: str = "changelog") -> JiraTicket:
    """
    Fetch a single ticket from Jira.

    Args:
        key: Ticket key like "SR-1234"
        config: Configuration with Jira credentials
        expand: Fields to expand (default "changelog")

    Returns:
        JiraTicket object

    Raises:
        JIRAError: If ticket not found or API error
    """
    conn = get_client(config)
    issue = conn.client.issue(key, expand=expand)
    return _issue_to_ticket(issue, conn.base_url)


def fetch_tickets(keys: list[str], config: "Config") -> list[JiraTicket]:
    """
    Fetch multiple tickets by key.

    Args:
        keys: List of ticket keys
        config: Configuration with Jira credentials

    Returns:
        List of JiraTicket objects (in same order as keys)
    """
    if not keys:
        return []

    # Use JQL for efficient bulk fetch
    jql = f"key in ({','.join(keys)})"
    conn = get_client(config)
    issues = conn.client.search_issues(jql, maxResults=len(keys))

    # Build lookup and return in original order
    by_key = {issue.key: _issue_to_ticket(issue, conn.base_url) for issue in issues}
    return [by_key[k] for k in keys if k in by_key]


def _issue_to_ticket(issue: Issue, base_url: str) -> JiraTicket:
    """
    Convert jira-python Issue to our JiraTicket type.

    Args:
        issue: jira-python Issue object
        base_url: Jira server base URL

    Returns:
        JiraTicket dataclass instance
    """
    fields = issue.fields

    ticket = JiraTicket(
        key=issue.key,
        summary=fields.summary or "",
        description=fields.description or "",
        status=getattr(fields.status, "name", "") if fields.status else "",
        priority=getattr(fields.priority, "name", "") if fields.priority else "",
        issue_type=getattr(fields.issuetype, "name", "") if fields.issuetype else "",
        assignee=getattr(fields.assignee, "displayName", "") if fields.assignee else "",
        reporter=getattr(fields.reporter, "displayName", "") if fields.reporter else "",
        created=_parse_date(fields.created),
        updated=_parse_date(fields.updated),
        resolved=_parse_date(getattr(fields, "resolutiondate", None)),
        labels=list(fields.labels) if fields.labels else [],
        url=f"{base_url}/browse/{issue.key}",
    )

    # Components
    if fields.components:
        ticket.components = [c.name for c in fields.components]

    # Fix versions
    if fields.fixVersions:
        ticket.fix_versions = [v.name for v in fields.fixVersions]

    # Parent (for subtasks)
    if hasattr(fields, "parent") and fields.parent:
        ticket.parent_key = fields.parent.key
        ticket.parent_summary = getattr(fields.parent.fields, "summary", "")

    # Epic link
    epic_key = _get_epic_link_field(fields)
    if epic_key:
        ticket.epic_key = epic_key

    # Subtasks
    if hasattr(fields, "subtasks") and fields.subtasks:
        ticket.subtasks = [st.key for st in fields.subtasks]

    # Issue links
    if hasattr(fields, "issuelinks") and fields.issuelinks:
        for link in fields.issuelinks:
            link_data = {"type": link.type.name}
            if hasattr(link, "outwardIssue"):
                link_data["direction"] = "outward"
                link_data["key"] = link.outwardIssue.key
                link_data["summary"] = link.outwardIssue.fields.summary
            elif hasattr(link, "inwardIssue"):
                link_data["direction"] = "inward"
                link_data["key"] = link.inwardIssue.key
                link_data["summary"] = link.inwardIssue.fields.summary
            ticket.links.append(link_data)

    # Comments
    if hasattr(fields, "comment") and fields.comment:
        for comment in fields.comment.comments:
            ticket.comments.append({
                "author": getattr(comment.author, "displayName", "Unknown"),
                "body": comment.body or "",
                "created": str(_parse_date(comment.created)),
            })

    # Attachments
    if hasattr(fields, "attachment") and fields.attachment:
        for att in fields.attachment:
            ticket.attachments.append({
                "filename": att.filename,
                "url": att.content,
                "size": att.size,
                "mime_type": att.mimeType,
            })

    return ticket


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse Jira date string to datetime."""
    if not date_str:
        return None

    if isinstance(date_str, datetime):
        return date_str

    try:
        # Jira format: "2024-01-15T10:30:00.000+0000"
        clean_date = date_str.split(".")[0]
        return datetime.fromisoformat(clean_date)
    except (ValueError, AttributeError):
        return None


def _get_epic_link_field(fields) -> Optional[str]:
    """Extract epic link from various custom field locations."""
    # Common custom field names for epic link
    for field_name in ["customfield_10014", "customfield_10008", "parent"]:
        if hasattr(fields, field_name):
            value = getattr(fields, field_name)
            if value:
                if isinstance(value, str):
                    return value
                elif hasattr(value, "key"):
                    return value.key
    return None
