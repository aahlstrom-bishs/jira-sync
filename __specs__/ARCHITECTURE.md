# Jira Sync Tool - Modular Architecture Redesign

## Goals
1. **Multiple output formats**: Obsidian, plain markdown, JSON, future formats
2. **Clean separation**: Pure functions that compose
3. **Future bidirectional sync**: Push local changes back to Jira

## Design Principles
- **Domain-driven**: Organize by concept (ticket, comment), not by layer
- **Co-located types & I/O**: Each domain owns its types, queries, and persistence
- **Pure functions**: Composable building blocks
- **Templates inside domains**: Each domain has its own output templates
- **lib/ for shared utilities**: Cross-domain transforms extracted to lib/

---

## Target Directory Structure

```
jira-sync/                    # current, root directory
├── __init__.py
├── __main__.py
├── cli.py                    # Thin: discovers & aggregates domain commands
├── config.py                 # Global configuration
│
├── ticket/                   # DOMAIN: Ticket
│   ├── __init__.py
│   ├── types.py              # JiraTicket, LocalTicket, DiffResult
│   ├── query.py              # fetch_ticket(key), fetch_tickets(keys)
│   ├── diff.py               # compare(local, remote) -> DiffResult
│   ├── persist.py            # write_file(), read_file()
│   ├── commands.py           # read:ticket, read:tickets, sync:ticket, sync:tickets, set:description
│   └── templates/
│       ├── __init__.py
│       ├── protocol.py       # Template interface/protocol
│       ├── obsidian.py       # transform() -> Obsidian markdown
│       ├── plain.py          # transform() -> plain markdown
│       └── json.py           # transform() -> JSON
│
├── comment/                  # DOMAIN: Comment
│   ├── __init__.py
│   ├── types.py              # JiraComment
│   ├── query.py              # fetch_comments(ticket_key)
│   ├── mutate.py             # add_comment(ticket_key, body)
│   ├── commands.py           # read:comments, add:comment
│   └── templates/
│       ├── __init__.py
│       ├── obsidian.py
│       └── plain.py
│
├── epic/                     # DOMAIN: Epic
│   ├── __init__.py
│   ├── types.py              # JiraEpic (extends ticket?)
│   ├── query.py              # fetch_epic(key), fetch_epic_children(key)
│   ├── persist.py            # write_epic_folder(), create_index()
│   ├── commands.py           # read:epic, sync:epic
│   └── templates/
│       ├── __init__.py
│       ├── obsidian.py
│       └── index.py          # Epic index file template
│
├── project/                  # DOMAIN: Project
│   ├── __init__.py
│   ├── types.py              # JiraProject
│   ├── query.py              # fetch_project_tickets(key, filters)
│   ├── persist.py            # write with index
│   ├── commands.py           # read:project, sync:project
│   └── templates/
│       └── ...
│
├── status/                   # DOMAIN: Status/Workflow
│   ├── __init__.py
│   ├── types.py              # Transition, StatusChange
│   ├── query.py              # fetch_status(key), fetch_transitions(key)
│   ├── mutate.py             # update_status(key, status)
│   ├── commands.py           # read:status, read:transitions, set:status
│   └── templates/
│       └── ...
│
├── link/                     # DOMAIN: Links
│   ├── __init__.py
│   ├── types.py              # JiraLink
│   ├── mutate.py             # create_link(from, to, type)
│   ├── commands.py           # add:link
│   └── templates/
│       └── ...
│
├── jql/                      # DOMAIN: JQL Queries
│   ├── __init__.py
│   ├── query.py              # execute_jql(query) -> list[JiraTicket]
│   ├── persist.py            # write with index
│   ├── commands.py           # read:jql, sync:jql
│   └── templates/
│       └── index.py          # JQL results index template
│
├── admin/                    # DOMAIN: Admin/Setup
│   ├── __init__.py
│   ├── init.py               # create .env file
│   ├── test.py               # test connection
│   ├── setup.py              # create specs/templates
│   └── commands.py           # init, test, setup
│
└── lib/                      # Shared utilities (cross-domain)
    ├── __init__.py
    ├── jira_markup.py        # jira_to_md(), md_to_jira()
    ├── text.py               # sanitize_name(), format_size()
    ├── jira_client.py        # Shared JIRA connection wrapper (used by query modules)
    └── markdown/             # Reusable markdown transforms
        ├── __init__.py
        ├── frontmatter.py    # build_frontmatter() - atomic element
        ├── tags.py           # format_tags() - atomic element
        ├── links.py          # format_wiki_links() - atomic element
        ├── code_blocks.py    # format_code_block() - atomic element
        └── types/            # Composed from atomic elements
            ├── __init__.py
            ├── description.py  # transform_description()
            ├── metadata.py     # transform_metadata()
            └── comment.py      # transform_comment()
```

---

## Dependency Graph (Build Order)

```
Phase 1: lib/ (no internal dependencies)
    lib/text.py
    lib/jira_markup.py
    lib/jira_client.py
    lib/markdown/frontmatter.py
    lib/markdown/tags.py
    lib/markdown/links.py
    lib/markdown/code_blocks.py
    lib/markdown/types/description.py  (depends on: jira_markup)
    lib/markdown/types/metadata.py     (depends on: frontmatter, tags)
    lib/markdown/types/comment.py      (depends on: jira_markup)

Phase 2: ticket/ (depends on lib/)
    ticket/types.py
    ticket/query.py            (depends on: lib/jira_client, ticket/types)
    ticket/templates/protocol.py
    ticket/templates/obsidian.py (depends on: lib/markdown/*, ticket/types)
    ticket/templates/plain.py
    ticket/templates/json.py
    ticket/persist.py          (depends on: ticket/types, lib/text)
    ticket/diff.py             (depends on: ticket/types)
    ticket/commands.py         (depends on: all above)

Phase 3: Other domains (depends on lib/, may depend on ticket/types)
    comment/, epic/, project/, status/, link/, jql/, admin/

Phase 4: CLI wiring
    cli.py                     (depends on: all domain/commands.py)
    __init__.py updates
```

---

## Complete File Specifications

### lib/__init__.py
```python
"""Shared utilities for Jira sync tool."""
from .text import sanitize_name, format_size
from .jira_markup import jira_to_md, md_to_jira
from .jira_client import get_client, JiraConnection

__all__ = [
    "sanitize_name",
    "format_size",
    "jira_to_md",
    "md_to_jira",
    "get_client",
    "JiraConnection",
]
```

---

