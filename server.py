"""folder-enforcer MCP server.

A proactive file organization assistant. Claude calls suggest_location BEFORE
saving files to get the right destination path based on .folder-rules.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from engine import find_rules_path, load_rules, suggest, validate

mcp = FastMCP(
    "folder-enforcer",
    instructions=(
        "File organization assistant. Call suggest_location BEFORE saving any "
        "file to get the right folder path. Call get_rules to see the user's "
        "folder structure."
    ),
)

# Cache rules in memory (reloaded if file changes)
_rules_cache = None
_rules_mtime: float = 0


def _get_rules():
    """Load rules with simple file-change detection."""
    global _rules_cache, _rules_mtime

    path = find_rules_path()
    if path is None:
        return None

    mtime = path.stat().st_mtime
    if _rules_cache is None or mtime != _rules_mtime:
        _rules_cache = load_rules([str(path)])
        _rules_mtime = mtime

    return _rules_cache


@mcp.tool()
def suggest_location(
    description: str,
    file_type: str = "file",
    proposed_path: str | None = None,
) -> str:
    """Suggest the best folder for a file, or validate a proposed path.

    Call this BEFORE saving any file to get the right destination.

    Args:
        description: What the file is (e.g. "standing desk research",
                     "Acme Corp invoice", "new product idea for todo app")
        file_type: The type - "markdown", "pdf", "code", "folder",
                   or any extension like ".py"
        proposed_path: If set, validates this path instead of suggesting one.
                       Use when you already have a path in mind.
    """
    rules = _get_rules()
    if rules is None:
        return (
            "No .folder-rules file found. Create one at ~/.folder-rules with:\n"
            "  - One allowed folder name per line\n"
            "  - Optional: pattern:*keyword* -> folder/\n"
            "Run 'folder-enforcer init' to generate one from your current structure."
        )

    if proposed_path:
        return validate(rules, proposed_path)

    return suggest(rules, description, file_type)


@mcp.tool()
def get_rules() -> str:
    """Return the current folder organization rules.

    Call this to understand the user's folder structure before suggesting paths.
    Returns the raw .folder-rules file content.
    """
    rules = _get_rules()
    if rules is None:
        return (
            "No .folder-rules file found.\n"
            "Create one at ~/.folder-rules or set $FOLDER_RULES_PATH.\n"
            "Format: one allowed folder per line, plus pattern: hints."
        )

    return rules.raw


if __name__ == "__main__":
    mcp.run(transport="stdio")
