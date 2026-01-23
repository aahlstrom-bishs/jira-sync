"""
Status domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from ...lib.jira_client import get_client

if TYPE_CHECKING:
    from ..config import Config


def handle_read_transitions(config: "Config", args) -> None:
    """
    Display available transitions for a ticket as JSON.

    Command: read:transitions <key>
    """
    conn = get_client(config)
    issue = conn.client.issue(args.key)
    transitions = conn.client.transitions(issue)

    output = {
        "key": args.key,
        "current_status": issue.fields.status.name if issue.fields.status else None,
        "transitions": [
            {
                "id": t["id"],
                "name": t["name"],
                "to_status": t.get("to", {}).get("name"),
            }
            for t in transitions
        ],
    }
    print(json.dumps(output, indent=2, default=str))


def handle_set_status(config: "Config", args) -> None:
    """
    Transition ticket to a new status.

    Command: set:status <key> <status>
    """
    conn = get_client(config)
    issue = conn.client.issue(args.key)
    transitions = conn.client.transitions(issue)

    # Find transition by target status name (case-insensitive)
    target = next(
        (t for t in transitions if t["to"]["name"].lower() == args.status.lower()),
        None
    )

    if not target:
        available = [t["to"]["name"] for t in transitions]
        raise ValueError(
            f"Cannot transition to '{args.status}'. Available: {', '.join(available)}"
        )

    conn.client.transition_issue(issue, target["id"])

    print(json.dumps({
        "success": True,
        "key": args.key,
        "status": args.status,
        "transition_id": target["id"],
    }, indent=2))


# Command registry for CLI discovery
COMMANDS = {
    "read:transitions": {
        "handler": handle_read_transitions,
        "help": "Display available status transitions as JSON",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., SR-1234)"},
        ],
    },
    "set:status": {
        "handler": handle_set_status,
        "help": "Transition ticket to new status",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., SR-1234)"},
            {"name": "status", "help": "Target status name"},
        ],
    },
}
