"""
Ticket domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import fetch_ticket, fetch_tickets
from ...lib.jira_client import get_client

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

    Command: read:tickets <key1> <key2> ... [--list]
    """
    tickets = fetch_tickets(args.keys, config)
    list_only = getattr(args, "list", False)
    if list_only:
        output = [
            {"key": ticket.key, "status": ticket.status, "summary": ticket.summary, "labels": ticket.labels}
            for ticket in tickets
        ]
    else:
        output = [ticket.to_dict() for ticket in tickets]
    print(json.dumps(output, indent=2, default=str))


def handle_create_ticket(config: "Config", args) -> None:
    """
    Create a new ticket.

    Command: create:ticket <project> <summary> [options]
    """
    conn = get_client(config)

    fields = {
        "project": {"key": args.project},
        "summary": args.summary,
        "issuetype": {"name": args.type},
    }

    if args.description:
        fields["description"] = args.description
    if args.assignee:
        fields["assignee"] = {"name": args.assignee}
    if args.priority:
        fields["priority"] = {"name": args.priority}
    if args.labels:
        fields["labels"] = args.labels
    if args.parent:
        fields["parent"] = {"key": args.parent}

    issue = conn.client.create_issue(fields=fields)

    print(json.dumps({
        "success": True,
        "key": issue.key,
        "id": issue.id,
        "url": conn.browse_url(issue.key),
        "summary": args.summary,
    }, indent=2))


def handle_add_label(config: "Config", args) -> None:
    """
    Add a label to a ticket.

    Command: add:label <key> <label>
    """
    conn = get_client(config)
    issue = conn.client.issue(args.key)
    current = list(issue.fields.labels) if issue.fields.labels else []
    if args.label not in current:
        current.append(args.label)
        issue.update(fields={"labels": current})
    print(json.dumps({
        "success": True,
        "key": args.key,
        "labels": current,
    }, indent=2, default=str))


def handle_add_link(config: "Config", args) -> None:
    """
    Link two tickets.

    Command: add:link <from_key> <to_key> [--type TYPE]
    """
    conn = get_client(config)
    conn.client.create_issue_link(
        type=args.type,
        inwardIssue=args.from_key,
        outwardIssue=args.to_key,
    )
    print(json.dumps({
        "success": True,
        "from": args.from_key,
        "to": args.to_key,
        "type": args.type,
    }, indent=2, default=str))


def handle_set_assignee(config: "Config", args) -> None:
    """
    Assign ticket to user.

    Command: set:assignee <key> <assignee>
    """
    conn = get_client(config)

    assignee = None if args.assignee.lower() == "none" else args.assignee
    conn.client.assign_issue(args.key, assignee)

    print(json.dumps({
        "success": True,
        "key": args.key,
        "assignee": assignee,
    }, indent=2))


def handle_set_priority(config: "Config", args) -> None:
    """
    Set ticket priority.

    Command: set:priority <key> <priority>
    """
    conn = get_client(config)
    issue = conn.client.issue(args.key)
    issue.update(fields={"priority": {"name": args.priority}})

    print(json.dumps({
        "success": True,
        "key": args.key,
        "priority": args.priority,
    }, indent=2))


def handle_set_labels(config: "Config", args) -> None:
    """
    Replace all labels on a ticket.

    Command: set:labels <key> [labels...]
    """
    conn = get_client(config)
    issue = conn.client.issue(args.key)

    labels = args.labels if args.labels else []
    issue.update(fields={"labels": labels})

    print(json.dumps({
        "success": True,
        "key": args.key,
        "labels": labels,
    }, indent=2))


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
            {"name": "--list", "action": "store_true", "help": "Show only key, status, summary, and labels"},
        ],
    },
    "create:ticket": {
        "handler": handle_create_ticket,
        "help": "Create a new ticket",
        "args": [
            {"name": "project", "help": "Project key (e.g., PROJ)"},
            {"name": "summary", "help": "Ticket summary/title"},
            {"name": "--type", "help": "Issue type", "default": "Task"},
            {"name": "--description", "help": "Description", "default": ""},
            {"name": "--assignee", "help": "Assignee", "default": None},
            {"name": "--priority", "help": "Priority", "default": None},
            {"name": "--labels", "nargs": "*", "help": "Labels", "default": []},
            {"name": "--parent", "help": "Parent epic key", "default": None},
        ],
    },
    "add:label": {
        "handler": handle_add_label,
        "help": "Add a label to a ticket",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "label", "help": "Label to add"},
        ],
    },
    "add:link": {
        "handler": handle_add_link,
        "help": "Link two tickets",
        "args": [
            {"name": "from_key", "help": "Source ticket key"},
            {"name": "to_key", "help": "Target ticket key"},
            {"name": "--type", "help": "Link type (Blocks, Relates, Duplicates, Clones)", "default": "Relates"},
        ],
    },
    "set:assignee": {
        "handler": handle_set_assignee,
        "help": "Assign ticket to user",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "assignee", "help": "Assignee (account ID, email, or 'none' to unassign)"},
        ],
    },
    "set:priority": {
        "handler": handle_set_priority,
        "help": "Set ticket priority",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "priority", "help": "Priority name (e.g., High, Medium, Low)"},
        ],
    },
    "set:labels": {
        "handler": handle_set_labels,
        "help": "Replace all labels on a ticket",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "labels", "nargs": "*", "help": "Labels (space-separated, empty to clear)"},
        ],
    },
}
