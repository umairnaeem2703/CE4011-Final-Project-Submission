# PHASE_6_UI_POLISH.md — Final UI/UX Polish

## Goal

Polish the Tkinter desktop MVP before documentation and final submission.

Final submitted scope:

- Static Analysis
- Modal Analysis

RSA and THA are deferred/future work and must not appear in the final desktop UI.

## Rules

- Cosmetic and ergonomic polish only.
- Do not change solver math.
- Do not change XML schema.
- Do not add RSA/THA UI.
- Do not touch `controller.py` unless tests clearly prove there is no safe alternative.
- Preserve current flat `src/` layout.
- Keep changes small and localized.
- Prefer fewer than 5 changed files per Codex pass.
- If a task becomes too large, stop and split it.
- Preserve the current architecture: UI collects input, validates, calls the engine, and displays results. No solver math in UI.
- Preserve existing plotting/sign conventions.

## Theme

- Primary: dark blue
- Accent: orange
- Background: white
- Neutral: light gray / dark gray
- Style: clean educational engineering desktop tool

## Current State

Static and Modal analysis remain the final submitted desktop scope. The result windows now use tabbed layouts with localized export actions, the bottom status bar refreshes after model imports/edits, the canvas supports mouse-wheel zoom and middle-button pan, and the right property pane is adjustable. Plot/canvas styling has been polished for readability without changing solver behavior. The only remaining test failure is the unrelated missing SAP2000 benchmark file, which is outside this UI pass.

## Task Status

| Task | Status | One-line Result |
|---|---|---|
| 6A Command organization | DONE | Reorganized the desktop menus into Model, Edit, Assign, View, Analyze, Results, and Help with Static/Modal only. |
| 6B Help menu | DONE | Added Quick Start, safe User Manual handling, and About dialogs. |
| 6C Status bar and workflow hints | DONE | Added a live summary bar with model counts, result state, and units, plus clearer workflow messages. |
| 6D Tooltips | DONE | Added localized tooltips for key engineering fields and member type selection. |
| 6E Empty-state messages | DONE | Added explicit no-model, no-static, no-modal, and no-selection messages. |
| 6F Result-window layout polish | DONE | Reworked Static and Modal result windows into tabbed layouts with tab-specific summary, DOF map, matrix, table, member-force, and plot sections. |
| 6G Export button placement | DONE | Moved export actions into the result window action bar with the requested `Export Table TXT`, `Export Table CSV`, and `Export Plot PNG` labels. |
| 6H Plot sizing/readability | DONE | Increased default figure/window sizing, updated plot titles/labels, and added tighter margins for the static and modal visualizers. |
| 6I Canvas visual polish | DONE | Applied the Phase 6 white/gray/blue/orange canvas theme with clearer labels, subtler symbols, and stronger selected-node emphasis. |
| 6J Final UI smoke audit | DONE | Verified desktop launch paths and focused desktop/visualizer tests; the only remaining failure is the unrelated missing SAP2000 benchmark file. |

---

## 6A Command Organization

Use this top-level organization:

```text
Model | Edit | Assign | View | Analyze | Results | Help
```

### Model

- New Model
- Open XML, if already safely wired
- Save XML
- Export XML

### Edit

- Select/Inspect
- Delete
- Replicate

### Assign

- Materials/Sections
- Supports
- Loads
- Masses
- Diaphragm

### View

- Grid
- Snap
- Local Axes
- Zoom In
- Zoom Out
- Full View

### Analyze

- Validate Model
- Run Static Analysis
- Run Modal Analysis

### Results

- Static Results
- Modal Results

### Help

- Quick Start
- User Manual
- About

Remove or hide dead/disabled placeholder menu items if they are user-facing and not needed for final submission.

Do not expose RSA or THA in the final desktop UI.

---

## 6B Help Menu

Add or clean the Help menu.

### Quick Start

Quick Start should open a read-only dialog with this workflow:

1. Create a Blank Model or 2D Shear Frame Template.
2. Draw or inspect nodes and members.
3. Assign materials, sections, supports, loads, and masses.
4. Click Validate Model.
5. Run Static Analysis or Modal Analysis.
6. Open Static Results or Modal Results.
7. Export visible tables as TXT/CSV and plots as PNG.

### User Manual

User Manual should behave safely:

- If a user manual file already exists, open it or show its path.
- If it does not exist yet, show:

```text
User manual will be provided with the final documentation package.
```

- Do not crash if the file is missing.

### About

About should show:

- CE 4011 Structural Analysis Suite
- Static + Modal Educational Solver
- Tkinter desktop MVP
- Developed by Mohammad Umair Naeem
- Final scope: Static Analysis and Modal Analysis

---

## 6C Status Bar and Workflow Hints

Improve the bottom status bar to show useful model/result state:

```text
Model: <name> | Nodes: <n> | Members: <m> | Static: missing/current/stale | Modal: missing/current/stale | Units: <unit_system>
```

If exact stale/current tracking already exists, reuse it.

If not, implement minimally and safely using existing state variables.

When the model is edited, previous Static and Modal results should be cleared or marked stale according to the existing architecture decision.

Use clear workflow messages:

- “Model changed. Previous Static/Modal results were cleared.”
- “No model is open. Create a Blank Model or choose a template to begin.”
- “Run Static Analysis before opening Static Results.”
- “Run Modal Analysis before opening Modal Results.”
- “Validation passed. Model is ready for analysis.”
- “Validation failed. Review supports, members, materials, sections, loads, and masses.”

