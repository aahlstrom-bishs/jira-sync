"""
JQL domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import execute_jql

if TYPE_CHECKING:
    from ..config import Config


def handle_read_jql(config: "Config", args) -> None:
    """
    Execute JQL query and display results as JSON.

    Command: read:jql <query> [--limit N]
    """
    max_results = getattr(args, "limit", 50)
    tickets = execute_jql(args.query, config, max_results=max_results)
    output = [ticket.to_dict() for ticket in tickets]
    print(json.dumps(output, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:jql": {
        "handler": handle_read_jql,
        "help": "Execute JQL query and display results as JSON",
        "args": [
            {"name": "query", "help": "JQL query string"},
            {"name": "--limit", "type": int, "default": 50, "help": "Max results (default 50)"},
        ],
    },
}
