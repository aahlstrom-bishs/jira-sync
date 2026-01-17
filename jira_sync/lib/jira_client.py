"""
Shared JIRA connection wrapper.

Provides a singleton-like connection manager that domains can use
to interact with the Jira API without each creating their own connection.
"""
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

from jira import JIRA

if TYPE_CHECKING:
    from ..config import Config


@dataclass
class JiraConnection:
    """Wrapper around JIRA client with connection info."""
    client: JIRA
    base_url: str
    email: str

    def browse_url(self, key: str) -> str:
        """Get the browse URL for a ticket."""
        return f"{self.base_url}/browse/{key}"


_connection: Optional[JiraConnection] = None


def get_client(config: "Config") -> JiraConnection:
    """
    Get or create a JIRA client connection.

    Args:
        config: Configuration with Jira credentials

    Returns:
        JiraConnection wrapper

    Raises:
        ValueError: If required credentials are missing

    Note: Reuses existing connection if config matches.
    """
    global _connection

    # Validate credentials before attempting connection
    errors = config.validate()
    if errors:
        raise ValueError(f"Missing credentials: {', '.join(errors)}")

    if _connection is None or _connection.base_url != config.jira_url:
        client = JIRA(
            server=config.jira_url,
            basic_auth=(config.jira_email, config.jira_api_token),
            options={"timeout": 5},
        )
        _connection = JiraConnection(
            client=client,
            base_url=config.jira_url,
            email=config.jira_email,
        )

    return _connection


def reset_connection():
    """Reset the cached connection. Useful for testing."""
    global _connection
    _connection = None
