"""
Comment domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import fetch_comments
from ...lib.jira_client import get_client

if TYPE_CHECKING:
    from ...config import Config


def handle_read_comments(config: "Config", args) -> None:
    """
    Display comments for a ticket as JSON.

    Command: read:comments <key>
    """
    comments = fetch_comments(args.key, config)
    output = [comment.to_dict() for comment in comments]
    print(json.dumps(output, indent=2, default=str))


def handle_add_comment(config: "Config", args) -> None:
    """
    Add a comment to a ticket.

    Command: add:comment <key> <body>
    """
    conn = get_client(config)
    comment = conn.client.add_comment(args.key, args.body)
    print(json.dumps({
        "success": True,
        "key": args.key,
        "comment_id": comment.id,
        "body": comment.body,
    }, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:comments": {
        "handler": handle_read_comments,
        "help": "Display ticket comments as JSON",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., SR-1234)"},
        ],
    },
    "add:comment": {
        "handler": handle_add_comment,
        "help": "Add a comment to a ticket",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "body", "help": "Comment text"},
        ],
    },
}
