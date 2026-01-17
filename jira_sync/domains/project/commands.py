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

    Command: read:project [key] [--status STATUS] [--type TYPE] [--title TEXT] [--limit N] [--include-all]
    """
    # Use config default if key not provided
    key = getattr(args, "key", None) or config.get_default("project", "key")
    if not key:
        print("Error: No project key provided and no default configured.")
        print("Set defaults.project.key in config or pass key as argument.")
        return

    status = getattr(args, "status", None)
    issue_type = getattr(args, "type", None)
    summary = getattr(args, "title", None)
    max_results = getattr(args, "limit", None) or config.get_default("jql", "max_results", 50)
    include_all = getattr(args, "include_all", False)

    # Build excluded statuses list
    excluded_statuses = [] if include_all else config.get_default("jql", "excluded_statuses", [])

    tickets = fetch_project_tickets(
        key,
        config,
        status=status,
        issue_type=issue_type,
        summary=summary,
        max_results=max_results,
        excluded_statuses=excluded_statuses,
    )
    output = [ticket.to_dict() for ticket in tickets]
    print(json.dumps(output, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:project": {
        "handler": handle_read_project,
        "help": "Display project tickets as JSON",
        "args": [
            {"name": "key", "nargs": "?", "help": "Project key (e.g., SR). Uses default if not provided."},
            {"name": "--status", "help": "Filter by status"},
            {"name": "--type", "help": "Filter by issue type"},
            {"names": ["--title", "--summary"], "help": "Filter by title/summary text"},
            {"name": "--limit", "type": int, "help": "Max results (uses config default)"},
            {"name": "--include-all", "action": "store_true", "help": "Include all statuses (ignore excluded_statuses)"},
        ],
    },
}
