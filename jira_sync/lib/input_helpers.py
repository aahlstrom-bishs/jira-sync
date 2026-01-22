"""
Shared input helpers for CLI commands.
"""
import sys


def resolve_text_input(args, text_attr: str = "body", file_attr: str = "file") -> str:
    """
    Resolve text from positional arg, file, or stdin.

    Priority:
    1. --file flag (if provided)
    2. stdin (if '-' passed or piped input with no text arg)
    3. Positional text argument

    Args:
        args: Parsed argparse namespace
        text_attr: Name of the positional text attribute (default: "body")
        file_attr: Name of the file flag attribute (default: "file")

    Returns:
        Resolved text content, stripped of leading/trailing whitespace
    """
    # File flag takes precedence
    if getattr(args, file_attr, None):
        with open(getattr(args, file_attr), 'r') as f:
            return f.read().strip()

    text_value = getattr(args, text_attr, None)

    # Stdin: explicit '-' or piped input with no text
    if text_value == '-' or (text_value is None and not sys.stdin.isatty()):
        return sys.stdin.read().strip()

    return text_value or ''
