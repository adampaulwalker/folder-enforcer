# folder-enforcer

A linter for your folder structure. Define what belongs at the top level, get warned when stray files appear.

Built this after my spouse's Syncthing accidentally dumped her entire Desktop into my dev folder. Never again.

## Two ways to use it

### 1. CLI script (reactive)

Checks your folder structure and flags anything that doesn't belong.

```bash
# Generate rules from current structure
./folder-enforcer.sh init

# Edit .folder-rules - remove what shouldn't be there
vim .folder-rules

# Check for strays
./folder-enforcer.sh

# Interactively sort them
./folder-enforcer.sh --interactive
```

### 2. MCP server (proactive)

An MCP that Claude calls *before* saving files to suggest the right location. Works with Claude Code, Claude Desktop, and Claude Cowork.

```
You: "save this research on standing desks"
Claude calls: suggest_location("standing desk research", "markdown")
MCP returns: research/standing-desks.md
Claude: "I'll save this to research/standing-desks.md - sound good?"
```

## Install

### CLI script

```bash
curl -o /usr/local/bin/folder-enforcer https://raw.githubusercontent.com/adampaulwalker/folder-enforcer/main/folder-enforcer.sh
chmod +x /usr/local/bin/folder-enforcer
```

### MCP server (Claude Code)

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "folder-enforcer": {
      "command": "python3",
      "args": ["/path/to/folder-enforcer/server.py"]
    }
  }
}
```

Requires `mcp` package: `pip install mcp`

## The `.folder-rules` file

Both the CLI and MCP read from the same config. Place it at `~/.folder-rules` or in any directory as `.folder-rules`.

```
# Allowed top-level folders
clients
projects
research
notes
.git
.DS_Store

# Pattern hints - used by MCP and interactive mode
# Format: pattern:*glob*|*glob* -> destination/
pattern:*research*|*analysis* -> research/
pattern:*client*|*invoice* -> clients/
pattern:*.md|*.txt -> notes/
```

See [.folder-rules.example](.folder-rules.example) for a full example.

## MCP tools

### `suggest_location`

Suggest the best folder for a file based on your rules. Call before saving any file.

```
suggest_location(
  description="standing desk research",
  file_type="markdown"
)
# Returns: "Suggested: research/standing-desks.md"
```

Pass `proposed_path` to validate an existing path instead:

```
suggest_location(
  description="invoice",
  proposed_path="misc/invoice.pdf"
)
# Returns: "Invalid: 'misc/' is not an allowed top-level folder."
```

### `get_rules`

Returns the raw `.folder-rules` file so Claude has full context about your folder structure.

## Hook integration

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

Every synced folder accumulates entropy. Files appear from shared devices, temp files stick around, one-off downloads never get sorted. This tool is the equivalent of a linter for your file system - define the rules once, catch violations automatically. The MCP takes it further: instead of cleaning up after the mess, it prevents the mess in the first place.

## License

MIT