### lib/text.py
```python
"""Text processing utilities."""
import re
from typing import Optional

def sanitize_name(
    name: str,
    max_length: int = 50,
    lowercase: bool = False,
    replace_spaces: str = "-"
) -> str:
    """
    Sanitize a string for use as a file or folder name.

    Args:
        name: Input string to sanitize
        max_length: Maximum length of output (default 50)
        lowercase: Convert to lowercase (default False)
        replace_spaces: Character to replace spaces with (default "-")

    Returns:
        Sanitized string safe for filesystem use

    Transformations:
        - Removes invalid filesystem characters: <>:"/\\|?*
        - Replaces + and whitespace with replace_spaces character
        - Collapses multiple hyphens/underscores
        - Trims to max_length
        - Strips leading/trailing hyphens
    """
    if not name:
        return ""

    # Remove invalid filesystem characters
    result = re.sub(r'[<>:"/\\|?*]', "", name)

    # Replace + and whitespace
    result = result.replace("+", replace_spaces)
    result = re.sub(r"\s+", replace_spaces, result)

    # Collapse multiple hyphens/separators
    if replace_spaces == "-":
        result = re.sub(r"-+", "-", result)
    elif replace_spaces == "_":
        result = re.sub(r"_+", "_", result)

    # Strip and truncate
    result = result.strip("-_")
    result = result[:max_length].rstrip("-_")

    if lowercase:
        result = result.lower()

    return result


def format_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string like "1.5 MB" or "256 B"
    """
    if size_bytes < 0:
        return "0 B"

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            if unit == "B":
                return f"{size_bytes} {unit}"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

    return f"{size_bytes:.1f} TB"


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length, adding suffix if truncated."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
```

---

