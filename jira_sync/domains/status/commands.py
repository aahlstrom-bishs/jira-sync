"""
Status domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import fetch_transitions

if TYPE_CHECKING:
    from ..config import Config


def handle_read_transitions(config: "Config", args) -> None:
    """
    Display available transitions for a ticket as JSON.

    Command: read:transitions <key>
    """
    transitions = fetch_transitions(args.key, config)
    output = [t.to_dict() for t in transitions]
    print(json.dumps(output, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:transitions": {
        "handler": handle_read_transitions,
        "help": "Display available status transitions as JSON",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., SR-1234)"},
        ],
    },
}
