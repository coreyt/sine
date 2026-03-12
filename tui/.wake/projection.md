# System Check
- **Schema**: Schema version 1 (up-to-date)
- **MCP**: MCP available (wake-mcp binary, mcp module)
- **Store**: Store has 558 events
- **Smart Events** WARNING: Previous session had 4 events but 0 Smart Events — you MUST log decisions, constraints, and rejections using wake MCP tools or `wake log` CLI commands. See 'Wake: What to Log' section below.
- **Custom Types**: No custom event types registered
- **Shared Events**: No .gitignore found — run `wake share-init` to enable sharing

# Changes Since Last Session
_Since: 2026-03-06T02:32:15.791124+00:00_


## Recent Activity
- Modified registry.py (05:33)
- Modified registry.py (05:34)
- Modified registry.py (05:34)
- Modified config_editor.py (05:34)
- Modified app.tcss (05:35)
- Modified test_catalog.py (05:35)
- Modified test_config_editor.py (05:35)
- Modified test_registry_screen.py (05:36)
- Ran `uv run pytest tests/ -x -q 2>&1` (05:36)
- Consulted 3 files: test_config_editor.py, input_dialog.py, app.tcss

---

# Project Status
_Last updated: 2026-03-06T05:50:09.347760+00:00_

## Constraints
_None logged._

## Wake: What to Log

You MUST log Smart Events when you recognize these moments. Without them, the next session has no memory of your decisions, constraints, or rejected approaches.

| Moment | Command |
|--------|---------|
| Quick one-liner (auto-classified) | `wake note "I chose X over Y because Z"` |
| You choose between approaches | `wake log decision --decision '...' --rationale '...' --rejected '...'` |
| You discover a rule that must be followed | `wake log constraint --rule '...' --scope '...' --reason '...' --severity hard` |
| You need human input to proceed | `wake log blocked --question '...' --context '...'` |
| You try something and it fails | `wake log rejection --approach '...' --reason '...' --context '...'` |
| You start a distinct unit of work | `wake log task-start --description '...'` |
| You finish a unit of work | `wake log task-done --task-id '...' --description '...'` |
| You finish exploring how a subsystem works | `wake log knowledge --topic '...' --summary '...' --files '...'` |
| Context window is filling up (you'll be warned) | `wake log checkpoint --summary '...' --next-steps '...' --files '...'` |
| You are about to enter plan mode | `wake plan-check` (also fires automatically via PreToolUse hook) |
| Session ends with no Smart Events | `wake extract-smart-events` (runs automatically via Stop hook) |
| Human asks you to review a stale item | `wake review <id> --action agree\|revisit\|refresh\|persist` |
| A decision applies to a specific area | `wake scope <id> --scope "path"` |
| Agent detects conflicting decisions | Ask the user: supersede, scope, keep both, or withdraw |
| Need latest teammate data mid-session | `wake fetch` (imports shared events + re-renders) |

**Plan mode**: Planning is where key decisions happen. When you finalize a plan, log each significant decision (chosen approach + rejected alternatives). Constraints and rejections discovered during exploration should be logged as they arise — the plan file is ephemeral, Smart Events persist.

To verify events were stored: `wake reduce` (prints current state as JSON). MCP equivalents (`wake_log_decision`, etc.) also work if available.

Without these, the next session sees only file edits and bash commands — no decisions, no constraints, no context.

## Blocked (waiting on human)
_None logged._

## Do Not Retry
_None logged._

## Decisions
_None logged._

## Recent Activity
_(35 earlier entries omitted)_
- Ran `uv run pytest tests/ -x -q 2>&1 | tail -5` (05:26)
- Modified catalog.py (05:32)
- Modified catalog.py (05:33)
- Modified config.py (05:33)
- Modified input_dialog.py (05:33)
- Modified registry.py (05:33)
- Modified registry.py (05:34)
- Modified registry.py (05:34)
- Modified config_editor.py (05:34)
- Modified app.tcss (05:35)
- Modified test_catalog.py (05:35)
- Modified test_config_editor.py (05:35)
- Modified test_registry_screen.py (05:36)
- Ran `uv run pytest tests/ -x -q 2>&1` (05:36)
- Consulted 3 files: test_config_editor.py, input_dialog.py, app.tcss

## Completed
_None logged._
