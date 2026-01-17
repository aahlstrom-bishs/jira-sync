"""
Configuration management for Jira Sync.

Handles loading credentials and settings from environment variables or config files.
Note: .env files are automatically loaded by the package __init__.py
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """Configuration for Jira sync operations."""

    # Jira connection settings
    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_cloud_id: str = ""

    # Vault settings
    vault_path: Path = field(default_factory=lambda: Path.cwd())
    tickets_folder: str = "tickets"

    # Formatting options
    include_comments: bool = True
    include_attachments: bool = True
    include_links: bool = True
    max_description_length: int = 0  # 0 = no limit

    # Default Tag mappings (Jira status -> Obsidian tag)
    status_tags: dict = field(default_factory=lambda: {
        "To Do": "status/todo",
        "In Progress": "status/in-progress",
        "Ready": "status/ready",
        "Done": "status/done",
        "Closed": "status/closed",
    })

    priority_tags: dict = field(default_factory=lambda: {
        "Highest": "priority/highest",
        "High": "priority/high",
        "Medium": "priority/medium",
        "Low": "priority/low",
        "Lowest": "priority/lowest",
    })

    type_tags: dict = field(default_factory=lambda: {
        "Epic": "type/epic",
        "Story": "type/story",
        "Task": "type/task",
        "Bug": "type/bug",
        "Sub-task": "type/subtask",
    })

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            jira_url=os.getenv("JIRA_URL", ""),
            jira_email=os.getenv("JIRA_EMAIL", ""),
            jira_api_token=os.getenv("JIRA_API_TOKEN", ""),
            jira_cloud_id=os.getenv("JIRA_CLOUD_ID", ""),
            vault_path=Path(os.getenv("VAULT_PATH", Path.cwd())),
            tickets_folder=os.getenv("TICKETS_FOLDER", "tickets"),
        )

    @classmethod
    def from_file(cls, config_path: Path) -> "Config":
        """Load configuration from a JSON file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            data = json.load(f)

        # Convert vault_path to Path object
        if "vault_path" in data:
            data["vault_path"] = Path(data["vault_path"])

        return cls(**data)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "Config":
        """
        Load configuration with layered priority:
        1. Specified config file (if provided)
        2. Otherwise: ~/.jira/config.json (global defaults)
           -> merged with {cwd}/.jira/config.json (project overrides)
           -> merged with environment variables (final overrides)
        """
        # If explicit config path provided, use it directly
        if config_path and config_path.exists():
            config = cls.from_file(config_path)
            config._apply_env_overrides()
            return config

        # Start with defaults
        config = cls()

        # Layer 1: Global defaults from ~/.jira/config.json
        home_config = Path.home() / ".jira" / "config.json"
        if home_config.exists():
            config = cls.from_file(home_config)

        # Layer 2: Project overrides from {cwd}/.jira/config.json
        cwd_config = Path.cwd() / ".jira" / "config.json"
        if cwd_config.exists():
            config._apply_file_overrides(cwd_config)

        # Layer 3: Environment variable overrides (from .env files already loaded)
        config._apply_env_overrides()

        return config

    def _apply_env_overrides(self):
        """Apply environment variable overrides to existing config."""
        if os.getenv("JIRA_URL"):
            self.jira_url = os.getenv("JIRA_URL")
        if os.getenv("JIRA_EMAIL"):
            self.jira_email = os.getenv("JIRA_EMAIL")
        if os.getenv("JIRA_API_TOKEN"):
            self.jira_api_token = os.getenv("JIRA_API_TOKEN")
        if os.getenv("JIRA_CLOUD_ID"):
            self.jira_cloud_id = os.getenv("JIRA_CLOUD_ID")

    def _apply_file_overrides(self, config_path: Path):
        """Apply overrides from a config file (only non-empty values)."""
        with open(config_path, "r") as f:
            data = json.load(f)

        if data.get("jira_url"):
            self.jira_url = data["jira_url"]
        if data.get("jira_email"):
            self.jira_email = data["jira_email"]
        if data.get("jira_cloud_id"):
            self.jira_cloud_id = data["jira_cloud_id"]
        if data.get("vault_path"):
            self.vault_path = Path(data["vault_path"])
        if data.get("tickets_folder"):
            self.tickets_folder = data["tickets_folder"]
        if "include_comments" in data:
            self.include_comments = data["include_comments"]
        if "include_attachments" in data:
            self.include_attachments = data["include_attachments"]
        if "include_links" in data:
            self.include_links = data["include_links"]
        if data.get("status_tags"):
            self.status_tags.update(data["status_tags"])
        if data.get("priority_tags"):
            self.priority_tags.update(data["priority_tags"])
        if data.get("type_tags"):
            self.type_tags.update(data["type_tags"])

    def save(self, config_path: Optional[Path] = None):
        """Save configuration to a JSON file."""
        path = config_path or (Path.home() / ".jira" / "config.json")
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "jira_url": self.jira_url,
            "jira_email": self.jira_email,
            # Don't save API token to file for security
            "jira_cloud_id": self.jira_cloud_id,
            "vault_path": str(self.vault_path),
            "tickets_folder": self.tickets_folder,
            "include_comments": self.include_comments,
            "include_attachments": self.include_attachments,
            "include_links": self.include_links,
            "status_tags": self.status_tags,
            "priority_tags": self.priority_tags,
            "type_tags": self.type_tags,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"Config saved to {path}")
        print("Note: JIRA_API_TOKEN should be set via environment variable")

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not self.jira_url:
            errors.append("JIRA_URL is required")
        if not self.jira_email:
            errors.append("JIRA_EMAIL is required")
        if not self.jira_api_token:
            errors.append("JIRA_API_TOKEN is required")

        return errors

    @property
    def tickets_path(self) -> Path:
        """Get the full path to the tickets folder."""
        return self.vault_path / self.tickets_folder

    def get_status_tag(self, status: str) -> str:
        """Get the Obsidian tag for a Jira status."""
        return self.status_tags.get(status, f"status/{status.lower().replace(' ', '-')}")

    def get_priority_tag(self, priority: str) -> str:
        """Get the Obsidian tag for a Jira priority."""
        return self.priority_tags.get(priority, f"priority/{priority.lower()}")

    def get_type_tag(self, issue_type: str) -> str:
        """Get the Obsidian tag for a Jira issue type."""
        return self.type_tags.get(issue_type, f"type/{issue_type.lower().replace(' ', '-')}")
