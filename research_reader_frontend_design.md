# Research Reader Frontend Design

## Product Frame

The research reader should feel like a technical workbench, not a casual article viewer. The core job is to help a user move from "this paper is dense" to "I understand the dependency structure of its ideas."

Primary mental model:

```text
Paper text -> extracted principles/claims -> dependency graph -> explanations, proofs, exercises, annotations
```

The interface should support three simultaneous activities:

1. Reading the source text.
2. Understanding the conceptual structure.
3. Tracking personal comprehension.

## Overall Layout

Use a three-pane layout optimized for wide screens, with responsive fallbacks.

```text
+--------------------------------------------------------------+
| Top Nav: Paper title | mode selector | search | progress     |
+---------------+------------------------------+---------------+
| Left Rail     | Main Document Viewer          | Right Panel   |
| Outline       | Source text / highlights      | Concept info  |
| Concept graph | Equations / figures           | Summary/proof |
| Progress      | Inline annotations            | Exercises     |
+---------------+------------------------------+---------------+
```

Top navigation should include:

- Paper title and metadata.
- Mode switch: `Reader`, `Review`, `PoC`, `Research`.
- Search across text, equations, claims, and references.
- Reading progress: atoms visited, understood, flagged.
- Export study guide button.

Left rail should include:

- Document outline.
- Concept dependency graph mini-map.
- "Start here" recommendations.
- Filters: definitions, theorems, assumptions, methods, limitations.

Main area should be the source-grounded document viewer.

Right panel should change based on selected text, claim, equation, or concept.

## Core Components

### Document Viewer

Purpose: preserve trust by keeping explanations anchored to the original source.

Features:

- Render paper sections in order.
- Highlight extracted principles, claims, definitions, assumptions, equations, and citations.
- Support synced scrolling with outline and graph.
- Inline badges for atom type: `Definition`, `Lemma`, `Theorem`, `Assumption`, `Technique`.
- Hovering a highlight previews a short explanation.
- Clicking a highlight opens full detail in the right panel.

Design choice: the source text remains the center of gravity. Technical users want to verify every abstraction against the original wording.

### Concept / Claim Panel

Appears in the right pane when a highlighted atom is selected.

Sections:

- Plain-language summary.
- Formal statement.
- Why it matters.
- Dependencies.
- Downstream consequences.
- Source quote.
- Related equations.
- Related citations.
- User notes.
- Exercises or checks.

Suggested tabs:

```text
Summary | Details | Proof | Dependencies | Exercises | Notes
```

### Concept Graph

A dependency graph should show how ideas support each other.

Node types:

- Definition
- Assumption
- Lemma
- Theorem
- Method
- Experiment
- Limitation
- Open problem

Edge types:

- depends on
- proves
- motivates
- contradicts
- generalizes
- uses notation from
- cites evidence from

Important convention:

```text
Current concept -> depends on -> prerequisite concept
```

Visual encoding:

- Definitions: blue.
- Assumptions: amber.
- Theorems/results: green.
- Limitations/risks: red.
- Techniques/methods: purple or slate.
- User-understood nodes: filled or checked.
- Unvisited nodes: muted outline.

### Summaries Panel

A collapsible panel for navigating abstraction levels.

Levels:

1. One-sentence gist.
2. Paragraph explanation.
3. Technical summary.
4. Formal statement.
5. Proof / derivation.
6. Source quote.

This should not be a separate page. It should sit beside the document so the user can compare generated explanation with source text.

### Annotation Panel

User annotations should be attached to:

- Text spans.
- Atoms/claims.
- Equations.
- Graph nodes.
- Citations.

Annotation types:

- Note.
- Question.
- Confusion.
- Important.
- Suspected flaw.
- Follow up.
- Understood.

Each annotation should optionally have visibility:

```text
private | shared with team | included in study guide
```

## Content Decomposition

The backend should decompose research content into "principles" or "atoms."

Recommended atom categories:

- Core definitions.
- Assumptions.
- Problem setup.
- Notation.
- Lemmas.
- Theorems.
- Proof steps.
- Algorithms.
- Experimental claims.
- Limitations.
- Open questions.
- Citations that support claims.

Each atom should contain:

```text
id
type
source span
formal text
plain explanation
section
dependencies
related equations
related citations
importance
user comprehension status
```

Importance levels:

```text
low | medium | high | core
```

This allows the frontend to recommend a reading path instead of forcing linear reading.

## Interaction Flow: Expanding Concepts

Default state:

- Document shows compact highlights.
- Graph shows top-level concepts only.
- Right panel says "Select a concept."

On click:

1. Highlight becomes active.
2. Right panel opens summary.
3. Graph centers selected node.
4. Dependencies are emphasized.
5. Source span scrolls into view if selected from graph.

Expanded concept view:

```text
[Theorem 3.1]
Short summary
Formal statement
Depends on: Definition 2.1, Lemma 2.4
Used by: Corollary 3.2, Main Result
Status: In progress
```

Collapse behavior:

- Collapse details but keep active highlight.
- Preserve scroll position.
- Keep user notes saved.

## Interaction Flow: Dependencies

When viewing a concept:

