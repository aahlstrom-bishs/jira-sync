"""
Epic domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import fetch_epic
from ...lib.jira_client import get_client
from ...lib.input_helpers import resolve_text_input

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
            {"key": child.key, "status": child.status, "summary": child.summary, "labels": child.labels}
            for child in result["children"]
        ]
    else:
        children = [child.to_dict() for child in result["children"]]
    output = {
        "epic": result["epic"].to_dict(),
        "children": children,
    }
    print(json.dumps(output, indent=2, default=str))


def handle_create_epic(config: "Config", args) -> None:
    """
    Create a new epic.

    Command: create:epic <project> <summary> [description] [options]
    """
    conn = get_client(config)

    fields = {
        "project": {"key": args.project},
        "summary": args.summary,
        "issuetype": {"name": "Epic"},
    }

    description = resolve_text_input(args, text_attr="description", file_attr="file")
    if description:
        fields["description"] = description
    if args.labels:
        fields["labels"] = args.labels

    issue = conn.client.create_issue(fields=fields)

    print(json.dumps({
        "success": True,
        "key": issue.key,
        "id": issue.id,
        "url": conn.browse_url(issue.key),
        "summary": args.summary,
    }, indent=2))


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
    "create:epic": {
        "handler": handle_create_epic,
        "help": "Create a new epic",
        "epilog": """Tips:
  Multi-line descriptions: Use heredoc syntax or --file flag
    jira create:epic PROJ "Summary" <<'EOF'
    Description line 1
    Description line 2
    EOF

    jira create:epic PROJ "Summary" --file description.md

    echo "Description" | jira create:epic PROJ "Summary"

  Formatting: Use Jira wiki syntax, not Markdown
    *bold*           instead of **bold**
    _italic_         instead of *italic*
    {code}...{code}  instead of ```code blocks```""",
        "args": [
            {"name": "project", "help": "Project key (e.g., PROJ)"},
            {"name": "summary", "help": "Epic summary/title"},
            {"name": "description", "nargs": "?", "help": "Description (use - for stdin)"},
            {"names": ["--file", "-f"], "help": "Read description from file"},
            {"name": "--labels", "nargs": "*", "help": "Labels", "default": []},
        ],
    },
}
