"""
Admin domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from ..lib.jira_client import get_client

if TYPE_CHECKING:
    from ..config import Config


def handle_init(args) -> None:
    """
    Initialize jira-sync configuration.

    By default, creates global config in ~/.jira/
    Use --project to create project-specific config in {cwd}/.jira/

    Command: init [--project]
    """
    # Determine target directory
    if getattr(args, "project", False):
        base_dir = Path.cwd() / ".jira"
        config_type = "project"
    else:
        base_dir = Path.home() / ".jira"
        config_type = "global"

    # Create directory structure
    base_dir.mkdir(parents=True, exist_ok=True)
    tickets_dir = base_dir / "tickets"
    tickets_dir.mkdir(exist_ok=True)

    env_path = base_dir / ".env"
    config_path = base_dir / "config.json"

    # Create .env template if it doesn't exist
    if env_path.exists():
        print(f".env already exists at {env_path}")
    else:
        env_template = """# Jira API Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
"""
        env_path.write_text(env_template)
        print(f"Created .env template at {env_path}")

    # Create config.json template if it doesn't exist
    if config_path.exists():
        print(f"config.json already exists at {config_path}")
    else:
        config_template = {
            "vault_path": str(base_dir),
            "tickets_folder": "tickets",
            "include_comments": True,
            "include_attachments": True,
            "include_links": True,
        }
        config_path.write_text(json.dumps(config_template, indent=2))
        print(f"Created config.json at {config_path}")

    print(f"\nInitialized {config_type} jira-sync config at {base_dir}")
    print("Edit .env with your Jira credentials to get started.")


def handle_test(config: "Config", args) -> None:
    """
    Test connection to Jira.

    Command: test
    """
    try:
        conn = get_client(config)
        server_info = conn.client.server_info()
        result = {
            "success": True,
            "server": server_info.get("baseUrl"),
            "version": server_info.get("version"),
            "deployment_type": server_info.get("deploymentType"),
        }
    except Exception as e:
        result = {
            "success": False,
            "error": str(e),
        }

    print(json.dumps(result, indent=2))


# Command registry for CLI discovery
COMMANDS = {
    "init": {
        "handler": handle_init,
        "help": "Initialize jira-sync config (global by default, --project for cwd)",
        "args": [
            {"name": "--project", "action": "store_true", "help": "Create project-specific config in {cwd}/.jira/"},
        ],
        "no_config": True,  # Special flag: doesn't require config
    },
    "test": {
        "handler": handle_test,
        "help": "Test connection to Jira",
        "args": [],
    },
}
