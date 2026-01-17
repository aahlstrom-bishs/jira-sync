"""
Epic domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import fetch_epic

if TYPE_CHECKING:
    from ..config import Config


def handle_read_epic(config: "Config", args) -> None:
    """
    Display epic and its children as JSON.

    Command: read:epic <key>
    """
    result = fetch_epic(args.key, config)

    list_only = getattr(args, "list", False)
    if list_only:
        children = [
            {"key": child.key, "status": child.status, "summary": child.summary}
            for child in result["children"]
        ]
    else:
        children = [child.to_dict() for child in result["children"]]
    output = {
        "epic": result["epic"].to_dict(),
        "children": children,
    }
    print(json.dumps(output, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:epic": {
        "handler": handle_read_epic,
        "help": "Display epic and its children as JSON",
        "args": [
            {"name": "key", "help": "Epic key (e.g., EPIC-123)"},
            {"name": "--list", "action": "store_true", "help": "Show only key, status, and summary"},
        ],
    },
}
