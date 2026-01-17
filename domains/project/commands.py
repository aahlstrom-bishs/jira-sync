"""
Project domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import fetch_project_tickets

if TYPE_CHECKING:
    from ...config import Config


def handle_read_project(config: "Config", args) -> None:
    """
    Display project tickets as JSON.

    Command: read:project <key> [--status STATUS] [--type TYPE] [--title TEXT] [--limit N]
    """
    status = getattr(args, "status", None)
    issue_type = getattr(args, "type", None)
    summary = getattr(args, "title", None)
    max_results = getattr(args, "limit", 50)

    tickets = fetch_project_tickets(
        args.key,
        config,
        status=status,
        issue_type=issue_type,
        summary=summary,
        max_results=max_results,
    )
    output = [ticket.to_dict() for ticket in tickets]
    print(json.dumps(output, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:project": {
        "handler": handle_read_project,
        "help": "Display project tickets as JSON",
        "args": [
            {"name": "key", "help": "Project key (e.g., SR)"},
            {"name": "--status", "help": "Filter by status"},
            {"name": "--type", "help": "Filter by issue type"},
            {"names": ["--title", "--summary"], "help": "Filter by title/summary text"},
            {"name": "--limit", "type": int, "default": 50, "help": "Max results (default 50)"},
        ],
    },
}