- Direct prerequisites are shown above or to the left.
- Dependents are shown below or to the right.
- Hovering an edge explains the relationship.
- Clicking a dependency navigates to that atom.

Useful graph controls:

```text
Show prerequisites only
Show downstream impact
Show local neighborhood
Show full graph
Hide low-importance nodes
```

A "Why do I need this?" button should explain why a prerequisite matters for the selected claim.

## Interaction Flow: Highlighting and Annotating

User selects text in the document.

Floating toolbar appears:

```text
Add note | Ask | Mark confusing | Link to concept | Highlight
```

If selected text overlaps an existing atom:

- Offer to attach note to that atom.
- Show existing generated explanation.

If selected text is not part of an atom:

- Allow manual annotation.
- Optional: "Create concept from selection."

Annotation UX:

- Notes appear as small margin markers.
- Clicking marker opens thread in right panel.
- Confusion markers can feed a "review later" queue.

## Interaction Flow: Abstraction Levels

Provide a persistent abstraction control in the right panel:

```text
Gist | Intuition | Technical | Formal | Proof
```

Behavior:

- `Gist`: one sentence, minimal notation.
- `Intuition`: explains motivation and analogy.
- `Technical`: assumes undergraduate/graduate background.
- `Formal`: exact theorem/definition structure.
- `Proof`: step-by-step derivation with dependencies.

For mathematical material, proof view should show:

```text
Goal
Assumptions
Known lemmas used
Step-by-step argument
Where each step appears in source
Open gaps or unclear steps
```

Do not replace source text. Always link generated explanations back to source spans.

## Visual Design

Use a restrained technical palette.

Suggested colors:

```text
Background: #0f1320 or #f8fafc depending theme
Text: high contrast neutral
Definitions: blue
Assumptions: amber
Results: green
Warnings/flaws: red
User notes: violet
Current selection: cyan outline
```

Typography:

- Source text: serif or highly readable academic font.
- UI labels: clean sans-serif.
- Equations: preserve TeX formatting.
- Code/math identifiers: monospace.
- Avoid tiny dense controls; use compact but legible spacing.

Spacing:

- Main document max width around `760-900px`.
- Right panel width around `360-480px`.
- Left rail around `280-360px`.
- Use generous line height for dense math text.
- Keep graph nodes compact but not cramped.

Emphasis:

- Use color for type, not decoration.
- Use borders and subtle backgrounds for active states.
- Avoid heavy cards everywhere; reserve cards for repeated concepts and annotations.

## State Management

Track state at several levels.

Session state:

```text
selectedPaper
selectedAtom
activeMode
activeAbstractionLevel
currentSection
searchQuery
graphFilters
```

Reading progress:

```text
visitedAtoms
understoodAtoms
flaggedAtoms
inProgressAtoms
startHereAtoms
lastReadPosition
```

UI state:

```text
expandedSections
openedGraphNodes
rightPanelTab
collapsedPanels
hoveredAtom
activeHighlight
```

User-generated state:

```text
annotations
manualHighlights
questions
exerciseAnswers
studyGuideSelections
```

Generated content cache:

```text
atom explanations by level
prerequisites
glossary
exercises
tutor history
dependency graph
```

Important: cache explanations per abstraction level so switching levels does not repeatedly refetch unless stale.

## Long Documents and Performance

Dense papers can be hundreds of pages or thousands of equations, so the frontend should avoid rendering everything eagerly.

Use:

- Virtualized document rendering by section.
- Lazy-load atom annotations on click.
- Lazy-render graph neighborhoods.
- Cache visited atom panels.
- Debounced search.
- Web workers for client-side search/highlight indexing.
- Progressive loading: outline first, then graph, then annotations.
- Skeleton states for right panel content.
- Chunked rendering for equations and references.

For graph performance:

- Default to local neighborhood, not full graph.
- Use clustering by section.
- Collapse low-importance nodes.
- Provide mini-map only after graph stabilizes.

## Accessibility

The interface should be fully keyboard-navigable.

Required support:

- `Tab` through highlights and controls.
- Arrow keys move between concepts.
- Enter opens selected concept.
- Escape closes popovers.
- Search results navigable by keyboard.
- Graph has list/tree alternative.
- Color is never the only status indicator.
- Use icons plus labels for atom types.
- High contrast mode.
- Adjustable text size.
- Screen-reader labels for highlights:
  "Theorem, high importance, in progress, selected."
- Reduced motion option for graph transitions.

For mathematical content:

- Equations should have accessible TeX source or alt text.
- Copy equation as LaTeX.
- Allow "explain this symbol" interaction.

## Optimized Workflow for Technical Users

The ideal reader flow:

1. User opens paper.
2. System builds concept graph and recommends `Start here`.
3. User clicks first core definition.
4. Right panel shows intuition, formal statement, dependencies.
5. User expands proof-level detail when needed.
6. User jumps through prerequisites using graph.
7. User marks atoms as understood or flagged.
8. User annotates confusing source spans.
9. Exercises test understanding.
10. Study guide exports only visited/important concepts.

The key design principle: never hide the original paper, but make its conceptual structure visible and navigable.