### lib/jira_markup.py
```python
"""
Jira wiki markup <-> Markdown conversion.

Jira uses a wiki-style markup that differs from Markdown.
This module provides bidirectional conversion.
"""
import re
from typing import Optional


def jira_to_md(text: str) -> str:
    """
    Convert Jira wiki markup to Markdown format.

    Args:
        text: Jira wiki markup text

    Returns:
        Markdown formatted text

    Conversions:
        Headers:     h1. Title     ->  # Title
        Bold:        *bold*        ->  **bold**
        Italic:      _italic_      ->  *italic*
        Strike:      -strike-      ->  ~~strike~~
        Code:        {{code}}      ->  `code`
        Code block:  {code}...{code}  ->  ```...```
        Links:       [text|url]    ->  [text](url)
        Images:      !image.png!   ->  ![](image.png)
        Lists:       * item        ->  - item
        Checkboxes:  (/) done      ->  [x] done
                     (x) not done  ->  [ ] not done
    """
    if not text:
        return ""

    result = text

    # Headers: h1. through h6.
    for i in range(1, 7):
        result = re.sub(
            rf'^h{i}\.\s*(.+)$',
            r'#' * i + r' \1',
            result,
            flags=re.MULTILINE
        )

    # Code blocks: {code:language} or {code}
    result = re.sub(
        r'\{code(?::(\w+))?\}(.*?)\{code\}',
        lambda m: f"```{m.group(1) or ''}\n{m.group(2)}\n```",
        result,
        flags=re.DOTALL
    )

    # Inline code: {{code}}
    result = re.sub(r'\{\{(.+?)\}\}', r'`\1`', result)

    # Bold: *text* -> **text** (but not inside words)
    result = re.sub(r'(?<!\w)\*(\S.*?\S|\S)\*(?!\w)', r'**\1**', result)

    # Italic: _text_ -> *text*
    result = re.sub(r'(?<!\w)_(\S.*?\S|\S)_(?!\w)', r'*\1*', result)

    # Strikethrough: -text- -> ~~text~~
    result = re.sub(r'(?<!\w)-(\S.*?\S|\S)-(?!\w)', r'~~\1~~', result)

    # Links: [text|url] -> [text](url)
    result = re.sub(r'\[([^\]|]+)\|([^\]]+)\]', r'[\1](\2)', result)

    # Plain links: [url] -> [url](url)
    result = re.sub(r'\[([^\]|]+)\](?!\()', r'[\1](\1)', result)

    # Images: !image.png! or !image.png|alt=text!
    result = re.sub(r'!([^|!]+)(?:\|[^!]*)?\!', r'![](\1)', result)

    # Bullet lists: * item -> - item (handle nesting)
    result = re.sub(r'^(\*+)\s', lambda m: '  ' * (len(m.group(1)) - 1) + '- ', result, flags=re.MULTILINE)

    # Numbered lists: # item -> 1. item
    result = re.sub(r'^#+\s', '1. ', result, flags=re.MULTILINE)

    # Checkboxes
    result = result.replace('(/)', '[x]')
    result = result.replace('(x)', '[ ]')
    result = result.replace('( )', '[ ]')

    # Horizontal rule
    result = re.sub(r'^----+$', '---', result, flags=re.MULTILINE)

    # Tables: ||header|| -> | header |
    result = re.sub(r'\|\|([^|]+)\|\|', r'| \1 |', result)
    result = re.sub(r'\|([^|]+)\|', r'| \1 |', result)

    return result.strip()


def md_to_jira(text: str) -> str:
    """
    Convert Markdown to Jira wiki markup.

    Args:
        text: Markdown formatted text

    Returns:
        Jira wiki markup text

    Note: This is for bidirectional sync - pushing local changes to Jira.
    """
    if not text:
        return ""

    result = text

    # Headers: # Title -> h1. Title
    for i in range(6, 0, -1):  # Process h6 first to avoid conflicts
        result = re.sub(
            rf'^{"#" * i}\s+(.+)$',
            rf'h{i}. \1',
            result,
            flags=re.MULTILINE
        )

    # Code blocks
    result = re.sub(
        r'```(\w*)\n(.*?)\n```',
        lambda m: f"{{code:{m.group(1)}}}{m.group(2)}{{code}}" if m.group(1) else f"{{code}}{m.group(2)}{{code}}",
        result,
        flags=re.DOTALL
    )

    # Inline code
    result = re.sub(r'`([^`]+)`', r'{{\1}}', result)

    # Bold: **text** -> *text*
    result = re.sub(r'\*\*(.+?)\*\*', r'*\1*', result)

    # Italic: *text* -> _text_ (after bold conversion)
    result = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'_\1_', result)

    # Strikethrough: ~~text~~ -> -text-
    result = re.sub(r'~~(.+?)~~', r'-\1-', result)

    # Links: [text](url) -> [text|url]
    result = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1|\2]', result)

    # Images: ![alt](url) -> !url!
    result = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'!\2!', result)

    # Bullet lists: - item -> * item
    result = re.sub(r'^(\s*)- ', lambda m: '*' * (len(m.group(1)) // 2 + 1) + ' ', result, flags=re.MULTILINE)

    # Checkboxes
    result = result.replace('[x]', '(/)')
    result = result.replace('[ ]', '(x)')

    return result.strip()
```

---

### lib/jira_client.py
```python
"""
Shared JIRA connection wrapper.

Provides a singleton-like connection manager that domains can use
to interact with the Jira API without each creating their own connection.
"""
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass
from functools import lru_cache

from jira import JIRA

if TYPE_CHECKING:
    from ..config import Config


@dataclass
class JiraConnection:
    """Wrapper around JIRA client with connection info."""
    client: JIRA
    base_url: str
    email: str

    def browse_url(self, key: str) -> str:
        """Get the browse URL for a ticket."""
        return f"{self.base_url}/browse/{key}"


_connection: Optional[JiraConnection] = None


def get_client(config: "Config") -> JiraConnection:
    """
    Get or create a JIRA client connection.

    Args:
        config: Configuration with Jira credentials

    Returns:
        JiraConnection wrapper

    Note: Reuses existing connection if config matches.
    """
    global _connection

    if _connection is None or _connection.base_url != config.jira_url:
        client = JIRA(
            server=config.jira_url,
            basic_auth=(config.jira_email, config.jira_api_token),
        )
        _connection = JiraConnection(
            client=client,
            base_url=config.jira_url,
            email=config.jira_email,
        )

    return _connection


def reset_connection():
    """Reset the cached connection. Useful for testing."""
    global _connection
    _connection = None
```

---

### lib/markdown/__init__.py
```python
"""Markdown transform utilities."""
from .frontmatter import build_frontmatter, parse_frontmatter
from .tags import format_tags, format_obsidian_tag
from .links import format_wiki_links, format_wiki_link
from .code_blocks import format_code_block

__all__ = [
    "build_frontmatter",
    "parse_frontmatter",
    "format_tags",
    "format_obsidian_tag",
    "format_wiki_links",
    "format_wiki_link",
    "format_code_block",
]
```

---

### lib/markdown/frontmatter.py
```python
"""YAML frontmatter utilities for markdown files."""
from typing import Any, Optional
from datetime import datetime
import re


def build_frontmatter(data: dict[str, Any], include_timestamp: bool = True) -> str:
    """
    Build YAML frontmatter block from dictionary.

    Args:
        data: Dictionary of frontmatter fields
        include_timestamp: Add synced timestamp (default True)

    Returns:
        YAML frontmatter string including --- delimiters

    Example:
        >>> build_frontmatter({"key": "SR-1234", "status": "Done"})
        '---\\njira_key: SR-1234\\nstatus: Done\\nsynced: 2024-01-15 10:30\\n---'
    """
    lines = ["---"]

    for key, value in data.items():
        if value is None:
            continue

        if isinstance(value, list):
            if value:  # Only include non-empty lists
                formatted = ", ".join(str(v) for v in value)
                lines.append(f"{key}: [{formatted}]")
        elif isinstance(value, datetime):
            lines.append(f"{key}: {value.strftime('%Y-%m-%d')}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {str(value).lower()}")
        else:
            # Escape quotes in strings
            str_value = str(value)
            if '"' in str_value or ':' in str_value or '\n' in str_value:
                str_value = f'"{str_value}"'
            lines.append(f"{key}: {str_value}")

    if include_timestamp:
        lines.append(f"synced: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    lines.append("---")
    return "\n".join(lines)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown content with optional frontmatter

    Returns:
        Tuple of (frontmatter_dict, body_content)

    Example:
        >>> fm, body = parse_frontmatter("---\\nkey: value\\n---\\n# Title")
        >>> fm
        {'key': 'value'}
        >>> body
        '# Title'
    """
    if not content.startswith("---"):
        return {}, content

    # Find the closing ---
    match = re.match(r'^---\n(.*?)\n---\n?(.*)', content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = match.group(2)

    # Simple YAML parsing (key: value format)
    data = {}
    for line in frontmatter_text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Handle lists [a, b, c]
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip() for v in value[1:-1].split(",")]
            # Handle booleans
            elif value.lower() in ("true", "false"):
                value = value.lower() == "true"
            # Handle quoted strings
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]

            data[key] = value

    return data, body
```

---

### lib/markdown/tags.py
```python
"""Tag formatting utilities for Obsidian."""
from typing import Optional


def format_obsidian_tag(value: str, prefix: Optional[str] = None) -> str:
    """
    Format a single value as an Obsidian tag.

    Args:
        value: The tag value
        prefix: Optional prefix like "status" or "priority"

    Returns:
        Formatted tag like "#status/in-progress"

    Example:
        >>> format_obsidian_tag("In Progress", "status")
        '#status/in-progress'
    """
    # Normalize: lowercase, replace spaces with hyphens
    normalized = value.lower().replace(" ", "-")

    # Remove any existing # prefix
    normalized = normalized.lstrip("#")

    if prefix:
        return f"#{prefix}/{normalized}"
    return f"#{normalized}"


def format_tags(
    tags: list[str],
    prefix: Optional[str] = None,
    separator: str = " "
) -> str:
    """
    Format multiple values as Obsidian tags.

    Args:
        tags: List of tag values
        prefix: Optional prefix for all tags
        separator: Separator between tags (default space)

    Returns:
        Formatted tags string

    Example:
        >>> format_tags(["In Progress", "High"], None)
        '#in-progress #high'
        >>> format_tags(["bug", "feature"], "label")
        '#label/bug #label/feature'
    """
    if not tags:
        return ""

    formatted = [format_obsidian_tag(tag, prefix) for tag in tags if tag]
    return separator.join(formatted)


def format_status_tag(status: str) -> str:
    """Format status as Obsidian tag with status/ prefix."""
    return format_obsidian_tag(status, "status")


def format_priority_tag(priority: str) -> str:
    """Format priority as Obsidian tag with priority/ prefix."""
    return format_obsidian_tag(priority, "priority")


def format_type_tag(issue_type: str) -> str:
    """Format issue type as Obsidian tag with type/ prefix."""
    return format_obsidian_tag(issue_type, "type")
```

---

### lib/markdown/links.py
```python
"""Wiki-link formatting utilities for Obsidian."""
from typing import Optional


def format_wiki_link(key: str, display_text: Optional[str] = None) -> str:
    """
    Format a ticket key as an Obsidian wiki-link.

    Args:
        key: Ticket key like "SR-1234"
        display_text: Optional display text

    Returns:
        Wiki-link like "[[SR-1234]]" or "[[SR-1234|Display Text]]"

    Example:
        >>> format_wiki_link("SR-1234")
        '[[SR-1234]]'
        >>> format_wiki_link("SR-1234", "Parent Ticket")
        '[[SR-1234|Parent Ticket]]'
    """
    if display_text:
        return f"[[{key}|{display_text}]]"
    return f"[[{key}]]"


def format_wiki_links(keys: list[str], separator: str = ", ") -> str:
    """
    Format multiple ticket keys as wiki-links.

    Args:
        keys: List of ticket keys
        separator: Separator between links (default ", ")

    Returns:
        Formatted wiki-links string

    Example:
        >>> format_wiki_links(["SR-1", "SR-2", "SR-3"])
        '[[SR-1]], [[SR-2]], [[SR-3]]'
    """
    if not keys:
        return ""

    return separator.join(format_wiki_link(key) for key in keys)


def format_external_link(url: str, text: str) -> str:
    """
    Format an external URL as a markdown link.

    Args:
        url: The URL
        text: Display text

    Returns:
        Markdown link like "[text](url)"
    """
    return f"[{text}]({url})"
```

---

### lib/markdown/code_blocks.py
```python
"""Code block formatting utilities."""
from typing import Optional


def format_code_block(
    content: str,
    language: Optional[str] = None,
    inline: bool = False
) -> str:
    """
    Format content as a code block.

    Args:
        content: The code content
        language: Optional language for syntax highlighting
        inline: If True, format as inline code

    Returns:
        Formatted code block or inline code

    Example:
        >>> format_code_block("print('hello')", "python")
        '```python\\nprint('hello')\\n```'
        >>> format_code_block("var", inline=True)
        '`var`'
    """
    if inline:
        # Escape backticks in inline code
        if '`' in content:
            return f"``{content}``"
        return f"`{content}`"

    lang = language or ""
    return f"```{lang}\n{content}\n```"


def format_callout(
    content: str,
    callout_type: str = "info",
    title: Optional[str] = None,
    foldable: bool = False
) -> str:
    """
    Format content as an Obsidian callout.

    Args:
        content: The callout content
        callout_type: Type like "info", "warning", "note", "tip"
        title: Optional custom title
        foldable: If True, make callout foldable with -

    Returns:
        Formatted Obsidian callout

    Example:
        >>> format_callout("Important note", "warning", "Watch out!")
        '> [!warning] Watch out!\\n> Important note'
    """
    fold_marker = "-" if foldable else ""
    header = f"> [!{callout_type}]{fold_marker}"

    if title:
        header = f"{header} {title}"

    # Indent content lines with >
    content_lines = content.split("\n")
    formatted_content = "\n".join(f"> {line}" for line in content_lines)

    return f"{header}\n{formatted_content}"
```

---

### lib/markdown/types/__init__.py
```python
"""Composed markdown transforms by data type."""
from .description import transform_description
from .metadata import transform_metadata
from .comment import transform_comment

__all__ = [
    "transform_description",
    "transform_metadata",
    "transform_comment",
]
```

---

### lib/markdown/types/description.py
```python
"""Description field transformation."""
from typing import Optional
from ...jira_markup import jira_to_md


def transform_description(
    raw_description: str,
    max_length: Optional[int] = None,
    include_header: bool = False
) -> str:
    """
    Transform a Jira description to markdown.

    Args:
        raw_description: Raw description from Jira (wiki markup)
        max_length: Optional max length to truncate
        include_header: Include "## Description" header

    Returns:
        Markdown formatted description
    """
    if not raw_description:
        return ""

    # Convert Jira markup to markdown
    content = jira_to_md(raw_description)

    # Truncate if needed
    if max_length and len(content) > max_length:
        content = content[:max_length - 3] + "..."

    if include_header:
        return f"## Description\n\n{content}"

    return content
```

---

### lib/markdown/types/metadata.py
```python
"""Metadata section transformation."""
from typing import Any, Optional
from datetime import datetime
from ..frontmatter import build_frontmatter
from ..tags import format_status_tag, format_priority_tag, format_type_tag


def transform_metadata(
    data: dict[str, Any],
    format: str = "frontmatter"
) -> str:
    """
    Transform metadata to markdown format.

    Args:
        data: Dictionary with ticket metadata
        format: "frontmatter" (YAML) or "table" (markdown table)

    Returns:
        Formatted metadata section
    """
    if format == "frontmatter":
        return build_frontmatter(data)
    elif format == "table":
        return _build_metadata_table(data)
    else:
        raise ValueError(f"Unknown format: {format}")


def _build_metadata_table(data: dict[str, Any]) -> str:
    """Build metadata as a markdown table."""
    lines = [
        "## Metadata",
        "",
        "| Field | Value |",
        "|-------|-------|",
    ]

    for key, value in data.items():
        if value is None:
            continue

        # Format value based on type
        if isinstance(value, list):
            formatted = ", ".join(str(v) for v in value)
        elif isinstance(value, datetime):
            formatted = value.strftime("%Y-%m-%d")
        else:
            formatted = str(value)

        # Capitalize key for display
        display_key = key.replace("_", " ").title()
        lines.append(f"| **{display_key}** | {formatted} |")

    return "\n".join(lines)


def build_tag_line(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    issue_type: Optional[str] = None,
    labels: Optional[list[str]] = None
) -> str:
    """
    Build a line of Obsidian tags for a ticket.

    Args:
        status: Ticket status
        priority: Ticket priority
        issue_type: Issue type (Story, Bug, etc.)
        labels: List of labels

    Returns:
        Space-separated tags string
    """
    tags = []

    if status:
        tags.append(format_status_tag(status))
    if priority:
        tags.append(format_priority_tag(priority))
    if issue_type:
        tags.append(format_type_tag(issue_type))
    if labels:
        for label in labels:
            tags.append(f"#label/{label.lower().replace(' ', '-')}")

    return " ".join(tags)
```

---

### lib/markdown/types/comment.py
```python
"""Comment transformation."""
from typing import Optional
from datetime import datetime
from ...jira_markup import jira_to_md
from ..code_blocks import format_callout


def transform_comment(
    author: str,
    body: str,
    created: datetime | str,
    format: str = "callout"
) -> str:
    """
    Transform a single comment to markdown.

    Args:
        author: Comment author name
        body: Comment body (Jira wiki markup)
        created: Creation timestamp
        format: "callout" (Obsidian callout), "blockquote", or "section"

    Returns:
        Formatted comment
    """
    # Convert body from Jira markup
    md_body = jira_to_md(body) if body else ""

    # Format timestamp
    if isinstance(created, datetime):
        timestamp = created.strftime("%Y-%m-%d %H:%M")
    else:
        timestamp = str(created)

    if format == "callout":
        return format_callout(
            md_body,
            callout_type="quote",
            title=f"{author} - {timestamp}",
            foldable=True
        )
    elif format == "blockquote":
        lines = [f"> **{author}** - {timestamp}", ">"]
        for line in md_body.split("\n"):
            lines.append(f"> {line}")
        return "\n".join(lines)
    elif format == "section":
        return f"### {author} - {timestamp}\n\n{md_body}"
    else:
        raise ValueError(f"Unknown format: {format}")


def transform_comments(
    comments: list[dict],
    include_header: bool = True,
    format: str = "callout"
) -> str:
    """
    Transform multiple comments to markdown.

    Args:
        comments: List of comment dicts with author, body, created
        include_header: Include "## Comments" header
        format: Format for individual comments

    Returns:
        Formatted comments section
    """
    if not comments:
        return ""

    parts = []

    if include_header:
        parts.append("## Comments")
        parts.append("")

    for comment in comments:
        formatted = transform_comment(
            author=comment.get("author", "Unknown"),
            body=comment.get("body", ""),
            created=comment.get("created", ""),
            format=format
        )
        parts.append(formatted)
        parts.append("")

    return "\n".join(parts)
```

---

## ticket/ Domain Specification

### ticket/types.py
```python
"""Type definitions for ticket domain."""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any


@dataclass
class JiraTicket:
    """
    Normalized ticket data from Jira.

    This is the canonical representation of a Jira issue,
    independent of the jira-python library's Issue object.
    """
    key: str
    summary: str
    description: str = ""
    status: str = ""
    priority: str = ""
    issue_type: str = ""
    assignee: str = ""
    reporter: str = ""
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    resolved: Optional[datetime] = None
    labels: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    fix_versions: list[str] = field(default_factory=list)
    parent_key: Optional[str] = None
    parent_summary: Optional[str] = None
    epic_key: Optional[str] = None
    epic_name: Optional[str] = None
    subtasks: list[str] = field(default_factory=list)
    links: list[dict] = field(default_factory=list)
    comments: list[dict] = field(default_factory=list)
    attachments: list[dict] = field(default_factory=list)
    url: str = ""
    custom_fields: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "summary": self.summary,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "issue_type": self.issue_type,
            "assignee": self.assignee,
            "reporter": self.reporter,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
            "resolved": self.resolved.isoformat() if self.resolved else None,
            "labels": self.labels,
            "components": self.components,
            "fix_versions": self.fix_versions,
            "parent_key": self.parent_key,
            "epic_key": self.epic_key,
            "subtasks": self.subtasks,
            "links": self.links,
            "url": self.url,
        }


@dataclass
class LocalTicket:
    """
    Representation of a ticket stored locally in the vault.

    Used for diff comparison and bidirectional sync.
    """
    path: Path
    content: str
    frontmatter: dict[str, Any]
    body: str
    key: str = ""

    @classmethod
    def from_file(cls, path: Path) -> "LocalTicket":
        """Load a local ticket from a markdown file."""
        from ...lib.markdown import parse_frontmatter

        content = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)

        return cls(
            path=path,
            content=content,
            frontmatter=frontmatter,
            body=body,
            key=frontmatter.get("jira_key", path.stem.split("-")[0]),
        )


@dataclass
class DiffResult:
    """
    Result of comparing local and remote ticket versions.

    Used to determine if sync is needed and what changed.
    """
    changed: bool
    local: Optional[LocalTicket]
    remote: JiraTicket
    changes: list[str] = field(default_factory=list)  # List of changed fields

    @property
    def is_new(self) -> bool:
        """True if ticket doesn't exist locally."""
        return self.local is None

    @property
    def is_updated(self) -> bool:
        """True if ticket exists locally but has changes."""
        return self.local is not None and self.changed
```

---

### ticket/query.py
```python
"""
Ticket query operations - fetching from Jira.
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from jira.resources import Issue

from .types import JiraTicket
from ..lib.jira_client import get_client

if TYPE_CHECKING:
    from ..config import Config


def fetch_ticket(key: str, config: "Config", expand: str = "changelog") -> JiraTicket:
    """
    Fetch a single ticket from Jira.

    Args:
        key: Ticket key like "SR-1234"
        config: Configuration with Jira credentials
        expand: Fields to expand (default "changelog")

    Returns:
        JiraTicket object

    Raises:
        JIRAError: If ticket not found or API error
    """
    conn = get_client(config)
    issue = conn.client.issue(key, expand=expand)
    return _issue_to_ticket(issue, conn.base_url)


def fetch_tickets(keys: list[str], config: "Config") -> list[JiraTicket]:
    """
    Fetch multiple tickets by key.

    Args:
        keys: List of ticket keys
        config: Configuration with Jira credentials

    Returns:
        List of JiraTicket objects (in same order as keys)
    """
    if not keys:
        return []

    # Use JQL for efficient bulk fetch
    jql = f"key in ({','.join(keys)})"
    conn = get_client(config)
    issues = conn.client.search_issues(jql, maxResults=len(keys))

    # Build lookup and return in original order
    by_key = {_issue_to_ticket(i, conn.base_url).key: _issue_to_ticket(i, conn.base_url) for i in issues}
    return [by_key[k] for k in keys if k in by_key]


def _issue_to_ticket(issue: Issue, base_url: str) -> JiraTicket:
    """
    Convert jira-python Issue to our JiraTicket type.

    Args:
        issue: jira-python Issue object
        base_url: Jira server base URL

    Returns:
        JiraTicket dataclass instance
    """
    fields = issue.fields

    ticket = JiraTicket(
        key=issue.key,
        summary=fields.summary or "",
        description=fields.description or "",
        status=getattr(fields.status, "name", "") if fields.status else "",
        priority=getattr(fields.priority, "name", "") if fields.priority else "",
        issue_type=getattr(fields.issuetype, "name", "") if fields.issuetype else "",
        assignee=getattr(fields.assignee, "displayName", "") if fields.assignee else "",
        reporter=getattr(fields.reporter, "displayName", "") if fields.reporter else "",
        created=_parse_date(fields.created),
        updated=_parse_date(fields.updated),
        resolved=_parse_date(getattr(fields, "resolutiondate", None)),
        labels=list(fields.labels) if fields.labels else [],
        url=f"{base_url}/browse/{issue.key}",
    )

    # Components
    if fields.components:
        ticket.components = [c.name for c in fields.components]

    # Fix versions
    if fields.fixVersions:
        ticket.fix_versions = [v.name for v in fields.fixVersions]

    # Parent (for subtasks)
    if hasattr(fields, "parent") and fields.parent:
        ticket.parent_key = fields.parent.key
        ticket.parent_summary = getattr(fields.parent.fields, "summary", "")

    # Epic link
    epic_key = _get_epic_link(fields)
    if epic_key:
        ticket.epic_key = epic_key

    # Subtasks
    if hasattr(fields, "subtasks") and fields.subtasks:
        ticket.subtasks = [st.key for st in fields.subtasks]

    # Issue links
    if hasattr(fields, "issuelinks") and fields.issuelinks:
        for link in fields.issuelinks:
            link_data = {"type": link.type.name}
            if hasattr(link, "outwardIssue"):
                link_data["direction"] = "outward"
                link_data["key"] = link.outwardIssue.key
                link_data["summary"] = link.outwardIssue.fields.summary
            elif hasattr(link, "inwardIssue"):
                link_data["direction"] = "inward"
                link_data["key"] = link.inwardIssue.key
                link_data["summary"] = link.inwardIssue.fields.summary
            ticket.links.append(link_data)

    # Comments
    if hasattr(fields, "comment") and fields.comment:
        for comment in fields.comment.comments:
            ticket.comments.append({
                "author": getattr(comment.author, "displayName", "Unknown"),
                "body": comment.body or "",
                "created": str(_parse_date(comment.created)),
            })

    # Attachments
    if hasattr(fields, "attachment") and fields.attachment:
        for att in fields.attachment:
            ticket.attachments.append({
                "filename": att.filename,
                "url": att.content,
                "size": att.size,
                "mime_type": att.mimeType,
            })

    return ticket


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse Jira date string to datetime."""
    if not date_str:
        return None

    if isinstance(date_str, datetime):
        return date_str

    try:
        # Jira format: "2024-01-15T10:30:00.000+0000"
        clean_date = date_str.split(".")[0]
        return datetime.fromisoformat(clean_date)
    except (ValueError, AttributeError):
        return None


def _get_epic_link(fields) -> Optional[str]:
    """Extract epic link from various custom field locations."""
    # Common custom field names for epic link
    for field_name in ["customfield_10014", "customfield_10008", "parent"]:
        if hasattr(fields, field_name):
            value = getattr(fields, field_name)
            if value:
                if isinstance(value, str):
                    return value
                elif hasattr(value, "key"):
                    return value.key
    return None
```

---

### ticket/templates/protocol.py
```python
"""Template protocol definition."""
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import JiraTicket


class TicketTemplate(Protocol):
    """Protocol for ticket template implementations."""

    def transform(self, ticket: "JiraTicket") -> str:
        """Transform a ticket to the output format."""
        ...

    @property
    def file_extension(self) -> str:
        """File extension for this format (e.g., '.md', '.json')."""
        ...
```

---

### ticket/templates/obsidian.py
```python
"""Obsidian markdown template for tickets."""
from typing import TYPE_CHECKING, Optional

from ...lib.markdown import build_frontmatter, format_wiki_link, format_wiki_links
from ...lib.markdown.types import transform_description, build_tag_line
from ...lib.markdown.types.comment import transform_comments
from ...lib.text import format_size

if TYPE_CHECKING:
    from ..types import JiraTicket


def transform(
    ticket: "JiraTicket",
    include_comments: bool = True,
    include_attachments: bool = True
) -> str:
    """
    Transform a JiraTicket to Obsidian-flavored markdown.

    Args:
        ticket: The ticket to transform
        include_comments: Include comments section
        include_attachments: Include attachments section

    Returns:
        Complete markdown document string
    """
    parts = []

    # 1. YAML Frontmatter
    frontmatter_data = {
        "jira_key": ticket.key,
        "jira_url": ticket.url,
        "status": ticket.status,
        "priority": ticket.priority,
        "type": ticket.issue_type,
    }
    if ticket.assignee:
        frontmatter_data["assignee"] = ticket.assignee
    if ticket.reporter:
        frontmatter_data["reporter"] = ticket.reporter
    if ticket.created:
        frontmatter_data["created"] = ticket.created
    if ticket.updated:
        frontmatter_data["updated"] = ticket.updated
    if ticket.parent_key:
        frontmatter_data["parent"] = ticket.parent_key
    if ticket.epic_key:
        frontmatter_data["epic"] = ticket.epic_key
    if ticket.labels:
        frontmatter_data["labels"] = ticket.labels

    parts.append(build_frontmatter(frontmatter_data))
    parts.append("")

    # 2. Title
    parts.append(f"# {ticket.key}: {ticket.summary}")
    parts.append("")

    # 3. Tags line
    tag_line = build_tag_line(
        status=ticket.status,
        priority=ticket.priority,
        issue_type=ticket.issue_type,
        labels=ticket.labels
    )
    if tag_line:
        parts.append(tag_line)
        parts.append("")

    # 4. Description
    if ticket.description:
        parts.append("## Description")
        parts.append("")
        parts.append(transform_description(ticket.description))
        parts.append("")

    # 5. Related tickets
    if ticket.links or ticket.parent_key or ticket.subtasks:
        parts.append(_build_links_section(ticket))

    # 6. Comments
    if include_comments and ticket.comments:
        parts.append(transform_comments(ticket.comments))

    # 7. Attachments
    if include_attachments and ticket.attachments:
        parts.append(_build_attachments_section(ticket.attachments))

    return "\n".join(parts)


def _build_links_section(ticket: "JiraTicket") -> str:
    """Build the related tickets section."""
    lines = ["## Related Tickets", ""]

    # Parent
    if ticket.parent_key:
        parent_text = f"{ticket.parent_summary}" if ticket.parent_summary else ""
        lines.append(f"**Parent:** {format_wiki_link(ticket.parent_key, parent_text)}")
        lines.append("")

    # Epic
    if ticket.epic_key and ticket.epic_key != ticket.parent_key:
        lines.append(f"**Epic:** {format_wiki_link(ticket.epic_key)}")
        lines.append("")

    # Issue links
    if ticket.links:
        lines.append("### Links")
        for link in ticket.links:
            direction = link.get("direction", "")
            link_type = link.get("type", "")
            key = link.get("key", "")
            summary = link.get("summary", "")

            if direction == "outward":
                lines.append(f"- {link_type}: {format_wiki_link(key)} - {summary}")
            else:
                lines.append(f"- {link_type} (inward): {format_wiki_link(key)} - {summary}")
        lines.append("")

    # Subtasks
    if ticket.subtasks:
        lines.append("### Subtasks")
        for subtask in ticket.subtasks:
            lines.append(f"- {format_wiki_link(subtask)}")
        lines.append("")

    return "\n".join(lines)


def _build_attachments_section(attachments: list[dict]) -> str:
    """Build the attachments section."""
    lines = ["## Attachments", ""]

    for att in attachments:
        filename = att.get("filename", "")
        url = att.get("url", "")
        size = att.get("size", 0)
        size_str = format_size(size)
        lines.append(f"- [{filename}]({url}) ({size_str})")

    lines.append("")
    return "\n".join(lines)


# Template metadata
file_extension = ".md"
```

---

### ticket/templates/plain.py
```python
"""Plain markdown template (no Obsidian-specific features)."""
from typing import TYPE_CHECKING

from ...lib.markdown.types import transform_description
from ...lib.text import format_size

if TYPE_CHECKING:
    from ..types import JiraTicket


def transform(ticket: "JiraTicket") -> str:
    """
    Transform a JiraTicket to plain markdown (no wiki-links, no tags).

    Args:
        ticket: The ticket to transform

    Returns:
        Plain markdown document string
    """
    parts = []

    # Title with link
    parts.append(f"# [{ticket.key}]({ticket.url}): {ticket.summary}")
    parts.append("")

    # Metadata table
    parts.append("| Field | Value |")
    parts.append("|-------|-------|")
    parts.append(f"| **Status** | {ticket.status} |")
    parts.append(f"| **Priority** | {ticket.priority} |")
    parts.append(f"| **Type** | {ticket.issue_type} |")
    if ticket.assignee:
        parts.append(f"| **Assignee** | {ticket.assignee} |")
    if ticket.reporter:
        parts.append(f"| **Reporter** | {ticket.reporter} |")
    if ticket.created:
        parts.append(f"| **Created** | {ticket.created.strftime('%Y-%m-%d')} |")
    parts.append("")

    # Description
    if ticket.description:
        parts.append("## Description")
        parts.append("")
        parts.append(transform_description(ticket.description))
        parts.append("")

    # Related (as plain links)
    if ticket.parent_key:
        parts.append(f"**Parent:** [{ticket.parent_key}]({ticket.url.rsplit('/', 1)[0]}/{ticket.parent_key})")
        parts.append("")

    return "\n".join(parts)


file_extension = ".md"
```

---

### ticket/templates/json.py
```python
"""JSON template for tickets."""
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import JiraTicket


def transform(ticket: "JiraTicket", indent: int = 2) -> str:
    """
    Transform a JiraTicket to JSON.

    Args:
        ticket: The ticket to transform
        indent: JSON indentation (default 2)

    Returns:
        JSON string
    """
    return json.dumps(ticket.to_dict(), indent=indent, default=str)


file_extension = ".json"
```

---

### ticket/persist.py
```python
"""
Ticket file persistence operations.
"""
import re
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ..lib.text import sanitize_name

if TYPE_CHECKING:
    from ..config import Config
    from .types import JiraTicket


def write_file(
    ticket: "JiraTicket",
    content: str,
    config: "Config",
    category: Optional[str] = None,
    force: bool = False
) -> Optional[Path]:
    """
    Write ticket content to file in vault.

    Args:
        ticket: The ticket being written
        content: Formatted content to write
        config: Configuration with vault path
        category: Optional subfolder category
        force: Overwrite even if unchanged

    Returns:
        Path to written file, or None if skipped (unchanged)
    """
    # Determine folder
    base_path = config.tickets_path
    if category:
        folder = base_path / sanitize_name(category)
    else:
        folder = base_path

    folder.mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = generate_filename(ticket)
    file_path = folder / filename

    # Check if unchanged
    if file_path.exists() and not force:
        existing = file_path.read_text(encoding="utf-8")
        if content_unchanged(existing, content):
            return None

    # Write file
    file_path.write_text(content, encoding="utf-8")
    return file_path


def read_file(path: Path) -> Optional[str]:
    """
    Read ticket file content.

    Args:
        path: Path to ticket file

    Returns:
        File content or None if not found
    """
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def find_ticket_file(key: str, config: "Config") -> Optional[Path]:
    """
    Find existing ticket file by key.

    Args:
        key: Ticket key like "SR-1234"
        config: Configuration with vault path

    Returns:
        Path to file if found, None otherwise
    """
    base_path = config.tickets_path

    # Search for file starting with key
    for path in base_path.rglob(f"{key}*.md"):
        return path

    return None


def generate_filename(ticket: "JiraTicket", extension: str = ".md") -> str:
    """
    Generate a safe filename for a ticket.

    Args:
        ticket: The ticket
        extension: File extension (default ".md")

    Returns:
        Filename like "SR-1234-summary-text.md"
    """
    if ticket.summary:
        safe_summary = sanitize_name(ticket.summary, max_length=50, lowercase=True)
        return f"{ticket.key}-{safe_summary}{extension}"
    return f"{ticket.key}{extension}"


def content_unchanged(existing: str, new: str) -> bool:
    """
    Compare content ignoring sync timestamp.

    Args:
        existing: Existing file content
        new: New content to write

    Returns:
        True if content is effectively unchanged
    """
    # Remove sync timestamp line for comparison
    existing_clean = re.sub(r"synced: .*\n?", "", existing)
    new_clean = re.sub(r"synced: .*\n?", "", new)

    return existing_clean.strip() == new_clean.strip()
```

---

### ticket/diff.py
```python
"""
Ticket diff operations for comparing local and remote versions.
"""
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from .types import JiraTicket, LocalTicket, DiffResult

if TYPE_CHECKING:
    from ..config import Config


def compare(
    local: Optional[LocalTicket],
    remote: JiraTicket
) -> DiffResult:
    """
    Compare local and remote ticket versions.

    Args:
        local: Local ticket (None if doesn't exist)
        remote: Remote ticket from Jira

    Returns:
        DiffResult with change information
    """
    if local is None:
        return DiffResult(
            changed=True,
            local=None,
            remote=remote,
            changes=["new_ticket"]
        )

    changes = []

    # Compare frontmatter fields
    fm = local.frontmatter

    if fm.get("status") != remote.status:
        changes.append("status")
    if fm.get("priority") != remote.priority:
        changes.append("priority")
    if fm.get("assignee") != remote.assignee:
        changes.append("assignee")

    # Compare description (more complex - need to check body)
    # For now, use updated timestamp as proxy
    remote_updated = remote.updated.isoformat() if remote.updated else ""
    local_updated = fm.get("updated", "")
    if remote_updated != local_updated:
        changes.append("updated")

    return DiffResult(
        changed=len(changes) > 0,
        local=local,
        remote=remote,
        changes=changes
    )


def load_local_ticket(key: str, config: "Config") -> Optional[LocalTicket]:
    """
    Load local ticket file if it exists.

    Args:
        key: Ticket key
        config: Configuration with vault path

    Returns:
        LocalTicket or None
    """
    from .persist import find_ticket_file

    path = find_ticket_file(key, config)
    if path is None:
        return None

    return LocalTicket.from_file(path)
```

---

### ticket/commands.py
```python
"""
Ticket domain commands.

Exports COMMANDS dict for CLI discovery.
"""
from typing import TYPE_CHECKING, Optional
import sys

from .query import fetch_ticket, fetch_tickets
from .persist import write_file
from .templates import obsidian, plain, json as json_template

if TYPE_CHECKING:
    from ..config import Config


# Template registry
TEMPLATES = {
    "obsidian": obsidian.transform,
    "plain": plain.transform,
    "json": json_template.transform,
    "none": lambda t: str(t.to_dict()),
}


def handle_read_ticket(config: "Config", args) -> None:
    """
    Display single ticket to terminal.

    Command: read:ticket <key> [--template <name>] [--category <cat>]
    """
    ticket = fetch_ticket(args.key, config)
    template_name = getattr(args, "template", "obsidian")
    template_fn = TEMPLATES.get(template_name, obsidian.transform)
    print(template_fn(ticket))


def handle_read_tickets(config: "Config", args) -> None:
    """
    Display multiple tickets to terminal.

    Command: read:tickets <key1> <key2> ... [--template <name>]
    """
    tickets = fetch_tickets(args.keys, config)
    template_name = getattr(args, "template", "obsidian")
    template_fn = TEMPLATES.get(template_name, obsidian.transform)

    for ticket in tickets:
        print(f"\n{'='*60}\n")
        print(template_fn(ticket))


def handle_sync_ticket(config: "Config", args) -> None:
    """
    Sync single ticket to vault.

    Command: sync:ticket <key> [--category <cat>] [--force]
    """
    ticket = fetch_ticket(args.key, config)
    content = obsidian.transform(ticket)
    category = getattr(args, "category", None)
    force = getattr(args, "force", False)

    path = write_file(ticket, content, config, category=category, force=force)

    if path:
        print(f"Synced {ticket.key} to {path}")
    else:
        print(f"Skipped {ticket.key} (unchanged)")


def handle_sync_tickets(config: "Config", args) -> None:
    """
    Sync multiple tickets to vault.

    Command: sync:tickets <key1> <key2> ... [--category <cat>]
    """
    tickets = fetch_tickets(args.keys, config)
    category = getattr(args, "category", None)

    synced = 0
    skipped = 0

    for ticket in tickets:
        content = obsidian.transform(ticket)
        path = write_file(ticket, content, config, category=category)

        if path:
            print(f"Synced {ticket.key} to {path}")
            synced += 1
        else:
            skipped += 1

    print(f"\nSynced: {synced}, Skipped: {skipped}")


def handle_set_description(config: "Config", args) -> None:
    """
    Update ticket description in Jira.

    Command: set:description <key> <description>
    """
    from ..lib.jira_client import get_client

    conn = get_client(config)
    issue = conn.client.issue(args.key)
    issue.update(fields={"description": args.description})
    print(f"Updated description for {args.key}")


# Command registry for CLI discovery
COMMANDS = {
    "read:ticket": {
        "handler": handle_read_ticket,
        "help": "Display single ticket",
        "args": [
            {"names": "key", "kwargs": {"help": "Ticket key (e.g., SR-1234)"}},
            {"names": ["--template", "-t"], "kwargs": {"default": "obsidian", "help": "Output template"}},
            {"names": ["--category", "-C"], "kwargs": {"help": "Category folder"}},
        ],
    },
    "read:tickets": {
        "handler": handle_read_tickets,
        "help": "Display multiple tickets",
        "args": [
            {"names": "keys", "kwargs": {"nargs": "+", "help": "Ticket keys"}},
            {"names": ["--template", "-t"], "kwargs": {"default": "obsidian", "help": "Output template"}},
        ],
    },
    "sync:ticket": {
        "handler": handle_sync_ticket,
        "help": "Sync single ticket to vault",
        "args": [
            {"names": "key", "kwargs": {"help": "Ticket key"}},
            {"names": ["--category", "-C"], "kwargs": {"help": "Category folder"}},
            {"names": ["--force", "-f"], "kwargs": {"action": "store_true", "help": "Overwrite even if unchanged"}},
        ],
    },
    "sync:tickets": {
        "handler": handle_sync_tickets,
        "help": "Sync multiple tickets to vault",
        "args": [
            {"names": "keys", "kwargs": {"nargs": "+", "help": "Ticket keys"}},
            {"names": ["--category", "-C"], "kwargs": {"help": "Category folder"}},
        ],
    },
    "set:description": {
        "handler": handle_set_description,
        "help": "Update ticket description",
        "args": [
            {"names": "key", "kwargs": {"help": "Ticket key"}},
            {"names": "description", "kwargs": {"help": "New description text"}},
        ],
    },
}
```

---

### ticket/__init__.py
```python
"""Ticket domain - core ticket operations."""
from .types import JiraTicket, LocalTicket, DiffResult
from .query import fetch_ticket, fetch_tickets
from .persist import write_file, read_file, find_ticket_file
from .diff import compare, load_local_ticket

__all__ = [
    "JiraTicket",
    "LocalTicket",
    "DiffResult",
    "fetch_ticket",
    "fetch_tickets",
    "write_file",
    "read_file",
    "find_ticket_file",
    "compare",
    "load_local_ticket",
]
```

---

## cli.py - Command Discovery
```python
#!/usr/bin/env python3
"""
CLI for Jira Sync - thin command dispatcher.

Discovers commands from domain modules and dispatches to handlers.
"""
import argparse
import importlib
import sys
from pathlib import Path
from typing import Callable, Any

from dotenv import load_dotenv

from .config import Config

# Domains to scan for commands
DOMAINS = [
    "ticket",
    "comment",
    "epic",
    "project",
    "status",
    "link",
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
            mod = importlib.import_module(f"jira.{domain}.commands")
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

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Register each command
    for name, cmd_config in commands.items():
        subparser = subparsers.add_parser(name, help=cmd_config.get("help", ""))

        for arg in cmd_config.get("args", []):
            names = arg["names"]
            if isinstance(names, str):
                names = [names]
            kwargs = arg.get("kwargs", {})
            subparser.add_argument(*names, **kwargs)

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
        return cmd_config["handler"](args)

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
```

---

## Migration Steps (Detailed)

### Phase 1: Create lib/ foundation
Files to create:
1. `lib/__init__.py` - exports
2. `lib/text.py` - sanitize_name, format_size, truncate
3. `lib/jira_markup.py` - jira_to_md, md_to_jira
4. `lib/jira_client.py` - get_client, JiraConnection
5. `lib/markdown/__init__.py` - exports
6. `lib/markdown/frontmatter.py` - build_frontmatter, parse_frontmatter
7. `lib/markdown/tags.py` - format_tags, format_obsidian_tag
8. `lib/markdown/links.py` - format_wiki_link, format_wiki_links
9. `lib/markdown/code_blocks.py` - format_code_block, format_callout
10. `lib/markdown/types/__init__.py` - exports
11. `lib/markdown/types/description.py` - transform_description
12. `lib/markdown/types/metadata.py` - transform_metadata, build_tag_line
13. `lib/markdown/types/comment.py` - transform_comment, transform_comments

**Verification:** Each function should be importable and testable independently.

### Phase 2: Create ticket/ domain
Files to create:
1. `ticket/__init__.py` - exports
2. `ticket/types.py` - JiraTicket, LocalTicket, DiffResult
3. `ticket/query.py` - fetch_ticket, fetch_tickets
4. `ticket/templates/__init__.py` - exports
5. `ticket/templates/protocol.py` - TicketTemplate protocol
6. `ticket/templates/obsidian.py` - transform, file_extension
7. `ticket/templates/plain.py` - transform
8. `ticket/templates/json.py` - transform
9. `ticket/persist.py` - write_file, read_file, find_ticket_file
10. `ticket/diff.py` - compare, load_local_ticket
11. `ticket/commands.py` - COMMANDS dict, handlers

**Verification:** `cd .. && python -m jira-sync read:ticket SR-3536` should work.

### Phase 3: Create other domains
Each domain follows same pattern. Priority order:
1. **comment/** - read:comments, add:comment
2. **status/** - read:status, read:transitions, set:status
3. **admin/** - init, test, setup
4. **epic/** - read:epic, sync:epic
5. **project/** - read:project, sync:project
6. **jql/** - read:jql, sync:jql
7. **link/** - add:link

### Phase 4: Wire up CLI
1. Update `cli.py` with discover_commands()
2. Update `__init__.py` with new exports
3. Update `__main__.py` if needed

### Phase 5: Cleanup
1. Delete: `client.py`, `formatter.py`, `sync.py`
2. Delete empty: `commands/`, `services/` folders

---

## Verification Checklist

### Unit Tests
- [ ] lib/text.py: sanitize_name with various inputs
- [ ] lib/jira_markup.py: jira_to_md round-trip
- [ ] lib/markdown/frontmatter.py: build/parse cycle
- [ ] ticket/types.py: JiraTicket.to_dict()

### Integration Tests
- [ ] `cd .. && python -m jira-sync read:ticket SR-3536` - displays ticket
- [ ] `cd .. && python -m jira-sync read:ticket SR-3536 --template plain` - plain format
- [ ] `cd .. && python -m jira-sync read:ticket SR-3536 --template json` - JSON output
- [ ] `cd .. && python -m jira-sync sync:ticket SR-3536` - creates file
- [ ] `cd .. && python -m jira-sync sync:ticket SR-3536` (second run) - skips unchanged

### End-to-End
- [ ] Full sync workflow: read -> sync -> verify file
- [ ] Template switching works across all formats
- [ ] Category folders created correctly

---

## Files to Delete
- `client.py`
- `formatter.py`
- `sync.py`
- `commands/` folder (if exists)
- `services/` folder (if exists)

## Files to Keep/Modify
- `config.py` - keep, may enhance later
- `cli.py` - complete rewrite
- `__init__.py` - update exports
- `__main__.py` - keep as-is
