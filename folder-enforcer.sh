#!/bin/bash
# folder-enforcer.sh - Lint your folder structure. Catch stray files before they multiply.
#
# Usage:
#   folder-enforcer.sh                     Check for strays (exit 1 if found)
#   folder-enforcer.sh --interactive       Interactively sort stray files
#   folder-enforcer.sh init                Generate a .folder-rules file
#
# Configuration:
#   Create a .folder-rules file in any directory (or run `init` to generate one).
#   List one allowed item per line. Lines starting with # are comments.
#   Use pattern: prefix to add category suggestions for interactive mode.
#
# Example .folder-rules:
#   # Core folders
#   clients
#   projects
#   research
#   notes
#   # Infrastructure
#   .git
#   .DS_Store
#   README.md
#   # Category hints (used in --interactive mode)
#   pattern:*research*|*review*|*analysis* -> research/
#   pattern:*client*|*invoice* -> clients/
#   pattern:*.md|*.txt -> notes/

set -euo pipefail

VERSION="0.1.0"
RULES_FILE=".folder-rules"

# Colors (disabled if not a terminal)
if [[ -t 2 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' BOLD='' NC=''
fi

usage() {
  echo "folder-enforcer v${VERSION} - Lint your folder structure" >&2
  echo "" >&2
  echo "Usage:" >&2
  echo "  folder-enforcer.sh [OPTIONS] [DIRECTORY]" >&2
  echo "" >&2
  echo "Options:" >&2
  echo "  --interactive, -i    Interactively sort stray files" >&2
  echo "  init                 Generate a .folder-rules file from current structure" >&2
  echo "  --help, -h           Show this help" >&2
  echo "  --version, -v        Show version" >&2
  echo "" >&2
  echo "Configuration:" >&2
  echo "  Place a .folder-rules file in the target directory." >&2
  echo "  Run 'folder-enforcer.sh init' to generate one from the current contents." >&2
}

# Parse .folder-rules into allowed list and pattern hints
parse_rules() {
  local rules_path="$1"
  ALLOWED_ITEMS=""
  PATTERN_HINTS=""

  while IFS= read -r line; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

    if [[ "$line" =~ ^pattern: ]]; then
      PATTERN_HINTS="${PATTERN_HINTS}${line#pattern:}"$'\n'
    else
      ALLOWED_ITEMS="${ALLOWED_ITEMS}${line}"$'\n'
    fi
  done < "$rules_path"
}

is_allowed() {
  echo "$ALLOWED_ITEMS" | grep -qxF "$1"
}

# Suggest category based on pattern hints in .folder-rules
suggest_category() {
  local name="$1"
  local lower
  lower=$(echo "$name" | tr '[:upper:]' '[:lower:]')

  while IFS= read -r hint; do
    [[ -z "$hint" ]] && continue
    local patterns="${hint%% -> *}"
    local target="${hint##* -> }"

    # Split patterns by |
    echo "$patterns" | tr '|' '\n' | while IFS= read -r pat; do
      # shellcheck disable=SC2254
      case "$lower" in
        $pat) echo "$target"; exit 0 ;;
      esac
    done | head -1
  done <<< "$PATTERN_HINTS"
}

# Generate .folder-rules from current directory contents
do_init() {
  local target_dir="$1"
  local rules_path="$target_dir/$RULES_FILE"

  if [[ -f "$rules_path" ]]; then
    echo -e "${YELLOW}$RULES_FILE already exists in $target_dir${NC}" >&2
    echo "Edit it directly, or delete it and run init again." >&2
    exit 1
  fi

  {
    echo "# folder-enforcer rules"
    echo "# Generated $(date +%Y-%m-%d) from current directory contents"
    echo "# Remove items that shouldn't be here; keep what belongs."
    echo ""
    echo "# Allowed top-level items"
    ls -1A "$target_dir" | while read -r item; do
      echo "$item"
    done
    echo ""
    echo "# Category hints for --interactive mode"
    echo "# Format: pattern:*glob*|*glob* -> target-folder/"
    echo "# pattern:*research*|*analysis* -> research/"
    echo "# pattern:*client*|*invoice* -> clients/"
  } > "$rules_path"

  echo -e "${GREEN}Created $rules_path${NC}" >&2
  echo "Edit it to define your allowed structure, then run:" >&2
  echo "  folder-enforcer.sh $target_dir" >&2
}

# Main
INTERACTIVE=false
TARGET_DIR=""
ACTION="check"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --interactive|-i) INTERACTIVE=true; shift ;;
    --help|-h) usage; exit 0 ;;
    --version|-v) echo "folder-enforcer v${VERSION}"; exit 0 ;;
    init) ACTION="init"; shift ;;
    *) TARGET_DIR="$1"; shift ;;
  esac
