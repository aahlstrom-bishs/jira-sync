"""Type definitions for ticket domain."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class JiraTicket:
    """
    Normalized ticket data from Jira.

    This is the canonical representation of a Jira issue,
    independent of the jira-python library's Issue object.
    """
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
    custom_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "summary": self.summary,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "issue_type": self.issue_type,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "resolved": self.resolved.isoformat() if self.resolved else None,
            "labels": self.labels,
            "components": self.components,
            "fix_versions": self.fix_versions,
            "parent_key": self.parent_key,
            "parent_summary": self.parent_summary,
            "epic_key": self.epic_key,
            "epic_name": self.epic_name,
            "subtasks": self.subtasks,
            "links": self.links,
            "comments": self.comments,
            "attachments": self.attachments,
            "url": self.url,
            "custom_fields": self.custom_fields,
        }
