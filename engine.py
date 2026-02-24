"""Folder rules engine - pure Python, no MCP dependencies.

Parses .folder-rules files and matches descriptions to folder categories.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path


@dataclass
class PatternRule:
    globs: list[str]
    target: str


@dataclass
class FolderRules:
    allowed: list[str] = field(default_factory=list)
    patterns: list[PatternRule] = field(default_factory=list)
    raw: str = ""


def parse_rules(content: str) -> FolderRules:
    """Parse .folder-rules file content into structured rules."""
    allowed = []
    patterns = []

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("pattern:"):
            # pattern:*research*|*analysis* -> research/
            rest = line[len("pattern:"):]
            if " -> " not in rest:
                continue
            globs_str, target = rest.split(" -> ", 1)
            globs = [g.strip() for g in globs_str.split("|") if g.strip()]
            patterns.append(PatternRule(globs=globs, target=target.strip()))
        else:
            allowed.append(line)

    return FolderRules(allowed=allowed, patterns=patterns, raw=content)


def load_rules(search_paths: list[str | Path] | None = None) -> FolderRules | None:
    """Load .folder-rules from filesystem using search order.

    Search order:
    1. $FOLDER_RULES_PATH env var
    2. Provided search_paths (e.g. cwd/.folder-rules)
    3. ~/.folder-rules
    """
    import os

    candidates = []

    env_path = os.environ.get("FOLDER_RULES_PATH")
    if env_path:
        candidates.append(Path(env_path))

    if search_paths:
        candidates.extend(Path(p) for p in search_paths)

    candidates.append(Path.home() / ".folder-rules")

    for path in candidates:
        if path.is_file():
            return parse_rules(path.read_text())

    return None


def slugify(text: str) -> str:
    """Convert description to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extension_for(file_type: str) -> str:
    """Map file_type to a file extension."""
    ext_map = {
        "markdown": ".md",
        "md": ".md",
        "pdf": ".pdf",
        "image": ".png",
        "code": "",
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "json": ".json",
        "yaml": ".yaml",
        "folder": "",
        "file": "",
    }
    ft = file_type.lower().strip()
    if ft.startswith("."):
        return ft
    return ext_map.get(ft, "")


def _categories(rules: FolderRules) -> list[str]:
    """Return only user-facing folder categories (not infrastructure items)."""
    return [f for f in rules.allowed if not f.startswith(".") and "." not in f]


def suggest(rules: FolderRules, description: str, file_type: str = "file") -> str:
    """Suggest the best folder path for a file based on rules.

    Returns a human-readable string with the suggestion and reason.
    """
    desc_lower = description.lower()
    ext = extension_for(file_type)
    slug = slugify(description)
    filename = f"{slug}{ext}" if ext else slug
    categories = _categories(rules)

    # Tier 1: Check pattern rules
    for rule in rules.patterns:
        for glob in rule.globs:
            if fnmatch(desc_lower, glob):
                target = rule.target.rstrip("/")
                path = f"{target}/{filename}"
                return (
                    f"Suggested: {path}\n"
                    f"Reason: Matched pattern {glob} -> {rule.target}\n"
                    f"Category: {target}"
                )

    # Tier 2: Check if any category name appears in description
    for folder in categories:
        if folder.lower() in desc_lower:
            path = f"{folder}/{filename}"
            return (
                f"Suggested: {path}\n"
                f"Reason: Description contains category name '{folder}'\n"
                f"Category: {folder}"
            )

    # Tier 3: No match - return categories for Claude to decide
    folders = ", ".join(categories)
    return (
        f"No pattern match for: {description}\n"
        f"Available categories: {folders}\n"
        f"Suggested filename: {filename}\n"
        f"Pick the best category and use: <category>/{filename}"
    )


def validate(rules: FolderRules, path: str) -> str:
    """Validate whether a proposed path conforms to the folder rules.

    Returns a human-readable validation result.
    """
    parts = Path(path).parts
    if not parts:
        return "Invalid: empty path"

    top_level = parts[0]

    if top_level in rules.allowed:
        return f"Valid: {path} is in allowed category '{top_level}/'"

    # Not allowed - suggest the closest match
    categories = _categories(rules)
    desc = " ".join(parts)
    suggestion = suggest(rules, desc, file_type="file")
    return (
        f"Invalid: '{top_level}/' is not an allowed top-level folder.\n"
        f"Allowed: {', '.join(categories)}\n"
        f"\n{suggestion}"
    )
