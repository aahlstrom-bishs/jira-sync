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
            mod = importlib.import_module(f".{domain}.commands", package=__package__)
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
        prog="jira-sync",
        description="Sync Jira tickets to Obsidian vault",
    )

    # Global options
    parser.add_argument("--config", "-c", type=Path, help="Path to config file")
    parser.add_argument("--env", "-e", type=Path, help="Path to .env file")
    parser.add_argument("--vault", "-v", type=Path, help="Path to Obsidian vault")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Register each command
    for name, cmd_config in commands.items():
        subparser = subparsers.add_parser(name, help=cmd_config.get("help", ""))

        for arg in cmd_config.get("args", []):
            # Handle positional vs optional arguments
            arg_name = arg.get("name", arg.get("names"))

            # Build kwargs for add_argument
            kwargs = {}
            for key in ["help", "nargs", "type", "default", "action", "choices"]:
                if key in arg:
                    kwargs[key] = arg[key]

            if arg_name.startswith("-"):
                # Optional argument
                subparser.add_argument(arg_name, **kwargs)
            else:
                # Positional argument
                subparser.add_argument(arg_name, **kwargs)

    return parser


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
