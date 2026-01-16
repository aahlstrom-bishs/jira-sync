#!/usr/bin/env python3
"""
Command-line interface for Jira Sync.

Usage:
    python -m jira read:ticket SR-1234
    python -m jira sync:ticket SR-1234
    python -m jira set:status SR-1234 "In Dev"
    python -m jira init
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from .commands import (
    # Admin
    handle_init,
    handle_test,
    handle_setup,
    # Read
    handle_read_ticket,
    handle_read_tickets,
    handle_read_epic,
    handle_read_jql,
    handle_read_project,
    handle_read_status,
    handle_read_transitions,
    handle_read_comments,
    # Sync
    handle_sync_ticket,
    handle_sync_tickets,
    handle_sync_epic,
    handle_sync_jql,
    handle_sync_project,
    # Write
    handle_set_status,
    handle_set_description,
    handle_add_comment,
    handle_add_link,
)
from .commands.base import (
    TICKET_KEY_ARG,
    TICKET_KEYS_ARG,
    CATEGORY_ARG,
    NO_FOLDER_ARG,
    NO_INDEX_ARG,
    INDEX_NAME_ARG,
    STATUS_FILTER_ARG,
    TYPE_FILTER_ARG,
    load_config,
)


# =============================================================================
# Command Registry
# =============================================================================

def add_command(subparsers, name, help_text, args_config):
    """Factory function to create parsers based on verb:noun pattern."""
    parser = subparsers.add_parser(name, help=help_text)
    for arg in args_config:
        names = arg["names"] if isinstance(arg["names"], list) else [arg["names"]]
        kwargs = arg.get("kwargs", {})
        parser.add_argument(*names, **kwargs)
    return parser


# Commands organized by verb:noun pattern
COMMANDS = {
    # Read commands (output to terminal)
    "read:ticket": {
        "help": "Display single ticket",
        "args": [TICKET_KEY_ARG, CATEGORY_ARG],
        "handler": handle_read_ticket,
    },
    "read:tickets": {
        "help": "Display multiple tickets",
        "args": [TICKET_KEYS_ARG, CATEGORY_ARG],
        "handler": handle_read_tickets,
    },
    "read:epic": {
        "help": "Display epic + children",
        "args": [TICKET_KEY_ARG, NO_FOLDER_ARG],
        "handler": handle_read_epic,
    },
    "read:jql": {
        "help": "Display JQL results",
        "args": [
            {"names": "query", "kwargs": {"help": "JQL query string"}},
            CATEGORY_ARG,
        ],
        "handler": handle_read_jql,
    },
    "read:project": {
        "help": "Display project tickets",
        "args": [TICKET_KEY_ARG, STATUS_FILTER_ARG, TYPE_FILTER_ARG],
        "handler": handle_read_project,
    },
    "read:status": {
        "help": "Show current status",
        "args": [TICKET_KEY_ARG],
        "handler": handle_read_status,
    },
    "read:transitions": {
        "help": "List available transitions",
        "args": [TICKET_KEY_ARG],
        "handler": handle_read_transitions,
    },
    "read:comments": {
        "help": "Display ticket comments",
        "args": [TICKET_KEY_ARG],
        "handler": handle_read_comments,
    },
    # Sync commands (save to vault)
    "sync:ticket": {
        "help": "Sync single ticket",
        "args": [TICKET_KEY_ARG, CATEGORY_ARG],
        "handler": handle_sync_ticket,
    },
    "sync:tickets": {
        "help": "Sync multiple tickets",
        "args": [TICKET_KEYS_ARG, CATEGORY_ARG],
        "handler": handle_sync_tickets,
    },
    "sync:epic": {
        "help": "Sync epic + children",
        "args": [TICKET_KEY_ARG, NO_FOLDER_ARG, NO_INDEX_ARG],
        "handler": handle_sync_epic,
    },
    "sync:jql": {
        "help": "Sync JQL results",
        "args": [
            {"names": "query", "kwargs": {"help": "JQL query string"}},
            CATEGORY_ARG,
            NO_INDEX_ARG,
            INDEX_NAME_ARG,
        ],
        "handler": handle_sync_jql,
    },
    "sync:project": {
        "help": "Sync project tickets",
        "args": [TICKET_KEY_ARG, STATUS_FILTER_ARG, TYPE_FILTER_ARG, NO_INDEX_ARG],
        "handler": handle_sync_project,
    },
    # Write commands (modify Jira)
    "set:status": {
        "help": "Update ticket status",
        "args": [
            TICKET_KEY_ARG,
            {"names": "status", "kwargs": {"help": "Target status name"}},
        ],
        "handler": handle_set_status,
    },
    "set:description": {
        "help": "Update description",
        "args": [
            TICKET_KEY_ARG,
            {"names": "description", "kwargs": {"help": "New description text"}},
        ],
        "handler": handle_set_description,
    },
    "add:comment": {
        "help": "Add a comment",
        "args": [
            TICKET_KEY_ARG,
            {"names": "body", "kwargs": {"help": "Comment text"}},
        ],
        "handler": handle_add_comment,
    },
    "add:link": {
        "help": "Link two tickets",
        "args": [
            {"names": "from_key", "kwargs": {"help": "Source ticket key"}},
            {"names": "to_key", "kwargs": {"help": "Target ticket key"}},
            {"names": ["--type", "-t"], "kwargs": {"default": "Relates", "help": "Link type (default: Relates)"}},
        ],
        "handler": handle_add_link,
    },
    # Admin commands
    "init": {
        "help": "Initialize configuration",
        "args": [
            {"names": "--url", "kwargs": {"help": "Jira URL (e.g., https://company.atlassian.net)"}},
            {"names": "--email", "kwargs": {"help": "Jira email"}},
            {"names": "--token", "kwargs": {"help": "Jira API token"}},
            {"names": ["--output", "-o"], "kwargs": {"type": Path, "default": Path.home() / ".jira" / ".env", "help": "Output path for .env file (default: ~/.jira/.env)"}},
            {"names": ["--interactive", "-i"], "kwargs": {"action": "store_true", "help": "Interactive mode - prompt for missing values"}},
        ],
        "handler": handle_init,
        "no_config": True,
    },
    "test": {
        "help": "Test connection",
        "args": [],
        "handler": handle_test,
    },
    "setup": {
        "help": "Create specs/templates",
        "args": [],
        "handler": handle_setup,
    },
}


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="jira",
        description="Sync Jira tickets to Obsidian vault",
    )

    # Global options
    parser.add_argument(
        "--config", "-c",
        type=Path,
        help="Path to config file",
    )
    parser.add_argument(
        "--env", "-e",
        type=Path,
        help="Path to .env file (default: ~/.jira/.env or ./.env)",
    )
    parser.add_argument(
        "--vault", "-v",
        type=Path,
        help="Path to Obsidian vault",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Register all commands from registry
    for cmd_name, cmd_config in COMMANDS.items():
        add_command(subparsers, cmd_name, cmd_config["help"], cmd_config["args"])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load custom .env file if specified
    if hasattr(args, 'env') and args.env:
        if args.env.exists():
            load_dotenv(args.env, override=True)
            if args.verbose:
                print(f"Loaded environment from: {args.env}")
        else:
            print(f"Warning: .env file not found: {args.env}")

    # Get command config
    cmd_config = COMMANDS.get(args.command)
    if not cmd_config:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    # Handle commands that don't need config (like init)
    if cmd_config.get("no_config"):
        handler = cmd_config["handler"]
        return handler(args)

    # Load config
    try:
        config = load_config(args)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Execute command
    try:
        handler = cmd_config["handler"]
        return handler(config, args)
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
