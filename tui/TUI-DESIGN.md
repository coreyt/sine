# TUI-DESIGN.md — Lookout TUI

**Version 1.1** — Project-specific overrides to the
[Monospace Design TUI Standard](https://coreyt.github.io/monospace-design-tui/standard/) and
[Rendering Reference](https://coreyt.github.io/monospace-design-tui/reference/).

---

## Meta

| Key              | Value                                          |
|------------------|------------------------------------------------|
| Project          | Lookout                                        |
| Standard URL     | https://coreyt.github.io/monospace-design-tui/ |
| Standard version | 1.0                                            |
| Palette          | Custom (see Waivers below)                     |
| Archetypes       | §11.1 Dashboard, §11.2 Admin                  |
| Framework        | Textual                                        |
| Minimum terminal | 120×40                                         |
| Created          | 2026-03-05                                     |
| Last reviewed    | 2026-03-05                                     |

---

## Waivers

| Section | Rule | Waiver | Rationale |
|---------|------|--------|-----------|
| §4 Palette | Use standard Default palette tokens | WAIVE — use Textual built-in theme colors | Textual provides its own `$primary`, `$surface`, `$text` etc. via design system; remapping to Monospace palette tokens would break theme consistency and dark/light mode support |

---

## Overrides

_No overrides._

---

## Project Conventions

### Screen Layout

- **Pattern Browser** uses Dashboard archetype: left table panel (60%) + right detail panel (40%)
- **Registry** uses Dashboard archetype: left tree panel (30%) + right context panel (70%)
- **Generation Pipeline** uses Admin archetype: left queue panel (30%) + right stage/diff panel (70%)
- **Config Editor** uses Admin archetype: single-column form

### Navigation

Screen navigation uses number keys (§2.2 Tier 3 — conflict-free with Tier 1/2):

| Key | Action         | Scope  |
|-----|----------------|--------|
| `1` | Browser screen | Global |
| `2` | Registry screen| Global |
| `3` | Generate screen| Global |
| `4` | Config screen  | Global |
| `q` | Quit           | Global |
| `?`/F1 | Help        | Global |
| Esc/F3 | Back        | Global |

### Screen-specific Keys

**Browser:**

| Key | Action | Notes |
|-----|--------|-------|
| `/` | Focus filter | Tier 1 |
| `r`/F5 | Refresh index | Tier 1 |

**Registry:**

| Key | Action | Notes |
|-----|--------|-------|
| `a` | Add (new pattern) | Tier 2 |
| `d` | Deprecate | Tier 2 |
| `e` | Edit | Tier 2 |
| `y` | Yank pattern ID | Tier 2 |
| `l` | Add language | Screen-specific |
| `f` | Add framework | Screen-specific |
| `g` | Generate | Screen-specific |
| `w` | Write to disk | Screen-specific |
| `r`/F5 | Refresh | Tier 1 |
| `/` | Filter | Tier 1 |
| Ctrl+A | Approve generation | Screen-specific (avoids Tier 2 `a` conflict) |
| Ctrl+X | Reject generation | Screen-specific |

**Generation:**

| Key | Action | Notes |
|-----|--------|-------|
| `a` | Add job | Tier 2 |
| `t` | Retry stage | Screen-specific |
| `w` | Write YAML | Screen-specific |
| `r`/F5 | Refresh | Tier 1 |
| Ctrl+A | Approve stage | Screen-specific |
| Ctrl+X | Reject stage | Screen-specific |

**Config:**

| Key | Action | Notes |
|-----|--------|-------|
| Ctrl+S | Save | §11.2 Admin archetype (form-dominant screen) |

### Case-Insensitive Bindings (§2.2)

All single-letter bindings use the `ci()` helper which binds both lower and upper case, displaying only lowercase in the footer. The `ci()` function is defined in `app.py`.

### Responsive Breakpoints (§1.6)

The app applies CSS classes on resize:

| Class | Columns | Behavior |
|-------|---------|----------|
| `.compact` | <80 | Sidebars hidden, content fills width |
| `.standard` | 80–119 | Narrow sidebars |
| `.expanded` | 120–159 | Default layout |
| `.wide` | 160+ | Wider sidebars |

### Color Semantics

- Pipeline status indicators use Unicode symbols with semantic colors:
  - `○` pending (dim), `◐` running (yellow), `●` review (cyan)
  - `✓` approved (green), `✗` rejected (red), `!` error (red bold)

---

## Decision Log

| Date       | Decision | Rationale |
|------------|----------|-----------|
| 2026-03-05 | Dashboard + Admin archetypes | Browser is read-heavy (dashboard), generation is write-heavy (admin) |
| 2026-03-05 | Custom palette (Textual built-in) | Textual's design system provides consistent theming; remapping would break dark/light mode |
| 2026-03-05 | 120×40 minimum | Pattern tables need horizontal space for columns |
| 2026-03-05 | Number keys for screen nav | Avoids conflicts with Tier 1 `r` (refresh) and Tier 2 `d`/`e`/`a` |
| 2026-03-05 | Ctrl+A/Ctrl+X for approve/reject | Frees `a` for Tier 2 Add and avoids `r` conflict with Tier 1 Refresh |
| 2026-03-05 | `ci()` helper for bindings | Ensures §2.2 case-insensitivity compliance across all screens |
