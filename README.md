# Jira Sync

Sync Jira tickets to Obsidian markdown and perform write operations back to Jira.

## Quick Reference

### Read Operations (Display to Terminal)

| Command | Description |
|---------|-------------|
| `python -m jira read:ticket SR-1234` | Display single ticket |
| `python -m jira read:tickets SR-1234 SR-1235` | Display multiple tickets |
| `python -m jira read:epic SR-500` | Display epic and children |
| `python -m jira read:jql "project = SR AND status = Ready"` | Display JQL results |
| `python -m jira read:project SR --status "In Progress"` | Display project tickets |
| `python -m jira read:status SR-1234` | Show current status |
| `python -m jira read:transitions SR-1234` | List available transitions |
| `python -m jira read:comments SR-1234` | Display ticket comments |

### Sync Operations (Save to Vault)

| Command | Description |
|---------|-------------|
| `python -m jira sync:ticket SR-1234` | Sync single ticket |
| `python -m jira sync:tickets SR-1234 SR-1235` | Sync multiple tickets |
| `python -m jira sync:epic SR-500` | Sync epic and children |
| `python -m jira sync:jql "project = SR AND status = Ready"` | Sync JQL results |
| `python -m jira sync:project SR --status "In Progress"` | Sync project tickets |

### Write Operations (Push to Jira)

| Command | Description |
|---------|-------------|
| `python -m jira set:status SR-1234 "In Dev"` | Update status |
| `python -m jira set:description SR-1234 "New text"` | Update description |
| `python -m jira add:comment SR-1234 "Comment text"` | Add comment |
| `python -m jira add:link SR-1234 SR-5678 --type "Blocks"` | Link tickets |

### Admin Commands

| Command | Description |
|---------|-------------|
| `python -m jira test` | Test connection |
| `python -m jira init` | Initialize configuration |
| `python -m jira setup` | Create specs/templates |

## Python API

```python
from jira import JiraSync, JiraClient

# Sync operations
sync = JiraSync()
sync.sync_ticket("SR-1234")
sync.sync_epic("SR-500")
sync.sync_jql('project = SR AND status = "In Progress"')

# Write operations
client = JiraClient()
client.add_comment("SR-1234", "Comment text")
client.update_status("SR-1234", "In Dev")
client.update_description("SR-1234", "New description")
client.link_tickets("SR-1234", "SR-5678", "Relates")

# Get available options
transitions = client.get_transitions("SR-1234")
link_types = client.get_link_types()
```

## Setup

### 1. Get a Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create a new API token
3. Copy the token (you won't see it again)

### 2. Create .env File

Credentials are loaded from `~/.jira/.env` (primary) with fallback to `./.env` in the current directory.

**Option A: Interactive setup (recommended)**

```bash
python -m jira init --interactive
```

This will prompt for your URL, email, and API token, then create `~/.jira/.env`.

**Option B: Command line**

```bash
python -m jira init --url "https://company.atlassian.net" --email "you@company.com" --token "your-token"
```

**Option C: Manual .env file**

Create `~/.jira/.env`:

```env
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token
```

### 3. Test Connection

```bash
python -m jira test
```

### 4. Initialize Vault Structure (Optional)

```bash
python -m jira setup
```

Creates `tickets/SPECS.md` and `tickets/templates/default.md`.

## Configuration

### Credentials Loading Order

1. `~/.jira/.env` (user home - primary)
2. `./.env` (current working directory - fallback/override)
3. Custom `.env` via `--env` flag
4. Explicit environment variables
5. `.jira.json` config file (for non-secret settings)

### .env File

```env
# Required
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token

# Optional
VAULT_PATH=/path/to/obsidian/vault
TICKETS_FOLDER=tickets
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `JIRA_URL` | Your Jira instance URL |
| `JIRA_EMAIL` | Your Jira email |
| `JIRA_API_TOKEN` | Your API token |
| `JIRA_CLOUD_ID` | Cloud ID (optional) |
| `VAULT_PATH` | Path to Obsidian vault |
| `TICKETS_FOLDER` | Folder name for tickets (default: `tickets`) |

### Config File

See `.jira.example.json` for full options including custom tag mappings.

## File Structure

```
vault/
├── tickets/
│   ├── SPECS.md              # Conventions documentation
│   ├── templates/
│   │   └── default.md        # Default ticket template
│   ├── ROSM/                  # Category folder (from epic name)
│   │   ├── ROSM-tickets.md   # Index file
│   │   ├── SR-1234-summary.md
│   │   └── SR-1235-summary.md
│   └── SR-5000-standalone.md  # Uncategorized ticket
```

## Output Format

Each synced ticket creates a markdown file with:

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
