"""
Jira Sync Tools

A Python toolkit for syncing Jira tickets to an Obsidian vault.
Pulls ticket data from Jira and formats it as markdown files.

Usage:
    python -m jira_sync read:ticket SR-1234
    python -m jira_sync read:jql "project = SR"
"""

# Load .env files before any other imports
from pathlib import Path
from dotenv import load_dotenv


def _load_env_files():
    """Load .env files: global defaults from ~/.jira/, then project overrides from {cwd}/.jira/."""
    # Global defaults from user home directory
    home_env = Path.home() / ".jira" / ".env"
    if home_env.exists():
        load_dotenv(home_env)

    # Project-specific overrides from {cwd}/.jira/
    cwd_env = Path.cwd() / ".jira" / ".env"
    if cwd_env.exists():
        load_dotenv(cwd_env, override=True)


_load_env_files()

# Core exports
from .config import Config

__version__ = "2.0.0"
__all__ = [
    "Config",
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
