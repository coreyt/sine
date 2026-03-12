## §11.2 Admin / Config

**Purpose:** Application configuration and settings management (setup wizards, settings panels).

**Layout:**

```
┌─ Categories ─┬── General Settings ──────────────┐
│               │                                  │
│ ▸ General     │  Application Name                │
│   Network     │  [ My App_____________ ]         │
│   Security    │                                  │
│   Advanced    │  Log Level                       │
│               │  (*) Info                        │
│               │  ( ) Debug                       │
│               │  ( ) Error                       │
│               │                                  │
│               │  Enable Caching                  │
│               │  [X] Enabled                     │
│               │                                  │
│               │  < Save >   < Cancel >           │
├───────────────┴──────────────────────────────────┤
│ F1 Help  Tab Next  Esc Cancel  Enter Save        │
└──────────────────────────────────────────────────┘
```

**Structure:**

| Area | Position | Content |
|------|----------|---------|
| Region A — Sidebar | Left, 8–16 cols | Category list |
| Region B — Form | Center, flex | Tabbed or sectioned form fields |
| Footer | Bottom, 1–2 rows | Key strip |

**Keyboard (inherits all Tier 1):**

| Key | Action | Tier |
|-----|--------|------|
| `?` | Help | Tier 1 |
| Esc | Back / cancel edit | Tier 1 |
| Ctrl+S | Save | Archetype |
| Number keys (1–9) | Jump to sidebar item N | Archetype |
| `[` / `]` | Previous / next settings tab | Archetype |

Note: Single-letter Tier 2 keys (`d`, `e`, `a`) are suppressed in the Admin archetype because form fields dominate the screen. Use Ctrl+ modified keys or buttons instead.

**Key components:** Entry fields, toggles/switches, radio groups, push buttons, tabbed content.
