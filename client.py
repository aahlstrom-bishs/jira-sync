"""
Jira API client wrapper.

Handles authentication and provides methods for fetching tickets, comments,
attachments, and related data from Jira.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from jira import JIRA
from jira.resources import Issue

from .config import Config


@dataclass
class JiraTicket:
    """Normalized ticket data structure."""

    key: str
    summary: str
    description: str = ""
    status: str = ""
    priority: str = ""
    issue_type: str = ""
    assignee: str = ""
    reporter: str = ""
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    resolved: Optional[datetime] = None
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    fix_versions: list[str] = field(default_factory=list)
    parent_key: Optional[str] = None
    parent_summary: Optional[str] = None
    epic_key: Optional[str] = None
    epic_name: Optional[str] = None
    subtasks: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)
    attachments: list[dict] = field(default_factory=list)
    url: str = ""
    custom_fields: dict = field(default_factory=dict)

    @property
    def jira_url(self) -> str:
        """Get the full Jira URL for this ticket."""
        return self.url


@dataclass
class JiraComment:
    """Comment data structure."""

    id: str
    author: str
    body: str
    created: datetime
    updated: Optional[datetime] = None


@dataclass
class JiraAttachment:
    """Attachment data structure."""

    id: str
    filename: str
    author: str
    created: datetime
    size: int
    mime_type: str
    url: str


class JiraClient:
    """Client for interacting with Jira API."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the Jira client.

        Args:
            config: Configuration object. If not provided, loads from env/file.
        """
        self.config = config or Config.load()
        self._client: Optional[JIRA] = None
        self._validate_config()

    def _validate_config(self):
        """Validate configuration before connecting."""
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

    def connect(self) -> JIRA:
        """Establish connection to Jira."""
        if self._client is None:
            self._client = JIRA(
                server=self.config.jira_url,
                basic_auth=(self.config.jira_email, self.config.jira_api_token),
            )
        return self._client

    @property
    def client(self) -> JIRA:
        """Get or create the Jira client."""
        return self.connect()

    def get_ticket(self, ticket_key: str, expand: str = "changelog") -> JiraTicket:
        """
        Fetch a single ticket by key.

        Args:
            ticket_key: The Jira issue key (e.g., "SR-1234")
            expand: Fields to expand in the response

        Returns:
            JiraTicket object with ticket data
        """
        issue = self.client.issue(ticket_key, expand=expand)
        return self._issue_to_ticket(issue)

    def search_tickets(
        self,
        jql: str,
        max_results: int = 50,
        start_at: int = 0,
        fields: Optional[list[str]] = None,
    ) -> list[JiraTicket]:
        """
        Search for tickets using JQL.

        Args:
            jql: JQL query string
            max_results: Maximum number of results to return
            start_at: Starting index for pagination
            fields: Specific fields to fetch (None = all)

        Returns:
            List of JiraTicket objects
        """
        issues = self.client.search_issues(
            jql,
            maxResults=max_results,
            startAt=start_at,
            fields=fields,
        )
        return [self._issue_to_ticket(issue) for issue in issues]

    def search_all_tickets(self, jql: str, batch_size: int = 50) -> list[JiraTicket]:
        """
        Search for all tickets matching JQL (handles pagination).

        Args:
            jql: JQL query string
            batch_size: Number of results per API call

        Returns:
            List of all matching JiraTicket objects
        """
        all_tickets = []
        start_at = 0

        while True:
            batch = self.search_tickets(jql, max_results=batch_size, start_at=start_at)
            if not batch:
                break

            all_tickets.extend(batch)
            start_at += len(batch)

            if len(batch) < batch_size:
                break

        return all_tickets

    def get_epic_tickets(self, epic_key: str) -> list[JiraTicket]:
        """
        Get all tickets belonging to an epic.

        Args:
            epic_key: The epic's issue key

        Returns:
            List of JiraTicket objects in the epic
        """
        # Standard Jira Software epic link field
        jql = f'"Epic Link" = {epic_key} OR parent = {epic_key}'
        return self.search_all_tickets(jql)

    def get_project_tickets(
        self,
        project_key: str,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
    ) -> list[JiraTicket]:
        """
        Get tickets from a project with optional filters.

        Args:
            project_key: The project key (e.g., "SR")
            status: Optional status filter
            issue_type: Optional issue type filter

        Returns:
            List of JiraTicket objects
        """
        jql_parts = [f"project = {project_key}"]

        if status:
            jql_parts.append(f'status = "{status}"')
        if issue_type:
            jql_parts.append(f'issuetype = "{issue_type}"')

        jql = " AND ".join(jql_parts) + " ORDER BY created DESC"
        return self.search_all_tickets(jql)

    def get_comments(self, ticket_key: str) -> list[JiraComment]:
        """
        Get all comments for a ticket.

        Args:
            ticket_key: The Jira issue key

        Returns:
            List of JiraComment objects
        """
        issue = self.client.issue(ticket_key)
        comments = []

        for comment in self.client.comments(issue):
            comments.append(
                JiraComment(
                    id=comment.id,
                    author=getattr(comment.author, "displayName", "Unknown"),
                    body=comment.body or "",
                    created=self._parse_date(comment.created),
                    updated=self._parse_date(getattr(comment, "updated", None)),
                )
            )

        return comments

    def get_attachments(self, ticket_key: str) -> list[JiraAttachment]:
        """
        Get all attachments for a ticket.

        Args:
            ticket_key: The Jira issue key

        Returns:
            List of JiraAttachment objects
        """
        issue = self.client.issue(ticket_key)
        attachments = []

        for attachment in issue.fields.attachment:
            attachments.append(
                JiraAttachment(
                    id=attachment.id,
                    filename=attachment.filename,
                    author=getattr(attachment.author, "displayName", "Unknown"),
                    created=self._parse_date(attachment.created),
                    size=int(attachment.size),
                    mime_type=attachment.mimeType,
                    url=attachment.content,
                )
            )

        return attachments

    def _issue_to_ticket(self, issue: Issue) -> JiraTicket:
        """Convert a Jira Issue object to a JiraTicket."""
        fields = issue.fields

        # Extract basic fields
        ticket = JiraTicket(
            key=issue.key,
            summary=fields.summary or "",
            description=fields.description or "",
            status=getattr(fields.status, "name", "") if fields.status else "",
            priority=getattr(fields.priority, "name", "") if fields.priority else "",
            issue_type=getattr(fields.issuetype, "name", "") if fields.issuetype else "",
            assignee=getattr(fields.assignee, "displayName", "") if fields.assignee else "",
            reporter=getattr(fields.reporter, "displayName", "") if fields.reporter else "",
            created=self._parse_date(fields.created),
            updated=self._parse_date(fields.updated),
            resolved=self._parse_date(getattr(fields, "resolutiondate", None)),
            labels=list(fields.labels) if fields.labels else [],
            url=f"{self.config.jira_url}/browse/{issue.key}",
        )

        # Extract components
        if fields.components:
            ticket.components = [c.name for c in fields.components]

        # Extract fix versions
        if fields.fixVersions:
            ticket.fix_versions = [v.name for v in fields.fixVersions]

        # Extract parent (for subtasks)
        if hasattr(fields, "parent") and fields.parent:
            ticket.parent_key = fields.parent.key
            ticket.parent_summary = getattr(fields.parent.fields, "summary", "")

        # Extract epic link (custom field - may vary by Jira instance)
        epic_link_field = self._get_epic_link_field(fields)
        if epic_link_field:
            ticket.epic_key = epic_link_field

        # Extract subtasks
        if hasattr(fields, "subtasks") and fields.subtasks:
            ticket.subtasks = [st.key for st in fields.subtasks]

        # Extract issue links
        if hasattr(fields, "issuelinks") and fields.issuelinks:
            for link in fields.issuelinks:
                link_data = {
                    "type": link.type.name,
                }
                if hasattr(link, "outwardIssue"):
                    link_data["direction"] = "outward"
                    link_data["key"] = link.outwardIssue.key
                    link_data["summary"] = link.outwardIssue.fields.summary
                elif hasattr(link, "inwardIssue"):
                    link_data["direction"] = "inward"
                    link_data["key"] = link.inwardIssue.key
                    link_data["summary"] = link.inwardIssue.fields.summary
                ticket.links.append(link_data)

        # Extract comments (if available)
        if hasattr(fields, "comment") and fields.comment:
            for comment in fields.comment.comments:
                ticket.comments.append({
                    "author": getattr(comment.author, "displayName", "Unknown"),
                    "body": comment.body or "",
                    "created": str(self._parse_date(comment.created)),
                })

        # Extract attachments (if available)
        if hasattr(fields, "attachment") and fields.attachment:
            for att in fields.attachment:
                ticket.attachments.append({
                    "filename": att.filename,
                    "url": att.content,
                    "size": att.size,
                    "mime_type": att.mimeType,
                })

        return ticket

    def _get_epic_link_field(self, fields) -> Optional[str]:
        """Try to extract epic link from various custom field locations."""
        # Common custom field names for epic link
        epic_field_names = [
            "customfield_10014",  # Common Jira Software field
            "customfield_10008",  # Another common one
            "parent",  # Next-gen projects use parent
        ]

        for field_name in epic_field_names:
            if hasattr(fields, field_name):
                value = getattr(fields, field_name)
                if value:
                    if isinstance(value, str):
                        return value
                    elif hasattr(value, "key"):
                        return value.key

        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse a Jira date string to datetime."""
        if not date_str:
            return None

        try:
            # Jira uses ISO format with timezone
            # Example: "2024-01-15T10:30:00.000+0000"
            if isinstance(date_str, datetime):
                return date_str

            # Remove milliseconds and timezone for simpler parsing
            clean_date = date_str.split(".")[0]
            return datetime.fromisoformat(clean_date)
        except (ValueError, AttributeError):
            return None

    def test_connection(self) -> dict:
        """
        Test the connection to Jira and return server info.

        Returns:
            Dictionary with server information
        """
        try:
            server_info = self.client.server_info()
            return {
                "success": True,
                "server": server_info.get("baseUrl"),
                "version": server_info.get("version"),
                "deployment_type": server_info.get("deploymentType"),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    # ==================== Write Operations ====================

    def add_comment(self, ticket_key: str, body: str) -> str:
        """
        Add a comment to a ticket.

        Args:
            ticket_key: The Jira issue key (e.g., "SR-1234")
            body: The comment text

        Returns:
            The comment ID
        """
        issue = self.client.issue(ticket_key)
        comment = self.client.add_comment(issue, body)
        return comment.id

    def get_transitions(self, ticket_key: str) -> list[dict]:
        """
        Get available status transitions for a ticket.

        Args:
            ticket_key: The Jira issue key

        Returns:
            List of dicts with transition id and name
        """
        issue = self.client.issue(ticket_key)
        transitions = self.client.transitions(issue)
        return [{"id": t["id"], "name": t["name"]} for t in transitions]

    def update_status(self, ticket_key: str, status: str) -> bool:
        """
        Transition a ticket to a new status.

        Args:
            ticket_key: The Jira issue key
            status: The target status name, transition name, or transition ID

        Returns:
            True if successful

        Raises:
            ValueError: If status is not available for this ticket
        """
        issue = self.client.issue(ticket_key)
        transitions = self.client.transitions(issue)

        # Find matching transition by:
        # 1. Exact transition name match
        # 2. Exact transition ID match
        # 3. Target status name (from "to" field)
        # 4. Partial match (e.g., "Ready" matches "Open to Ready")
        transition_id = None
        status_lower = status.lower()

        for t in transitions:
            t_name = t["name"].lower()
            t_id = t["id"]
            # Get target status name if available
            t_to = t.get("to", {}).get("name", "").lower()

            if t_name == status_lower or t_id == status:
                transition_id = t_id
                break
            if t_to == status_lower:
                transition_id = t_id
                break
            if t_name.endswith(status_lower) or t_name.endswith(f"to {status_lower}"):
                transition_id = t_id
                break

        if not transition_id:
            available = [t["name"] for t in transitions]
            raise ValueError(f"Status '{status}' not available. Options: {available}")

        self.client.transition_issue(issue, transition_id)
        return True

    def update_description(self, ticket_key: str, description: str) -> bool:
        """
        Update the description of a ticket.

        Args:
            ticket_key: The Jira issue key
            description: The new description text

        Returns:
            True if successful
        """
        issue = self.client.issue(ticket_key)
        issue.update(fields={"description": description})
        return True

    def link_tickets(
        self,
        from_key: str,
        to_key: str,
        link_type: str = "Relates",
    ) -> bool:
        """
        Create a link between two tickets.

        Args:
            from_key: The source ticket key
            to_key: The target ticket key
            link_type: The type of link (default: "Relates")

        Returns:
            True if successful
        """
        self.client.create_issue_link(
            type=link_type,
            inwardIssue=to_key,
            outwardIssue=from_key,
        )
        return True

    def get_link_types(self) -> list[str]:
        """
        Get available link types.

        Returns:
            List of link type names
        """
        link_types = self.client.issue_link_types()
        return [lt.name for lt in link_types]
