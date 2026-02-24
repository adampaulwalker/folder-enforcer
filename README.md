# folder-enforcer

A linter for your folder structure. Define what belongs at the top level, get warned when stray files appear.

Built this after my spouse's Syncthing accidentally dumped her entire Desktop into my dev folder. Never again.

## Install

```bash
curl -o /usr/local/bin/folder-enforcer https://raw.githubusercontent.com/adampaulwalker/folder-enforcer/main/folder-enforcer.sh
chmod +x /usr/local/bin/folder-enforcer
```

Or just clone it:

```bash
git clone https://github.com/adampaulwalker/folder-enforcer.git
```

## Quick Start

```bash
cd ~/Syncthing  # or any directory you want to keep clean

# Generate rules from current structure
folder-enforcer init

# Edit .folder-rules - remove items that shouldn't be there
vim .folder-rules

# Check for strays
folder-enforcer

# Interactively sort them
folder-enforcer --interactive
```

## How It Works

You create a `.folder-rules` file that lists every item allowed at the top level:

```
# My allowed structure
clients
projects
research
notes
.git
.DS_Store
README.md

# Category hints for --interactive mode
# Format: pattern:*glob* -> destination/
pattern:*research*|*analysis* -> research/
pattern:*client*|*invoice* -> clients/
pattern:*.md|*.txt -> notes/
```

Run `folder-enforcer` and it flags anything not on the list. Run with `--interactive` to sort strays into the right folders.

## Use as a Git Hook, Cron Job, or Claude Code Hook

**Cron (check every hour):**
```bash
0 * * * * /usr/local/bin/folder-enforcer ~/Syncthing 2>&1 | logger -t folder-enforcer
```

**Claude Code hook (check on session end):**
```json
{
  "Stop": [{
    "matcher": "*",
    "hooks": [{
      "type": "command",
      "command": "folder-enforcer ~/Syncthing 2>/dev/null || true"
    }]
  }]
}
```

**Shell prompt (warn on cd):**
```bash
cd() { builtin cd "$@" && [[ -f .folder-rules ]] && folder-enforcer . 2>/dev/null; }
```

## Why

Every synced folder accumulates entropy. Files appear from shared devices, temp files stick around, one-off downloads never get sorted. This tool is the equivalent of a linter for your file system - define the rules once, catch violations automatically.

## License

MIT