---

## 6D Tooltips

Add lightweight tooltips for confusing engineering/UI fields if a tooltip helper exists or can be implemented simply.

Suggested tooltip text:

- UX: “Global horizontal displacement DOF.”
- UY: “Global vertical displacement DOF.”
- RZ: “Out-of-plane rotational DOF.”
- Frame: “Axial + bending stiffness member.”
- Truss: “Axial stiffness only.”
- Mass UX: “Translational mass active in global X direction.”
- Mass UY: “Translational mass active in global Y direction.”
- Rigid floor diaphragm: “Couples selected nodes in horizontal UX direction.”
- Direct EA/EI: “Uses direct stiffness values instead of deriving stiffness from E, A, and I.”
- Thermal depth d: “Used only for temperature-gradient loads.”
- Run Modal Analysis: “Solves Kφ = λMφ using active dynamic DOFs.”
- Static Results: “Open displacements, reactions, member forces, matrices, and N/V/M plots.”
- Modal Results: “Open frequencies, periods, mode shapes, participation factors, and mass ratios.”

If adding tooltips everywhere is too large, add them only to command buttons and the most confusing inspector fields.

---

## 6E Empty-State Messages

Add clear empty-state messages instead of blank windows or confusing disabled panels.

### No model

```text
No model is open. Create a Blank Model or choose a 2D Shear Frame Template to begin.
```

### No static result

```text
No Static result is available. Run Analyze → Run Static Analysis first.
```

### No modal result

```text
No Modal result is available. Assign masses, validate the model, then run Analyze → Run Modal Analysis.
```

### No selected object

```text
Select a node or member to inspect and edit its properties.
```

---

## 6F Result-Window Layout Polish

Do not change result computation.

### Static Results window

Use clear tabs/sections where practical:

- Summary
- DOF Map
- Matrices
- Displacements
- Reactions
- Member Forces
- Plots

Plots section should expose:

- Deformed Shape
- Axial N
- Shear V
- Moment M

### Modal Results window

Use clear tabs/sections where practical:

- Summary
- DOF Map
- Matrices
- Modal Table
- Mode Shapes

Modal table should preserve these educational fields if available:

- Mode
- λ = ω²
- ω
- f
- T
- Modal Mass
- Participation Factor Γ
- Effective Modal Mass
- Mass Participation %

If optional fields are missing, display “—” instead of crashing.

---

## 6G Export Button Placement

Place export actions inside result windows because they depend on the current table or plot:

- Export Table TXT
- Export Table CSV
- Export Plot PNG

If export already exists, improve placement/labels only.

If export does not exist, implement minimally using existing table/plot data and standard library file dialogs where safe.

Do not create a separate global export menu for result-specific exports.

---

## 6H Plot Sizing and Readability

Do not change plotting math, sign conventions, or solver output.

Only improve:

- default plot window size, preferably around 900 x 650 if practical
- plot titles
- axis labels
- margins to avoid clipped labels
- scale annotation where already available
- readable mode/deformed-shape titles

Suggested titles:

- Static Deformed Shape
- Axial Force Diagram
- Shear Force Diagram
- Bending Moment Diagram
- Mode Shape 1 - f = <value> Hz, T = <value> s

Preserve the hybrid plotting decision:

- Tkinter Canvas may remain for interactive member-level visualization.
- Matplotlib should remain for complete N/V/M diagrams, deformed shapes, mode shapes, and report-quality PNG export.

---

## 6I Canvas Visual Polish

Keep this limited and safe.

Apply the theme consistently:

- white canvas background
- light gray grid
- dark blue members
- orange selection highlight
- readable node/member labels
- compact support/load/mass/diaphragm symbols
- selected nodes slightly more visible than unselected nodes

Do not redesign the canvas engine.

Do not change coordinate transforms.

Do not change selection behavior.

Do not change drawing/editing logic except for colors, labels, and visual clarity.

---

## 6J Final UI Smoke Audit

Run:

```bash
python -m py_compile <modified_python_files>
```

Run focused UI tests if present.

Run:

```bash
pytest tests/test_ui_desktop_static.py
```

or the closest relevant UI test file if present.

Manual smoke test:

- Desktop app launches.
- Blank Model is available.
- 2D Shear Frame Template is available.
- Command organization is clean.
- Help → Quick Start opens.
- Help → User Manual does not crash if manual is missing.
- Help → About opens.
- Tooltips appear on at least main commands or key fields.
- Static Results empty state works when no static result exists.
- Modal Results empty state works when no modal result exists.
- Static Results still opens after running static analysis.
- Modal Results still opens after running modal analysis.
- Plot windows are readable.
- Canvas selection/editing still works.
- RSA/THA are not visible in the final desktop UI.

---

## Update Rule

After each Codex pass, update only:

1. task status from TODO to DONE or PARTIAL,
2. one-line result,
3. this Current State section in 1–3 sentences.

Do not paste long logs into this file.

---

## Recommended Pass Split

### Pass 1

Implement:

- 6A Command organization
- 6B Help menu
- 6C Status bar and workflow hints
- 6D Tooltips
- 6E Empty-state messages

### Pass 2

Implement:

- 6F Result-window layout polish
- 6G Export button placement
- 6H Plot sizing/readability
- 6I Canvas visual polish
- 6J Final UI smoke audit
