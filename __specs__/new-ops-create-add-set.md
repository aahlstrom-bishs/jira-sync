# Jira CLI Write Commands - Research Document

Reference document for implementing `create:`, `add:`, and `set:` command categories.

---

## Architecture Overview

### Current Structure
```
jira_sync/
├── cli.py                 # Command dispatcher, DOMAINS list
├── config.py              # Config loading
├── lib/
│   └── jira_client.py     # Singleton Jira connection
└── domains/
    ├── ticket/            # read:ticket, read:tickets
    ├── comment/           # read:comments
    ├── status/            # read:transitions
    ├── epic/              # read:epic
    ├── project/           # read:project
    ├── jql/               # read:jql
    └── admin/             # init, test
```

### New Domains to Create
```
jira_sync/domains/
├── create/                # create:ticket, create:epic
├── add/                   # add:comment, add:label, add:link, add:worklog
└── set/                   # set:status, set:assignee, set:priority, set:labels
```

### Registration
Add to `DOMAINS` list in `cli.py`:
```python
DOMAINS = [
    "ticket", "comment", "status", "epic", "project", "jql", "admin",
    "create", "add", "set"  # NEW
]
```

---

## Command Pattern Reference

### Standard Command Structure
```python
# domains/{domain}/commands.py

from jira_sync.config import Config
from jira_sync.lib.jira_client import get_client
import json

def handle_command(config: Config, args) -> None:
    conn = get_client(config)
    # ... logic ...
    print(json.dumps(result, indent=2, default=str))

COMMANDS = {
    "verb:noun": {
        "handler": handle_command,
        "help": "One-line description",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "--optional", "help": "Optional flag", "action": "store_true"},
            {"name": "--value", "help": "Optional value", "default": None},
        ],
    },
}
```

### Domain File Structure
Each domain folder contains:
- `__init__.py` - Empty or exports
- `commands.py` - COMMANDS dict and handlers (required)
- `query.py` - API interaction logic (optional, can inline in commands.py for simple cases)
- `types.py` - Dataclasses for domain objects (optional)

---

## Jira Python Library Methods

### Connection Access
```python
from jira_sync.lib.jira_client import get_client

conn = get_client(config)
client = conn.client  # jira.JIRA instance
```

### Methods by Command

| Command | Jira Method | Notes |
|---------|-------------|-------|
| `create:ticket` | `client.create_issue(fields={...})` | Returns created Issue |
| `create:epic` | `client.create_issue(fields={...})` | Same as ticket, different issuetype |
| `add:comment` | `client.add_comment(issue, body)` | Returns Comment |
| `add:label` | `issue.update(fields={"labels": [...]})` | Fetch first, append, update |
| `add:link` | `client.create_issue_link(type, inward, outward)` | Link types: "Blocks", "Relates", etc. |
| `add:worklog` | `client.add_worklog(issue, timeSpent=...)` | timeSpent format: "1h 30m" |
| `set:status` | `client.transition_issue(issue, transition_id)` | Must lookup transition ID first |
| `set:assignee` | `client.assign_issue(issue, assignee)` | accountId or None to unassign |
| `set:priority` | `issue.update(fields={"priority": {"name": ...}})` | Priority name string |
| `set:labels` | `issue.update(fields={"labels": [...]})` | Replaces all labels |

---

## Ticket 1: `add:` Commands

**Scope:** 4 commands - comment, label, link, worklog

### add:comment
```python
COMMANDS = {
    "add:comment": {
        "handler": handle_add_comment,
        "help": "Add a comment to a ticket",
        "args": [
            {"name": "key", "help": "Ticket key (e.g., PROJ-123)"},
            {"name": "body", "help": "Comment text"},
        ],
    },
}

def handle_add_comment(config: Config, args) -> None:
    conn = get_client(config)
    comment = conn.client.add_comment(args.key, args.body)
    print(json.dumps({
        "success": True,
        "key": args.key,
        "comment_id": comment.id,
        "body": comment.body,
    }, indent=2))
```

### add:label
```python
COMMANDS = {
    "add:label": {
        "handler": handle_add_label,
        "help": "Add a label to a ticket",
        "args": [
            {"name": "key", "help": "Ticket key"},
            {"name": "label", "help": "Label to add"},
        ],
    },
}

def handle_add_label(config: Config, args) -> None:
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
    }, indent=2))
```

### add:link
```python
COMMANDS = {
    "add:link": {
        "handler": handle_add_link,
        "help": "Link two tickets",
        "args": [
            {"name": "from_key", "help": "Source ticket key"},
            {"name": "to_key", "help": "Target ticket key"},
            {"name": "--type", "help": "Link type", "default": "Relates"},
        ],
    },
}

def handle_add_link(config: Config, args) -> None:
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
    }, indent=2))
```

**Common link types:** "Blocks", "Relates", "Duplicates", "Clones"

