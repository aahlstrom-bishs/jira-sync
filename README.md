# Jira Sync

A Python CLI tool for managing Jira tickets

## Installation

```bash
pip install git+https://github.com/aahlstrom-bishs/jira-sync
```

For development:
```bash
pip install -e .
```

## Example - Finding Tickets

``` bash
jira project --title "ROSM" --list
```
``` json
[
  {
    "key": "SR-3406",
    "status": "Ready",
    "summary": "ROSM - RO DETAIL - Jobs Table"
  },
  {
    "key": "SR-3405",
    "status": "Ready",
    "summary": "ROSM - SR DETAIL - Jobs Table"
  },
  {
    "key": "SR-3404",
    "status": "Ready",
    "summary": "ROSM - Images"
  },
  ...
]
```

``` bash
jira project --title "parts" --list
```
``` json
[
  {
    "key": "SR-3543",
    "status": "Open",
    "summary": "Part Manager refresh issue"
  },
  {
    "key": "SR-3457",
    "status": "Open",
    "summary": "Update parts verification url"
  },
  {
    "key": "SR-3398",
    "status": "Ready",
    "summary": "ROSM - SR DETAIL - Parts"
  },
  ...
]
```

## Example - Workflow

```bash
# Create an epic for a new feature
jira create:epic SR "User Authentication System"
# → {"success": true, "key": "SR-100", ...}

# Create tasks under the epic
jira create:ticket SR "Implement login endpoint" --parent SR-100 --type Task
jira create:ticket SR "Add password reset flow" --parent SR-100 --priority High

# Read the epic and its children
jira epic SR-100

# Add context to a ticket
jira add:comment SR-101 "Using OAuth2 for this implementation"
jira add:label SR-101 backend

# Update ticket status and assignment
jira set:status SR-101 "In Progress"
jira set:assignee SR-101 john.doe@example.com

# Log work
jira add:worklog SR-101 "2h" --comment "Initial API scaffolding"

# Query your queued tickets
jira project SR --status "Ready" --list

# Run JQL queries
jira jql "project = SR AND status = 'In Development' ORDER BY priority DESC"

## JQL - Save a query for reuse
jira jql "project = SR"
### `EXECUTING: ((project = SR) AND assignee = currentUser()) AND status NOT IN ("Done", "Closed")`

jira jql "project = SR" --user "me" --list --save my_sprint
### Config saved to ~\.jira\config.json
### `EXECUTING: ((project = SR) AND assignee = currentUser()) AND status NOT IN ("Done", "Closed")`

## JQL - Run saved query
jira jql my_sprint --list
```

## Quick Reference

### Read Operations

All read commands output JSON to stdout. Commands have shortcuts (e.g., `jira project` = `jira read:project`).

| Command | Shortcut | Description |
|---------|----------|-------------|
| `jira read:ticket SR-1234` | `jira ticket SR-1234` | Display single ticket |
| `jira read:tickets SR-1234 SR-1235` | `jira tickets SR-1234 SR-1235` | Display multiple tickets |
| `jira read:epic SR-500` | `jira epic SR-500` | Display epic and children |
| `jira read:jql "project = SR"` | `jira jql "project = SR"` | Execute JQL query |
| `jira read:project SR` | `jira project SR` | Display project tickets |
| `jira read:transitions SR-1234` | `jira transitions SR-1234` | List available transitions |
| `jira read:comments SR-1234` | `jira comments SR-1234` | Display ticket comments |

#### User Filtering

By default, results are filtered to the current user (configurable via `defaults.jql.user`).

```bash
jira project SR                        # Filter to current user (default)
jira project SR --all-users            # Show all users
jira project SR --user john.doe        # Filter to specific user
```

#### JQL Options

```bash
jira jql "project = SR" --limit 100           # Limit results
jira jql "project = SR" --include-all         # Include excluded statuses
jira jql "project = SR" --all-users           # Show all users
jira jql "project = SR" --save my-query       # Save query for reuse
jira jql my-query                             # Use saved query
```

#### Project Options

```bash
jira project SR --status "In Progress"        # Filter by status
jira project SR --type Story                  # Filter by issue type
jira project SR --title "search text"         # Filter by title
jira project SR --limit 50                    # Limit results
jira project SR --include-all                 # Include excluded statuses
jira project SR --list                        # Show only key, status, summary
```

### Create Operations

| Command | Description |
|---------|-------------|
| `jira create:ticket PROJECT "Summary"` | Create a new ticket |
| `jira create:epic PROJECT "Summary"` | Create a new epic |

#### create:ticket Options

```bash
jira create:ticket SR "Fix login bug"                    # Basic ticket
jira create:ticket SR "New feature" --type Story         # Specify type
jira create:ticket SR "Task" --assignee user@example.com # With assignee
jira create:ticket SR "Child task" --parent SR-100       # Under an epic
jira create:ticket SR "Urgent" --priority High --labels bug urgent
```

| Option | Description |
|--------|-------------|
| `--type` | Issue type (default: Task) |
| `--description` | Description text |
| `--assignee` | Assignee |
| `--priority` | Priority level |
| `--labels` | Labels (space-separated) |
| `--parent` | Parent epic key |

#### create:epic Options

| Option | Description |
|--------|-------------|
| `--description` | Description text |
| `--labels` | Labels (space-separated) |

### Add Operations

