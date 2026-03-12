---
title: "§R3 256-Color Palette"
description: "Palette structure, semantic role mappings, status colors, and eight named palettes with examples"
weight: 3
---

## §R3.1 Palette Structure

| Index Range | Content |
|------------|---------|
| 0–7 | Standard ANSI colors (black, red, green, yellow, blue, magenta, cyan, white) |
| 8–15 | Bright ANSI colors |
| 16–231 | 6×6×6 color cube: `index = 16 + 36r + 6g + b` (r, g, b = 0–5) |
| 232–255 | 24-step grayscale ramp (232 = darkest, 255 = lightest) |

## §R3.2 Semantic Role → 256-Color Mapping

### Dark Theme (default)

| Semantic Role | Foreground (index) | Background (index) | Hex Approximation |
|--------------|-------------------|-------------------|-------------------|
| Primary | 75 (light blue) | 17 (dark blue) | fg #5fafff, bg #00005f |
| Secondary | 109 (muted blue) | 236 (dark gray) | fg #87afaf, bg #303030 |
| Tertiary | 79 (teal) | 236 (dark gray) | fg #5fd7af, bg #303030 |
| Error | 196 (bright red) | 52 (dark red) | fg #ff0000, bg #5f0000 |
| Neutral fg | 252 (light gray) | — | fg #d0d0d0 |
| Neutral fg bright | 231 (white) | — | fg #ffffff |
| Neutral bg | — | 235 (near-black) | bg #262626 |
| Surface | 252 | 234 (charcoal) | bg #1c1c1c |

**Neutral fg bright** is for text on colored backgrounds (headers, selected tabs, active indicators) where standard neutral fg lacks sufficient contrast.

### Light Theme

| Semantic Role | Foreground (index) | Background (index) | Hex Approximation |
|--------------|-------------------|-------------------|-------------------|
| Primary | 25 (dark blue) | 189 (light blue) | fg #005faf, bg #d7d7ff |
| Secondary | 66 (muted blue) | 254 (near-white) | fg #5f8787, bg #e4e4e4 |
| Tertiary | 30 (dark teal) | 254 (near-white) | fg #008787, bg #e4e4e4 |
| Error | 124 (dark red) | 224 (light pink) | fg #af0000, bg #ffd7d7 |
| Neutral fg | 235 (dark gray) | — | fg #262626 |
| Neutral bg | — | 255 (white) | bg #eeeeee |
| Surface | 235 | 231 (pure white) | bg #ffffff |

## §R3.3 Status Color Mapping

| Status | Dark Theme (FG index) | Light Theme (FG index) | Paired Symbol |
|--------|----------------------|----------------------|---------------|
| Healthy / Success | 40 (green) | 28 (dark green) | `◉` or `✓` |
| Error / Critical | 196 (bright red) | 124 (dark red) | `✗` or `●` |
| Warning / Caution | 220 (yellow) | 172 (orange) | `⚠` or `▲` |
| Inactive / Disabled | 240 (gray) | 247 (gray) | `○` or `—` |

## §R3.4 Named Palettes

The Dark Theme and Light Theme mappings above (§R3.2) define the default palettes. Applications MAY offer additional named palettes. Eight named palettes are defined here, drawn from the historical research that informs the standard. All palettes map to the same five semantic roles ([§5.1](/standard/color/#51-semantic-color-roles)); they differ only in color assignment.

### Default

Source: Textual framework default dark theme. This is the standard modern dark palette — the recommended starting point for new applications. It uses the same 256-color mappings defined in §R3.2 Dark Theme.

| Semantic Role | Foreground (index) | Background (index) | Hex Approximation |
|--------------|-------------------|-------------------|-------------------|
| Primary | 75 (light blue) | 17 (dark blue) | fg #5fafff, bg #00005f |
| Secondary | 109 (muted blue) | 236 (dark gray) | fg #87afaf, bg #303030 |
| Tertiary | 79 (teal) | 236 (dark gray) | fg #5fd7af, bg #303030 |
| Error | 196 (bright red) | 52 (dark red) | fg #ff0000, bg #5f0000 |
| Neutral fg | 252 (light gray) | — | fg #d0d0d0 |
| Neutral fg bright | 231 (white) | — | fg #ffffff |
| Neutral bg | — | 235 (near-black) | bg #262626 |
| Surface | 252 | 234 (charcoal) | bg #1c1c1c |

Status colors:

| Status | Foreground (index) | Paired Symbol |
|--------|-------------------|---------------|
| Healthy / Success | 40 (green) | `◉` or `✓` |
| Error / Critical | 196 (bright red) | `✗` or `●` |
| Warning / Caution | 220 (yellow) | `⚠` or `▲` |
| Inactive / Disabled | 240 (gray) | `○` or `—` |

Example — Dashboard rendered in Default:

<pre class="palette-example palette-default"><span style="color:#585858">┌──</span> <span style="font-weight:bold;color:#5fafff">Service Monitor</span> <span style="color:#585858">────────────────────────────────────────────────────────────┐
│</span> <span style="color:#87afaf">File  View  Help</span>                                                              <span style="color:#585858">│
├───────────────────────────────────────────────────────────────────────────────┤</span>
<span style="color:#585858">│</span>                                                                               <span style="color:#585858">│</span>
<span style="color:#585858">│</span>  CPU: 34%          Services: 12/12          Alerts: 3          Mem: 61%       <span style="color:#585858">│</span>
<span style="color:#585858">│</span>                                                                               <span style="color:#585858">│
├───────────────────────────────────────────────────────────────────────────────┤</span>
<span style="color:#585858">│</span> Service              │ Status   │ Uptime       │ CPU     │ Memory             <span style="color:#585858">│</span>
<span style="color:#585858">│</span>──────────────────────│──────────│──────────────│─────────│────────────────────<span style="color:#585858">│</span>
<span style="color:#585858">│</span> <span style="background:#00005f;color:#5fafff">> api-gateway        │ </span><span style="background:#00005f;color:#00d700"> OK</span><span style="background:#00005f;color:#5fafff">      │ 14d  3h 22m  │   2.1%  │  340MB            </span> <span style="color:#585858">│</span>
<span style="color:#585858">│</span>   auth-service       │ <span style="color:#00d700"> OK</span>      │ 14d  3h 22m  │   0.8%  │  128MB             <span style="color:#585858">│</span>
<span style="color:#585858">│</span>   worker-pool        │ <span style="color:#ffd700"> WARN</span>    │  0d  1h 45m  │  78.3%  │  1.2GB             <span style="color:#585858">│</span>
<span style="color:#585858">│</span>   notification-svc   │ <span style="color:#ff0000"> DOWN</span>    │  0d  0h 00m  │   0.0%  │    0MB             <span style="color:#585858">│</span>
<span style="color:#585858">│</span>   metrics-collector  │ <span style="color:#00d700"> OK</span>      │ 14d  3h 22m  │   1.4%  │  256MB             <span style="color:#585858">│</span>
<span style="color:#585858">│</span>                                                                               <span style="color:#585858">│
├───────────────────────────────────────────────────────────────────────────────┤</span>
<span style="color:#585858">│</span><span style="color:#87afaf"> ? Help  r Refresh  / Filter  q Quit                             5 services    </span><span style="color:#585858">│</span>
<span style="color:#585858">└───────────────────────────────────────────────────────────────────────────────┘</span></pre>
