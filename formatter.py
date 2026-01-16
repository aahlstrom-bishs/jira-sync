"""
Markdown formatter for Obsidian vault.

Converts Jira ticket data to well-formatted markdown with:
- YAML frontmatter for metadata
- Obsidian tags (#status/in-progress, #priority/high)
- Wiki-links for related tickets ([[SR-1234]])
- Clean, scannable structure
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from .client import JiraTicket
from .config import Config
from .lib import sanitize_name, format_size, jira_to_markdown


@dataclass
class FormattedTicket:
    """Result of formatting a ticket."""

    filename: str
    content: str
    category: str


class TicketFormatter:
    """Formats Jira tickets as Obsidian markdown."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the formatter.

        Args:
            config: Configuration object for tag mappings
        """
        self.config = config or Config.load()

    def format_ticket(
        self,
        ticket: JiraTicket,
        category: Optional[str] = None,
        template: Optional[str] = None,
    ) -> FormattedTicket:
        """
        Format a ticket as markdown.

        Args:
            ticket: The ticket to format
            category: Optional category folder (auto-detected if not provided)
            template: Optional template name to use

        Returns:
            FormattedTicket with filename and content
        """
        # Auto-detect category from ticket summary if not provided
        if category is None:
            category = self._detect_category(ticket)

        # Generate filename
        filename = self._generate_filename(ticket)

        # Build markdown content
        content = self._build_markdown(ticket)

        return FormattedTicket(
            filename=filename,
            content=content,
            category=category,
        )

    def format_ticket_list(
        self,
        tickets: list[JiraTicket],
        title: str = "Tickets",
        include_table: bool = True,
        include_categories: bool = True,
    ) -> str:
        """
        Format a list of tickets as a summary markdown file.

        Args:
            tickets: List of tickets to include
            title: Title for the document
            include_table: Include a table view
            include_categories: Group tickets by category

        Returns:
            Markdown content string
        """
        lines = [f"# {title}", ""]

        # Summary section
        lines.extend([
            "## Summary",
            f"- **Total tickets:** {len(tickets)}",
        ])

        if tickets:
            # Get unique values
            statuses = set(t.status for t in tickets if t.status)
            priorities = set(t.priority for t in tickets if t.priority)
            types = set(t.issue_type for t in tickets if t.issue_type)

            if statuses:
                lines.append(f"- **Statuses:** {', '.join(sorted(statuses))}")
            if priorities:
                lines.append(f"- **Priorities:** {', '.join(sorted(priorities))}")
            if types:
                lines.append(f"- **Types:** {', '.join(sorted(types))}")

        lines.append("")

        # Table view
        if include_table and tickets:
            lines.extend(self._build_ticket_table(tickets))
            lines.append("")

        # Category grouping
        if include_categories and tickets:
            lines.extend(self._build_category_sections(tickets))

        # Quick links
        if tickets:
            lines.extend([
                "## Quick Links",
                "",
            ])
            for ticket in tickets[:5]:  # First 5 as examples
                lines.append(f"- [[{ticket.key}]] - {ticket.summary}")

        return "\n".join(lines)

    def _build_markdown(self, ticket: JiraTicket) -> str:
        """Build the full markdown content for a ticket."""
        lines = []

        # YAML frontmatter
        lines.extend(self._build_frontmatter(ticket))

        # Title
        lines.extend([
            f"# {ticket.key}: {ticket.summary}",
            "",
        ])

        # Tags line
        tags = self._build_tags(ticket)
        if tags:
            lines.extend([" ".join(tags), ""])

        # Description
        if ticket.description:
            lines.extend([
                "## Description",
                "",
                jira_to_markdown(ticket.description),
                "",
            ])

        # Links section
        if ticket.links or ticket.parent_key or ticket.subtasks:
            lines.extend(self._build_links_section(ticket))

        # Comments
        if ticket.comments and self.config.include_comments:
            lines.extend(self._build_comments_section(ticket))

        # Attachments
        if ticket.attachments and self.config.include_attachments:
            lines.extend(self._build_attachments_section(ticket))

        return "\n".join(lines)

    def _build_frontmatter(self, ticket: JiraTicket) -> list[str]:
        """Build YAML frontmatter."""
        lines = [
            "---",
            f"jira_key: {ticket.key}",
            f"jira_url: {ticket.url}",
            f"status: {ticket.status}",
            f"priority: {ticket.priority}",
            f"type: {ticket.issue_type}",
        ]

        if ticket.assignee:
            lines.append(f"assignee: {ticket.assignee}")
        if ticket.reporter:
            lines.append(f"reporter: {ticket.reporter}")
        if ticket.created:
            lines.append(f"created: {ticket.created.strftime('%Y-%m-%d')}")
        if ticket.updated:
            lines.append(f"updated: {ticket.updated.strftime('%Y-%m-%d')}")
        if ticket.parent_key:
            lines.append(f"parent: {ticket.parent_key}")
        if ticket.epic_key:
            lines.append(f"epic: {ticket.epic_key}")
        if ticket.labels:
            lines.append(f"labels: [{', '.join(ticket.labels)}]")

        lines.append(f"synced: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.extend(["---", ""])

        return lines

    def _build_tags(self, ticket: JiraTicket) -> list[str]:
        """Build Obsidian tags for the ticket."""
        tags = []

        # Status tag
        if ticket.status:
            tag = self.config.get_status_tag(ticket.status)
            tags.append(f"#{tag}")

        # Priority tag
        if ticket.priority:
            tag = self.config.get_priority_tag(ticket.priority)
            tags.append(f"#{tag}")

        # Type tag
        if ticket.issue_type:
            tag = self.config.get_type_tag(ticket.issue_type)
            tags.append(f"#{tag}")

        # Labels as tags
        for label in ticket.labels:
            clean_label = label.lower().replace(" ", "-")
            tags.append(f"#label/{clean_label}")

        return tags

    def _build_metadata_section(self, ticket: JiraTicket) -> list[str]:
        """Build the metadata section."""
        lines = [
            "## Metadata",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| **Key** | [{ticket.key}]({ticket.url}) |",
            f"| **Status** | {ticket.status} |",
            f"| **Priority** | {ticket.priority} |",
            f"| **Type** | {ticket.issue_type} |",
        ]

        if ticket.assignee:
            lines.append(f"| **Assignee** | {ticket.assignee} |")
        if ticket.reporter:
            lines.append(f"| **Reporter** | {ticket.reporter} |")
        if ticket.created:
            lines.append(f"| **Created** | {ticket.created.strftime('%Y-%m-%d')} |")
        if ticket.updated:
            lines.append(f"| **Updated** | {ticket.updated.strftime('%Y-%m-%d')} |")
        if ticket.components:
            lines.append(f"| **Components** | {', '.join(ticket.components)} |")

        lines.append("")
        return lines

    def _build_links_section(self, ticket: JiraTicket) -> list[str]:
        """Build the related tickets section."""
        lines = ["## Related Tickets", ""]

        # Parent
        if ticket.parent_key:
            lines.append(f"**Parent:** [[{ticket.parent_key}]] - {ticket.parent_summary or ''}")
            lines.append("")

        # Epic
        if ticket.epic_key and ticket.epic_key != ticket.parent_key:
            lines.append(f"**Epic:** [[{ticket.epic_key}]]")
            lines.append("")

        # Issue links
        if ticket.links:
            lines.append("### Links")
            for link in ticket.links:
                direction = link.get("direction", "")
                link_type = link.get("type", "")
                key = link.get("key", "")
                summary = link.get("summary", "")

                if direction == "outward":
                    lines.append(f"- {link_type}: [[{key}]] - {summary}")
                else:
                    lines.append(f"- {link_type} (inward): [[{key}]] - {summary}")
            lines.append("")

        # Subtasks
        if ticket.subtasks:
            lines.append("### Subtasks")
            for subtask in ticket.subtasks:
                lines.append(f"- [[{subtask}]]")
            lines.append("")

        return lines

    def _build_comments_section(self, ticket: JiraTicket) -> list[str]:
        """Build the comments section."""
        if not ticket.comments:
            return []

        lines = ["## Comments", ""]

        for comment in ticket.comments:
            author = comment.get("author", "Unknown")
            body = comment.get("body", "")
            created = comment.get("created", "")

            # Clean Jira markup in comment body
            clean_body = jira_to_markdown(body)

            lines.extend([
                f"### {author} - {created}",
                "",
                "```md",
                clean_body,
                "```",
                "",
            ])

        return lines

    def _build_attachments_section(self, ticket: JiraTicket) -> list[str]:
        """Build the attachments section."""
        if not ticket.attachments:
            return []

        lines = ["## Attachments", ""]

        for att in ticket.attachments:
            filename = att.get("filename", "")
            url = att.get("url", "")
            size = att.get("size", 0)

            size_str = format_size(size)
            lines.append(f"- [{filename}]({url}) ({size_str})")

        lines.append("")
        return lines

    def _build_ticket_table(self, tickets: list[JiraTicket]) -> list[str]:
        """Build a markdown table of tickets."""
        lines = [
            "## Ticket List",
            "",
            "| Key | Summary | Status | Priority | Type |",
            "|-----|---------|--------|----------|------|",
        ]

        for ticket in tickets:
            lines.append(
                f"| {ticket.key} | {ticket.summary} | {ticket.status} | "
                f"{ticket.priority} | {ticket.issue_type} |"
            )

        return lines

    def _build_category_sections(self, tickets: list[JiraTicket]) -> list[str]:
        """Build category-grouped sections."""
        categories = {}

        for ticket in tickets:
            category = self._detect_category(ticket)
            if category not in categories:
                categories[category] = []
            categories[category].append(ticket)

        lines = ["## By Category", ""]

        for category, cat_tickets in sorted(categories.items()):
            lines.extend([
                f"### {category}",
            ])
            for ticket in cat_tickets:
                lines.append(f"- {ticket.key} - {ticket.summary}")
            lines.append("")

        return lines

    def _detect_category(self, ticket: JiraTicket) -> str:
        """Detect category from parent ticket name or issue type."""
        # Use parent name as category if available
        if ticket.parent_summary:
            return sanitize_name(ticket.parent_summary, max_length=30)

        # Fall back to epic name if available
        if ticket.epic_name:
            return sanitize_name(ticket.epic_name, max_length=30)

        # Fall back to issue type
        if ticket.issue_type:
            return ticket.issue_type

        return "General"

    def _generate_filename(self, ticket: JiraTicket) -> str:
        """Generate a safe filename for the ticket."""
        if ticket.summary:
            safe_summary = sanitize_name(ticket.summary, max_length=50, lowercase=True)
            return f"{ticket.key}-{safe_summary}.md"
        return f"{ticket.key}.md"
