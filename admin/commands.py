"""
Admin domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from jira import JIRA

if TYPE_CHECKING:
    from ..config import Config


def handle_init(args) -> None:
    """
    Create .env template file.

    Command: init
    """
    env_path = Path.cwd() / ".env"

    if env_path.exists():
        print(f".env already exists at {env_path}")
        return

    template = """# Jira API Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Optional: Vault path for synced files
# VAULT_PATH=/path/to/obsidian/vault
# TICKETS_FOLDER=tickets
"""
    env_path.write_text(template)
    print(f"Created .env template at {env_path}")
    print("Edit this file with your Jira credentials.")


def handle_test(config: "Config", args) -> None:
    """
    Test connection to Jira.

    Command: test
    """
    try:
        client = JIRA(
            server=config.jira_url,
            basic_auth=(config.jira_email, config.jira_api_token),
        )
        server_info = client.server_info()
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
        "help": "Create .env template file",
        "args": [],
        "no_config": True,  # Special flag: doesn't require config
    },
    "test": {
        "handler": handle_test,
        "help": "Test connection to Jira",
        "args": [],
    },
}
