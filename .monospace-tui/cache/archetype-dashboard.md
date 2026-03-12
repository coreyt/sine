---
title: "§11 Archetypes"
description: "Dashboard, Admin, File Manager, Editor, Fuzzy Finder archetypes plus appendices"
weight: 11
---

An archetype defines a reusable screen pattern with a specific layout, keyboard layer, and component set. Applications MUST select one archetype per screen and adhere to its rules. Applications MAY combine archetypes across screens (e.g., a Dashboard screen and an Admin screen in the same application).

All archetypes inherit the CUA base keyboard ([§2.2](/standard/keyboard/#22-standard-key-assignments)), three-region layout ([§1.3](/standard/layout/#13-three-region-layout)), and footer key strip ([§1.4](/standard/layout/#14-footer-key-strip)).

## §11.1 Dashboard

**Purpose:** Real-time monitoring and status overview (htop, btop, system dashboards).

**Layout:**

```
╔══ Dashboard Title ══════════════════════════════╗
║ ▲ Metric A: 1,234  │ ◉ Status B  │ ⚠ Warns: 3  ║
╠═════════════════════════════════════════════════╣
║ Column 1    │ Column 2 │ Column 3 │ Column 4    ║
║ row data    │ ◉ OK     │  120ms   │ 0           ║
║ row data    │ ⚠ SLOW   │  890ms   │ 2           ║
║ row data    │ ◉ OK     │   45ms   │ 0           ║
╠═════════════════════════════════════════════════╣
║ ?Help  r Refresh  /Filter  s Sort  q Quit       ║
╚═════════════════════════════════════════════════╝
```

**Structure:**

| Area | Rows | Content |
|------|------|---------|
| Header metrics | 1–3 | Metric cards with status indicators |
| Data area | Flex | Scrollable data table or panel grid |
| Footer | 1–2 | Key strip |

**Keyboard (inherits all Tier 1; uses Tier 2 `s`, `/` from standard):**

| Key | Action | Tier |
|-----|--------|------|
| `?` | Help | Tier 1 (common key for F1) |
| `r` | Refresh | Tier 1 (common key for F5) |
| `/` | Activate filter input | Tier 1 |
| `s` | Cycle sort order (asc/desc) | Tier 2 |
| `q` | Quit | Tier 1 |
| Number keys (1–9) | Sort by column N | Archetype-specific |

**Key components:** Metric cards, data table, sparklines, status indicators.

**Example workflow — filter and sort a dashboard table:**

| Step | Key | Action | KLM |
|------|-----|--------|-----|
| 1 | `/` | Open filter | K = 0.28s |
| 2 | Type query | Filter text | M + nK |
| 3 | Enter | Apply filter | K = 0.28s |
| 4 | `s` | Sort focused column | K = 0.28s |
| Total | | 4 keystrokes + query | ~2.2s + typing |
