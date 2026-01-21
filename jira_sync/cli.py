#!/usr/bin/env python3
"""
CLI for Jira Sync - thin command dispatcher.

Discovers commands from domain modules and dispatches to handlers.
"""
import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .config import Config

# Domains to scan for commands
DOMAINS = [
    "ticket",
    "comment",
    "status",
    "epic",
    "project",
    "jql",
    "admin",
    "time",
]


def discover_commands() -> dict[str, dict]:
    """
    Discover all commands from domain modules.

    Returns:
        Dict mapping command name to config dict with handler, help, args
    """
    commands = {}

    for domain in DOMAINS:
        try:
            # Import relative to this package
            mod = importlib.import_module(f".domains.{domain}.commands", package=__package__)
            if hasattr(mod, "COMMANDS"):
                commands.update(mod.COMMANDS)
        except ImportError as e:
            # Domain not yet implemented - skip silently
            pass

    return commands


def build_parser(commands: dict) -> argparse.ArgumentParser:
    """
    Build argument parser with all discovered commands.

    Args:
        commands: Dict of command configs

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="jira",
        description="Sync Jira tickets to Obsidian vault",
    )

    # Global options
    parser.add_argument("--config", "-c", type=Path, help="Path to config file")
    parser.add_argument("--env", "-e", type=Path, help="Path to .env file")
    parser.add_argument("--vault", "-v", type=Path, help="Path to Obsidian vault")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND", help="Commands")

    # Register each command (sorted to group by action prefix)
    for name, cmd_config in sorted(commands.items()):
        subparser = subparsers.add_parser(
            name,
            help=cmd_config.get("help", ""),
            epilog=cmd_config.get("epilog"),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        for arg in cmd_config.get("args", []):
            # Handle single name or multiple names (aliases)
            names = arg.get("names") or [arg.get("name")]
            if isinstance(names, str):
                names = [names]

            # Build kwargs for add_argument
            kwargs = {}
            for key in ["help", "nargs", "type", "default", "action", "choices"]:
                if key in arg:
                    kwargs[key] = arg[key]

            subparser.add_argument(*names, **kwargs)

    return parser


def get_read_aliases(commands: dict) -> dict[str, str]:
    """Build mapping of aliases to read: commands (e.g., 'ticket' -> 'read:ticket')."""
    aliases = {}
    for cmd_name in commands:
        if cmd_name.startswith("read:"):
            alias = cmd_name[5:]  # Strip "read:" prefix
            aliases[alias] = cmd_name
    return aliases


def load_config(args) -> Config:
    """Load configuration from args and environment."""
    config = Config.load(getattr(args, "config", None))

    if hasattr(args, "vault") and args.vault:
        config.vault_path = args.vault

    return config


def main():
    """Main entry point."""
    # Discover commands
    commands = discover_commands()

    # Build alias map and substitute in sys.argv before parsing
    aliases = get_read_aliases(commands)

    # Find and substitute alias in argv (first non-option arg after script name)
    for i, arg in enumerate(sys.argv[1:], start=1):
        if not arg.startswith("-"):
            if arg in aliases:
                sys.argv[i] = aliases[arg]
            break

    # Build parser
    parser = build_parser(commands)
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load .env if specified
    if hasattr(args, "env") and args.env and args.env.exists():
        load_dotenv(args.env, override=True)

    # Get command config
    cmd_config = commands.get(args.command)
    if not cmd_config:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    # Handle commands that don't need config (like init)
    if cmd_config.get("no_config"):
        try:
            cmd_config["handler"](args)
        except Exception as e:
            print(f"Error: {e}")
            if getattr(args, "verbose", False):
                import traceback
                traceback.print_exc()
            sys.exit(1)
        return

    # Load config and execute
    try:
        config = load_config(args)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    try:
        cmd_config["handler"](config, args)
    except Exception as e:
        print(f"Error: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