### add:worklog
```python
COMMANDS = {
    "add:worklog": {
        "handler": handle_add_worklog,
        "help": "Log time on a ticket",
        "args": [
            {"name": "key", "help": "Ticket key"},
            {"name": "time", "help": "Time spent (e.g., '1h 30m', '2h')"},
            {"name": "--comment", "help": "Work description", "default": None},
        ],
    },
}

def handle_add_worklog(config: Config, args) -> None:
    conn = get_client(config)
    worklog = conn.client.add_worklog(
        issue=args.key,
        timeSpent=args.time,
        comment=args.comment,
    )
    print(json.dumps({
        "success": True,
        "key": args.key,
        "worklog_id": worklog.id,
        "time_spent": args.time,
    }, indent=2))
```

### Files to Create
```
jira_sync/domains/add/
├── __init__.py
└── commands.py
```

---

## Ticket 2: `set:` Commands

**Scope:** 4 commands - status, assignee, priority, labels

### set:status
Most complex - requires transition lookup.

```python
COMMANDS = {
    "set:status": {
        "handler": handle_set_status,
        "help": "Transition ticket to new status",
        "args": [
            {"name": "key", "help": "Ticket key"},
            {"name": "status", "help": "Target status name"},
        ],
    },
}

def handle_set_status(config: Config, args) -> None:
    conn = get_client(config)
    issue = conn.client.issue(args.key)
    transitions = conn.client.transitions(issue)

    # Find transition by target status name (case-insensitive)
    target = next(
        (t for t in transitions
         if t["to"]["name"].lower() == args.status.lower()),
        None
    )

    if not target:
        available = [t["to"]["name"] for t in transitions]
        raise ValueError(
            f"Cannot transition to '{args.status}'. "
            f"Available: {', '.join(available)}"
        )

    conn.client.transition_issue(issue, target["id"])

    print(json.dumps({
        "success": True,
        "key": args.key,
        "status": args.status,
        "transition_id": target["id"],
    }, indent=2))
```

### set:assignee
```python
COMMANDS = {
    "set:assignee": {
        "handler": handle_set_assignee,
        "help": "Assign ticket to user",
        "args": [
            {"name": "key", "help": "Ticket key"},
            {"name": "assignee", "help": "Assignee (account ID, email, or 'none')"},
        ],
    },
}

def handle_set_assignee(config: Config, args) -> None:
    conn = get_client(config)

    assignee = None if args.assignee.lower() == "none" else args.assignee
    conn.client.assign_issue(args.key, assignee)

    print(json.dumps({
        "success": True,
        "key": args.key,
        "assignee": assignee,
    }, indent=2))
```

### set:priority
```python
COMMANDS = {
    "set:priority": {
        "handler": handle_set_priority,
        "help": "Set ticket priority",
        "args": [
            {"name": "key", "help": "Ticket key"},
            {"name": "priority", "help": "Priority name (e.g., High, Medium, Low)"},
        ],
    },
}

def handle_set_priority(config: Config, args) -> None:
    conn = get_client(config)
    issue = conn.client.issue(args.key)
    issue.update(fields={"priority": {"name": args.priority}})

    print(json.dumps({
        "success": True,
        "key": args.key,
        "priority": args.priority,
    }, indent=2))
```

### set:labels
Replaces all labels (vs `add:label` which appends).

```python
COMMANDS = {
    "set:labels": {
        "handler": handle_set_labels,
        "help": "Replace all labels on a ticket",
        "args": [
            {"name": "key", "help": "Ticket key"},
            {"name": "labels", "nargs": "*", "help": "Labels (space-separated, empty to clear)"},
        ],
    },
}

def handle_set_labels(config: Config, args) -> None:
    conn = get_client(config)
    issue = conn.client.issue(args.key)

    labels = args.labels if args.labels else []
    issue.update(fields={"labels": labels})

    print(json.dumps({
        "success": True,
        "key": args.key,
        "labels": labels,
    }, indent=2))
```

### Files to Create
```
jira_sync/domains/set/
├── __init__.py
└── commands.py
```

---

## Ticket 3: `create:` Commands

**Scope:** 2 commands - ticket, epic

### Field Discovery
Projects have different required/optional fields. Consider adding a helper command or using `createmeta`:

```python
# Optional: discover fields for a project
meta = conn.client.createmeta(
    projectKeys="PROJ",
    issuetypeNames="Task",
    expand="projects.issuetypes.fields"
)
```

### create:ticket
```python
COMMANDS = {
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
}

def handle_create_ticket(config: Config, args) -> None:
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
        "url": f"{config.jira_url}/browse/{issue.key}",
        "summary": args.summary,
    }, indent=2))
```

