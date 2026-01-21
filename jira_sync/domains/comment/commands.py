"""
Comment domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
import sys
from typing import TYPE_CHECKING

from .query import fetch_comments
from ...lib.jira_client import get_client

if TYPE_CHECKING:
    from ...config import Config


def get_comment_body(args) -> str:
    """Resolve comment body from args, file, or stdin."""
    # File flag takes precedence
    if getattr(args, 'file', None):
        with open(args.file, 'r') as f:
            return f.read().strip()

    # Stdin: explicit '-' or piped input with no body
    if args.body == '-' or (args.body is None and not sys.stdin.isatty()):
        return sys.stdin.read().strip()

    return args.body or ''


def handle_read_comments(config: "Config", args) -> None:
    """
    Display comments for a ticket as JSON.

    Command: read:comments <key>
    """
    comments = fetch_comments(args.key, config)
    output = [comment.to_dict() for comment in comments]
    print(json.dumps(output, indent=2, default=str))


def handle_add_comment(config: "Config", args) -> None:
    """Add a comment to a ticket."""
    body = get_comment_body(args)
    if not body:
        print(json.dumps({"error": "No comment body provided"}, indent=2))
        sys.exit(1)

    conn = get_client(config)
    comment = conn.client.add_comment(args.key, body)
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
        "epilog": """Tips:
  Multi-line comments: Use heredoc syntax or --file flag
    jira add:comment PROJ-123 <<'EOF'
    Line 1
    Line 2
    EOF

    jira add:comment PROJ-123 --file comment.txt

  Formatting: Use Jira wiki syntax, not Markdown
    *bold*           instead of **bold**
    _italic_         instead of *italic*
    -strikethrough-  instead of ~~strikethrough~~
    +underline+      (no markdown equivalent)
    {{monospace}}    instead of `code`
    {code}...{code}  instead of ```code blocks```
    [link|https://]  instead of [link](https://)
    h1. Heading      instead of # Heading
    * bullet         instead of - bullet
    # numbered       instead of 1. numbered
    {quote}...{quote}  for block quotes
    {noformat}...{noformat}  for preformatted text""",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "body", "nargs": "?", "help": "Comment text (use - for stdin)"},
            {"names": ["--file", "-f"], "help": "Read comment from file"},
        ],
    },
}
