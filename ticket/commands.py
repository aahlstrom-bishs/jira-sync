"""
Ticket domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import fetch_ticket, fetch_tickets

if TYPE_CHECKING:
    from ..config import Config


def handle_read_ticket(config: "Config", args) -> None:
    """
    Display single ticket as JSON.

    Command: read:ticket <key>
    """
    ticket = fetch_ticket(args.key, config)
    print(json.dumps(ticket.to_dict(), indent=2, default=str))


def handle_read_tickets(config: "Config", args) -> None:
    """
    Display multiple tickets as JSON.

    Command: read:tickets <key1> <key2> ...
    """
    tickets = fetch_tickets(args.keys, config)
    output = [ticket.to_dict() for ticket in tickets]
    print(json.dumps(output, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:ticket": {
        "handler": handle_read_ticket,
        "help": "Display single ticket as JSON",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., SR-1234)"},
        ],
    },
    "read:tickets": {
        "handler": handle_read_tickets,
        "help": "Display multiple tickets as JSON",
        "args": [
            {"name": "keys", "nargs": "+", "help": "Ticket keys"},
        ],
    },
}