| Command | Description |
|---------|-------------|
| `jira add:comment SR-1234 "Comment text"` | Add a comment to a ticket |
| `jira add:label SR-1234 my-label` | Add a label to a ticket |
| `jira add:link SR-1234 SR-5678` | Link two tickets |
| `jira add:worklog SR-1234 "1h 30m"` | Log time on a ticket |

#### add:link Options

```bash
jira add:link SR-1234 SR-5678                  # Default: Relates
jira add:link SR-1234 SR-5678 --type Blocks    # SR-1234 blocks SR-5678
```

Common link types: `Blocks`, `Relates`, `Duplicates`, `Clones`

#### add:worklog Options

```bash
jira add:worklog SR-1234 "2h"                          # Log 2 hours
jira add:worklog SR-1234 "1h 30m" --comment "Code review"
```

### Set Operations

| Command | Description |
|---------|-------------|
| `jira set:status SR-1234 "In Progress"` | Transition ticket to new status |
| `jira set:assignee SR-1234 user@example.com` | Assign ticket to user |
| `jira set:priority SR-1234 High` | Set ticket priority |
| `jira set:labels SR-1234 label1 label2` | Replace all labels on a ticket |

```bash
jira set:assignee SR-1234 none           # Unassign ticket
jira set:labels SR-1234                  # Clear all labels
jira set:labels SR-1234 bug critical     # Replace with new labels
```

### Sync Operations (Coming Soon)

| Command | Description |
|---------|-------------|
| `jira sync:ticket SR-1234` | Sync single ticket to vault |
| `jira sync:tickets SR-1234 SR-1235` | Sync multiple tickets |
| `jira sync:epic SR-500` | Sync epic and children |
| `jira sync:jql "project = SR"` | Sync JQL results |
| `jira sync:project SR` | Sync project tickets |

### Admin Commands

| Command | Description |
|---------|-------------|
| `jira init` | Initialize global config in ~/.jira/ |
| `jira init --project` | Initialize project config in ./.jira/ |
| `jira test` | Test connection to Jira |

### Global Options

| Option | Description |
|--------|-------------|
| `--config, -c` | Path to config file |
| `--env, -e` | Path to .env file |
| `--vault, -v` | Path to vault |
| `--verbose` | Enable verbose output |

## Python API

```python
from jira_sync import Config, load_env
from pathlib import Path

# Load custom .env file
load_env(Path("path/to/.env"))

# Load configuration
config = Config.load()
```

## Setup

### 1. Get a Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Copy the token (you won't see it again)

### 2. Initialize Configuration

```bash
jira init
```

This creates `~/.jira/.env` and `~/.jira/config.json`. Edit `.env` with your credentials.

For project-specific config (overrides global):
```bash
jira init --project
```

### 3. Configure Credentials

Edit `~/.jira/.env`:

```env
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token
```

### 4. Test Connection

```bash
jira test
```

## Configuration

### Config Locations

| Location | Purpose |
|----------|---------|
| `~/.jira/.env` | Global credentials |
| `~/.jira/config.json` | Global settings |
| `./.jira/.env` | Project credentials (overrides global) |
| `./.jira/config.json` | Project settings (overrides global) |

### .env File

```env
# Required
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token

# Optional
VAULT_PATH=/path/to/vault
TICKETS_FOLDER=tickets
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | Your Jira instance URL |
| `JIRA_EMAIL` | Your Jira email |
| `JIRA_API_TOKEN` | Your API token |
| `JIRA_CLOUD_ID` | Cloud ID (optional) |
| `VAULT_PATH` | Path to vault |
| `TICKETS_FOLDER` | Folder name for tickets (default: `tickets`) |

### config.json Settings

```json
{
  "defaults": {
    "project": {
      "key": "SR",
      "user": "me"
    },
    "jql": {
      "max_results": 50,
      "excluded_statuses": ["Done", "Closed"],
      "user": "me"
    }
  },
  "saved_queries": {
    "my_open": "status != Done",
    "sprint": "project = SR AND sprint in openSprints()"
  }
}
```

| Setting | Description |
|---------|-------------|
| `defaults.project.key` | Default project key when not specified |
| `defaults.jql.max_results` | Default result limit (default: 50) |
| `defaults.jql.excluded_statuses` | Statuses to exclude by default |
| `defaults.jql.user` | Default user filter: `me` or `current` or a specific user ID |
| `saved_queries` | Named JQL queries for reuse |

## Output Format (Coming Soon)

When sync operations are implemented, each synced ticket will create a markdown file with:

- **YAML frontmatter** - Structured metadata (status, priority, assignee, dates, etc.)
- **Obsidian tags** - `#status/in-progress`, `#priority/high`, `#type/story`, etc.
- **Wiki-links** - `[[SR-1234]]` for related tickets
- **Clean sections** - Description, related tickets, comments

Example output:

```markdown
---
jira_key: SR-1234
jira_url: https://company.atlassian.net/browse/SR-1234
status: In Progress
priority: High
type: Story
assignee: John Doe
created: 2024-01-15
synced: 2024-01-20 15:30
---

# SR-1234: Implement user dashboard

#status/in-progress #priority/high #type/story

## Description

User dashboard with activity feed and metrics.

## Related Tickets

**Parent:** [[SR-500]] - Main Epic
- Blocks: [[SR-1235]] - API Integration
```
