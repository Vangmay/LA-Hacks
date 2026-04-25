# PaperCourt — Visual Design Principles

A reference for maintaining visual consistency when extending or modifying this prototype.

---

## Typography

Two typefaces only — no exceptions.

- **Space Grotesk** — all UI text: labels, body copy, buttons, headings. Weights 400/500/600/700.
- **JetBrains Mono** — all data-layer text: agent names, verdicts, node type badges, confidence scores, status strings, terminal/feed output. Weights 400/600/700.

The split is semantic: anything that _feels like data or code_ gets mono; anything that _feels like prose or UI chrome_ gets Grotesk.

Font sizes follow a tight scale. Nothing smaller than 9px in mono, 11px in Grotesk. Headers top out at ~22px; this is a dense tool, not a marketing page.

---

## Color

### Dark theme (default)

- **Background:** `#0A0C10` — very dark blue-black, not pure black
- **Surface (cards, panels, header):** `#131720`
- **Sunken surface (feed, sidebar bg):** `#0D1017`
- **Borders:** `rgba(255,255,255,0.08)` — extremely subtle
- **Primary text:** `#E4E7F0`
- **Secondary text / labels:** `#6B7280`

### Light theme

- **Background:** `#F5F3EE` — warm off-white, not pure white
- **Surface:** `#FFFFFF`
- **Primary text:** `#1C1A17`
- **Secondary text:** `#78716C`

### Accent

- **Brand indigo:** `#5B5BD6` — used for selection rings, buttons, active states, links, the logo. Used sparingly; not splashed everywhere.

### Verdict palette (semantic, not decorative)

| Verdict         | Dark bg   | Dark stroke | Light bg  | Light stroke |
| --------------- | --------- | ----------- | --------- | ------------ |
| SUPPORTED       | `#14532D` | `#22C55E`   | `#F0FDF4` | `#86EFAC`    |
| CONTESTED       | `#713F12` | `#F59E0B`   | `#FFFBEB` | `#FCD34D`    |
| REFUTED         | `#450A0A` | `#EF4444`   | `#FEF2F2` | `#FCA5A5`    |
| REFUTED_CASCADE | `#3B0008` | `#991B1B`   | `#FFF1F2` | `#FCA5A5`    |

Verdict colors are exclusively for claim status. Do not repurpose them for other UI states.

### Node type badge palette

Each logical claim type gets a distinct tint — blue for definitions, green for lemmas, purple for theorems, amber for corollaries. These are background fills on tiny badge chips only; subtle, not loud.

---

## Layout & Density

This is a **data-dense research tool**, not a landing page. Padding is tight (8–16px), not generous (32–64px). White space is used to separate functional regions, not to create breathing room for aesthetics.

Three-column layout in Review/Reader modes: DAG canvas (flex) · Activity feed (280px fixed) · Detail panel (380px fixed, slides in on demand).

The DAG canvas always takes the remaining space. Panels are fixed-width and do not shrink the canvas proportionally — the canvas always stays dominant.

---

## Node visual language

Each DAG node is `176×56px` with `8px` border radius. This is a deliberate small size — nodes are meant to be read at a glance, not read in detail (detail lives in the side panel).

Every node has three layers of information:

1. **Type badge** (top-left): tiny monospace chip — DEF / LEM / THM / COR
2. **Reference number** (top-left, next to badge): Def 1, Lem 2, etc.
3. **Short name** (bottom): human-readable claim name, truncated at ~22 chars

Verdict state is communicated through fill + stroke color, not icons or text labels on the node itself (except a small monospace verdict string top-right, which appears only after resolution).

Processing nodes pulse with a CSS SVG animation on the border. Cascade-refuted nodes glow red with animated dashed edges. No other decorative animations.

---

## Edges

Edges are cubic Bézier curves (SVG `C` path). Control points are at the midpoint Y between source and target, creating smooth S-curves in hierarchical mode.

- Normal edges: `1.5px`, low-opacity, direction indicated by arrowhead only
- Processing edges: `1.5px`, `#3B82F6`, with glow filter
- Cascade edges: `2.5px`, `#EF4444`, animated dashed stroke (`strokeDashoffset` animation), glow filter

The edge layer draws below the node layer. Edges never visually compete with nodes.

---

## Interaction states

- **Hover:** no hover state on nodes (this avoids jitter during DAG animation). The cursor changes to `pointer`.
- **Selected:** a `2px` indigo ring (`#5B5BD6`) around the node, 4px outside the border. The side panel opens.
- **Click to deselect:** clicking the same node again closes the panel.

Side panel slides in with a `fadeUp` animation (`opacity 0→1`, `translateY 12px→0`, 350ms ease). No sliding from the edge — it just appears with a lift.

---

## Surface hierarchy

1. Background (`#0A0C10`) — lowest
2. Sunken surfaces (feed, code areas) — slightly lighter
3. Primary surfaces (panels, header) — `#131720`
4. Elevated elements (tooltips, active badges) — achieved with border + subtle bg tint, never box-shadow at this level

Box shadows are avoided entirely in dark mode. Borders do the work of separation. In light mode, very light shadows (`0 1px 3px rgba(0,0,0,0.1)`) are used only for active tab-style elements.

---

## Iconography

No icon library. Icons are inline SVG drawn ad-hoc. Only the logo and the upload illustration use SVG. All other status indicators are Unicode characters rendered in JetBrains Mono:

- `✓` green — supported / success
- `✗` red — refuted / error
- `⚔` purple — attacker / challenge
- `🛡` blue — defender / rebuttal
- `⟳` gray — orchestrator / running
- `⚙` light gray — verifier / processing
- `⡄` amber — cascade / warning

These appear only in the activity feed and node detail panel, not on the DAG itself.

---

## Mode differentiation

The three modes share the same shell (header, DAG canvas, summary bar) but differ in their right-panel content and DAG overlay. Visual differences:

- **Review Mode:** verdict colors active, activity feed visible, legend shows claim states
- **Reader Mode:** comprehension-status dots on nodes (colored circles bottom-right of each node), legend shows comprehension states, "start here" hint chip top-right of canvas, side panel shows explanation levels + exercises
- **Research Mode:** replaces DAG + feed with a two-column layout (papers/log left, hypothesis panel right). The DAG is hidden — mode completely owns its canvas.

The mode switcher is a segmented control in the header, not tabs. Active segment: filled background + bold text. Inactive: transparent + medium-weight muted text.

---

## What to avoid

- Gradient backgrounds (none anywhere)
- Rounded cards with left-border accent colors
- Large hero typography or decorative display type
- Emoji in UI chrome (only in the mode switcher pills and feed icons as above, where they are semantic)
- Generous padding that makes the layout feel "app-like" or "marketing-like"
- Color for decoration — every color use is functional (verdict, type, status, brand)