### create:epic
```python
COMMANDS = {
    "create:epic": {
        "handler": handle_create_epic,
        "help": "Create a new epic",
        "args": [
            {"name": "project", "help": "Project key"},
            {"name": "summary", "help": "Epic summary/title"},
            {"name": "--description", "help": "Description", "default": ""},
            {"name": "--labels", "nargs": "*", "help": "Labels", "default": []},
        ],
    },
}

def handle_create_epic(config: Config, args) -> None:
    conn = get_client(config)

    fields = {
        "project": {"key": args.project},
        "summary": args.summary,
        "issuetype": {"name": "Epic"},
    }

    if args.description:
        fields["description"] = args.description
    if args.labels:
        fields["labels"] = args.labels

    # Note: Some Jira instances require "Epic Name" custom field
    # fields["customfield_10011"] = args.summary  # Epic Name field

    issue = conn.client.create_issue(fields=fields)

    print(json.dumps({
        "success": True,
        "key": issue.key,
        "id": issue.id,
        "url": f"{config.jira_url}/browse/{issue.key}",
        "summary": args.summary,
    }, indent=2))
```

### Epic Name Custom Field
Some Jira instances require an "Epic Name" custom field. This varies by instance:
- Cloud: Usually `customfield_10011`
- Server: May differ

Options:
1. Hardcode common field ID
2. Add `--epic-name` argument
3. Auto-discover via `createmeta`
4. Document as instance-specific configuration

### Files to Create
```
jira_sync/domains/create/
├── __init__.py
└── commands.py
```

---

## Error Handling Patterns

### Standard Error Response
```python
# Errors should raise exceptions - cli.py catches them
raise ValueError(f"Cannot transition to '{status}'. Available: {available}")
raise ValueError(f"User '{assignee}' not found")
raise ValueError(f"Project '{project}' not found or access denied")
```

### Validation Helpers
```python
def validate_issue_exists(client, key: str):
    """Raises JIRAError if issue doesn't exist."""
    try:
        return client.issue(key)
    except Exception as e:
        raise ValueError(f"Issue {key} not found: {e}")

def validate_transition_available(client, issue, target_status: str):
    """Returns transition dict or raises ValueError."""
    transitions = client.transitions(issue)
    target = next(
        (t for t in transitions if t["to"]["name"].lower() == target_status.lower()),
        None
    )
    if not target:
        available = [t["to"]["name"] for t in transitions]
        raise ValueError(
            f"Cannot transition to '{target_status}'. Available: {', '.join(available)}"
        )
    return target
```

---

## Output Format Standards

All write commands should return JSON with:
- `success: true` - Operation completed
- `key` - Affected ticket key
- Relevant data from the operation

```json
{
  "success": true,
  "key": "PROJ-123",
  "status": "In Progress"
}
```

---

## Testing Checklist

### add: Commands
- [ ] `jira add:comment PROJ-123 "Test comment"` - verify comment appears
- [ ] `jira add:label PROJ-123 test-label` - verify label added, not duplicated
- [ ] `jira add:link PROJ-123 PROJ-456` - verify link created
- [ ] `jira add:link PROJ-123 PROJ-456 --type Blocks` - verify link type
- [ ] `jira add:worklog PROJ-123 "1h 30m"` - verify worklog recorded

### set: Commands
- [ ] `jira set:status PROJ-123 "In Progress"` - verify transition
- [ ] `jira set:status PROJ-123 "Invalid"` - verify error with available statuses
- [ ] `jira set:assignee PROJ-123 user@example.com` - verify assignment
- [ ] `jira set:assignee PROJ-123 none` - verify unassignment
- [ ] `jira set:priority PROJ-123 High` - verify priority changed
- [ ] `jira set:labels PROJ-123 label1 label2` - verify labels replaced
- [ ] `jira set:labels PROJ-123` - verify labels cleared

### create: Commands
- [ ] `jira create:ticket PROJ "Test ticket"` - verify created
- [ ] `jira create:ticket PROJ "Test" --type Bug` - verify type
- [ ] `jira create:ticket PROJ "Test" --assignee user` - verify assignee
- [ ] `jira create:epic PROJ "Test epic"` - verify epic created
- [ ] `jira create:ticket PROJ "Child" --parent PROJ-100` - verify parent link

---

## Implementation Order

**Recommended sequence:**

1. **Ticket 1: `add:` commands** (lowest risk)
   - Create `domains/add/` folder
   - Implement 4 commands
   - Add "add" to DOMAINS list
   - Test all commands

2. **Ticket 2: `set:` commands** (medium complexity)
   - Create `domains/set/` folder
   - Implement 4 commands (status first, it's the trickiest)
   - Add "set" to DOMAINS list
   - Test all commands

3. **Ticket 3: `create:` commands** (most complex)
   - Create `domains/create/` folder
   - Implement 2 commands
   - Handle Epic Name custom field edge case
   - Add "create" to DOMAINS list
   - Test all commands

---

## Reference: Existing Command Examples

See these files for implementation patterns:
- [ticket/commands.py](jira_sync/domains/ticket/commands.py) - Standard read pattern
- [status/commands.py](jira_sync/domains/status/commands.py) - Transitions handling
- [comment/commands.py](jira_sync/domains/comment/commands.py) - Simple domain
- [cli.py](jira_sync/cli.py) - Command discovery, DOMAINS list
