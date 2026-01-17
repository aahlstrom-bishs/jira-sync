"""
Comment domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import fetch_comments

if TYPE_CHECKING:
    from ..config import Config


def handle_read_comments(config: "Config", args) -> None:
    """
    Display comments for a ticket as JSON.

    Command: read:comments <key>
    """
    comments = fetch_comments(args.key, config)
    output = [comment.to_dict() for comment in comments]
    print(json.dumps(output, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:comments": {
        "handler": handle_read_comments,
        "help": "Display ticket comments as JSON",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., SR-1234)"},
        ],
    },
}
