# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
pip install -e .              # Install locally for development
jira test                     # Test Jira connection
jira --help                   # Show available commands
```

No test framework or linting is configured.

## Architecture

Python CLI tool for reading Jira tickets and syncing to Obsidian markdown.

### Entry Point
- `jira_sync/cli.py` - Command dispatcher with dynamic command discovery
- CLI entry: `jira = "jira_sync.cli:main"` (from pyproject.toml)

### Domain-Driven Structure
Each domain in `jira_sync/domains/` owns its commands, queries, and types:

```
jira_sync/domains/
├── ticket/commands.py    # read:ticket, read:tickets
├── comment/commands.py   # read:comments
├── status/commands.py    # read:transitions
├── epic/commands.py      # read:epic
├── project/commands.py   # read:project
├── jql/commands.py       # read:jql, saved queries
└── admin/commands.py     # init, test
```

### Command Pattern
Commands are registered via `COMMANDS` dict in each domain's `commands.py`:

```python
COMMANDS = {
    "read:ticket": {
        "handler": handle_read_ticket,
        "help": "Display single ticket as JSON",
        "args": [{"name": "key", "help": "Ticket key"}],
    },
}
```

The CLI discovers commands by importing `COMMANDS` from each domain module listed in `cli.py:DOMAINS`.

### Aliases
`read:` commands have shortcuts: `jira ticket` = `jira read:ticket` (handled in `cli.py:get_read_aliases`)

### Configuration
- `jira_sync/config.py` - Dataclass-based config with layered loading:
  1. `~/.jira/config.json` (global)
  2. `./.jira/config.json` (project override)
  3. Environment variables (final override)
- Credentials in `.env` files: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`

### Shared Utilities
- `jira_sync/lib/jira_client.py` - Singleton Jira connection wrapper