done

TARGET_DIR="${TARGET_DIR:-.}"
TARGET_DIR=$(cd "$TARGET_DIR" && pwd)

# Init mode
if [[ "$ACTION" == "init" ]]; then
  do_init "$TARGET_DIR"
  exit 0
fi

# Check for rules file
if [[ ! -f "$TARGET_DIR/$RULES_FILE" ]]; then
  echo -e "${RED}No $RULES_FILE found in $TARGET_DIR${NC}" >&2
  echo "Run: folder-enforcer.sh init $TARGET_DIR" >&2
  exit 1
fi

parse_rules "$TARGET_DIR/$RULES_FILE"

# Find strays
strays=()
while IFS= read -r name; do
  [[ "$name" == "$RULES_FILE" ]] && continue
  if ! is_allowed "$name"; then
    strays+=("$name")
  fi
done < <(ls -1A "$TARGET_DIR" 2>/dev/null)

# Report
if [[ ${#strays[@]} -eq 0 ]]; then
  echo -e "${GREEN}All clean - no stray files in $TARGET_DIR${NC}" >&2
  exit 0
fi

echo "" >&2
echo -e "${BOLD}Found ${#strays[@]} item(s) that don't belong in $TARGET_DIR:${NC}" >&2
echo "" >&2
for stray in "${strays[@]}"; do
  suggestion=$(suggest_category "$stray")
  suggestion="${suggestion:-"(no suggestion)"}"
  if [[ -d "$TARGET_DIR/$stray" ]]; then
    echo -e "  ${YELLOW}[folder]${NC} $stray  -->  $suggestion" >&2
  else
    echo -e "  ${YELLOW}[file]${NC}   $stray  -->  $suggestion" >&2
  fi
done
echo "" >&2

# Interactive mode
if [[ "$INTERACTIVE" == true ]]; then
  # Collect folder names for menu
  folders=()
  while IFS= read -r name; do
    [[ "$name" == "$RULES_FILE" ]] && continue
    if is_allowed "$name" && [[ -d "$TARGET_DIR/$name" ]]; then
      folders+=("$name")
    fi
  done < <(ls -1A "$TARGET_DIR" 2>/dev/null)

  # Build menu
  echo "Available destinations:" >&2
  for i in "${!folders[@]}"; do
    echo "  [$((i+1))] ${folders[$i]}/" >&2
  done
  echo "  [s] skip" >&2
  echo "  [t] trash (move to ~/.Trash)" >&2
  echo "" >&2

  for stray in "${strays[@]}"; do
    suggestion=$(suggest_category "$stray")
    echo -e "${BOLD}$stray${NC}${suggestion:+  (suggested: $suggestion)}" >&2
    read -p "  Move to: " choice < /dev/tty

    case "$choice" in
      t) mv "$TARGET_DIR/$stray" "$HOME/.Trash/" && echo -e "  ${GREEN}-> Trash${NC}" >&2 ;;
      s|"") echo "  skipped" >&2 ;;
      *)
        if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#folders[@]} )); then
          dest="${folders[$((choice-1))]}"
          mv "$TARGET_DIR/$stray" "$TARGET_DIR/$dest/" && echo -e "  ${GREEN}-> $dest/${NC}" >&2
        else
          echo "  skipped (invalid choice)" >&2
        fi
        ;;
    esac
  done
else
  echo "Run with --interactive to sort them, or edit $RULES_FILE to allow them." >&2
fi

exit 1
