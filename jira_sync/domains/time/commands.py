"""
Worklog domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from ...lib.jira_client import get_client

if TYPE_CHECKING:
    from ...config import Config


def handle_add_worklog(config: "Config", args) -> None:
    """
    Log time on a ticket.

    Command: add:worklog <key> <time> [--comment COMMENT]
    """
    conn = get_client(config)
    worklog = conn.client.add_worklog(
        issue=args.key,
        timeSpent=args.time,
        comment=args.comment,
    )
    print(json.dumps({
        "success": True,
        "key": args.key,
        "worklog_id": worklog.id,
        "time_spent": args.time,
    }, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "add:worklog": {
        "handler": handle_add_worklog,
        "help": "Log time on a ticket",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "time", "help": "Time spent (e.g., '1h 30m', '2h')"},
            {"name": "--comment", "help": "Work description", "default": None},
        ],
    },
}
