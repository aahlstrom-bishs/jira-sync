"""
JQL domain commands.

Exports COMMANDS dict for CLI discovery.
"""
import json
from typing import TYPE_CHECKING

from .query import execute_jql

if TYPE_CHECKING:
    from ..config import Config


def handle_read_jql(config: "Config", args) -> None:
    """
    Execute JQL query and display results as JSON.

    Command: read:jql <query> [--limit N] [--include-all]

    The query can be either a JQL string or a saved query name from config.
    """
    query = args.query

    # Check if query is a saved query name
    saved = config.get_saved_query(query)
    if saved:
        query = saved

    # Save query if --save is provided (before adding exclusion clauses)
    if getattr(args, "save", None):
        config.saved_queries[args.save] = query
        config.save()

    max_results = getattr(args, "limit", None) or config.get_default("jql", "max_results", 50)
    include_all = getattr(args, "include_all", False)

    # Auto-append excluded statuses unless --include-all
    if not include_all:
        exclusion = config.build_exclusion_clause()
        if exclusion:
            query = f"({query}) AND {exclusion}"

    tickets = execute_jql(query, config, max_results=max_results)
    output = [ticket.to_dict() for ticket in tickets]
    print(json.dumps(output, indent=2, default=str))


# Command registry for CLI discovery
COMMANDS = {
    "read:jql": {
        "handler": handle_read_jql,
        "help": "Execute JQL query and display results as JSON",
        "args": [
            {"name": "query", "help": "JQL query string or saved query name"},
            {"name": "--limit", "type": int, "help": "Max results (uses config default)"},
            {"name": "--include-all", "action": "store_true", "help": "Include all statuses (ignore excluded_statuses)"},
            {"name": "--save", "help": "Save query with this name for future use"},
        ],
    },
}
