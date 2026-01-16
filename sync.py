"""
Main sync orchestration module.

Provides JiraSync facade class that delegates to service modules
for the actual sync operations.
"""

from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .client import JiraClient
from .formatter import TicketFormatter
from .config import Config
from .services import (
    sync_single_ticket,
    sync_multiple_tickets,
    sync_epic as service_sync_epic,
    sync_jql as service_sync_jql,
    sync_project as service_sync_project,
    create_specs_file as service_create_specs_file,
    create_default_template as service_create_default_template,
)


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool
    tickets_synced: int
    files_created: list[Path]
    files_updated: list[Path]
    errors: list[str]
    message: str


class JiraSync:
    """Main class for syncing Jira tickets to Obsidian vault."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the sync manager.

        Args:
            config: Configuration object. If not provided, loads from env/file.
        """
        self.config = config or Config.load()
        self.client = JiraClient(self.config)
        self.formatter = TicketFormatter(self.config)
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist."""
        tickets_path = self.config.tickets_path
        tickets_path.mkdir(parents=True, exist_ok=True)

        # Create templates directory
        templates_path = tickets_path / "templates"
        templates_path.mkdir(exist_ok=True)

    def sync_ticket(
        self,
        ticket_key: str,
        category: Optional[str] = None,
        force: bool = False,
    ) -> SyncResult:
        """
        Sync a single ticket from Jira.

        Args:
            ticket_key: The Jira ticket key (e.g., "SR-1234")
            category: Optional category folder override
            force: Overwrite existing file even if unchanged

        Returns:
            SyncResult with operation details
        """
        return sync_single_ticket(
            self.client, self.formatter, self.config,
            ticket_key, category, force
        )

    def sync_tickets(
        self,
        ticket_keys: list[str],
        category: Optional[str] = None,
    ) -> SyncResult:
        """
        Sync multiple tickets by key.

        Args:
            ticket_keys: List of ticket keys to sync
            category: Optional category folder for all tickets

        Returns:
            SyncResult with aggregated results
        """
        return sync_multiple_tickets(
            self.client, self.formatter, self.config,
            ticket_keys, category
        )

    def sync_jql(
        self,
        jql: str,
        category: Optional[str] = None,
        create_index: bool = True,
        index_name: Optional[str] = None,
    ) -> SyncResult:
        """
        Sync all tickets matching a JQL query.

        Args:
            jql: JQL query string
            category: Optional category folder for all tickets
            create_index: Whether to create an index file
            index_name: Name for the index file

        Returns:
            SyncResult with operation details
        """
        return service_sync_jql(
            self.client, self.formatter, self.config,
            jql, category, create_index, index_name
        )

    def sync_epic(
        self,
        epic_key: str,
        create_folder: bool = True,
        create_index: bool = True,
    ) -> SyncResult:
        """
        Sync all tickets in an epic.

        Args:
            epic_key: The epic's ticket key
            create_folder: Create a dedicated folder for the epic
            create_index: Create an index file for the epic

        Returns:
            SyncResult with operation details
        """
        return service_sync_epic(
            self.client, self.formatter, self.config,
            epic_key, create_folder, create_index
        )

    def sync_project(
        self,
        project_key: str,
        status: Optional[str] = None,
        issue_type: Optional[str] = None,
        create_index: bool = True,
    ) -> SyncResult:
        """
        Sync tickets from a project.

        Args:
            project_key: The project key (e.g., "SR")
            status: Optional status filter
            issue_type: Optional issue type filter
            create_index: Create an index file

        Returns:
            SyncResult with operation details
        """
        return service_sync_project(
            self.client, self.formatter, self.config,
            project_key, status, issue_type, create_index
        )

    def create_specs_file(self) -> Path:
        """Create or update the SPECS.md file with conventions."""
        return service_create_specs_file(self.config)

    def create_default_template(self) -> Path:
        """Create the default ticket template."""
        return service_create_default_template(self.config)
