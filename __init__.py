"""
Jira Ticket Sync Tools

A Python toolkit for syncing Jira tickets to an Obsidian vault.
Pulls ticket data from Jira and formats it as markdown files.

Usage:
    from jira import JiraSync

    sync = JiraSync()
    sync.sync_ticket("SR-1234")
    sync.sync_epic("SR-3384")
    sync.sync_jql("project = SR AND status = 'In Progress'")
"""

# Load .env files before any other imports
from pathlib import Path
from dotenv import load_dotenv

def _load_env_files():
    """Load .env files from current directory falling back to user home"""
    # Current working directory .env (primary)
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=True)

        # User home directory .env (fallback/override)
    home_env = Path.home() / ".jira" / ".env"
    if home_env.exists():
        load_dotenv(home_env)

_load_env_files()

# Core classes
from .client import JiraClient, JiraTicket, JiraComment, JiraAttachment
from .formatter import TicketFormatter, FormattedTicket
from .sync import JiraSync, SyncResult
from .config import Config

# Utilities from lib
from .lib import (
    sanitize_name,
    format_size,
    jira_to_markdown,
)

__version__ = "1.0.0"
__all__ = [
    # Core classes
    "JiraClient",
    "JiraTicket",
    "JiraComment",
    "JiraAttachment",
    "TicketFormatter",
    "FormattedTicket",
    "JiraSync",
    "SyncResult",
    "Config",
    # Utilities
    "sanitize_name",
    "format_size",
    "jira_to_markdown",
    "load_env",
]

def load_env(env_path: Path = None):
    """
    Manually load a .env file.

    Args:
        env_path: Path to .env file. If None, reloads default locations.
    """
    if env_path:
        load_dotenv(env_path, override=True)
    else:
        _load_env_files()
