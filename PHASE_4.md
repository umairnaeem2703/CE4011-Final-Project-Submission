# PHASE 4 — Tkinter Desktop MVP Input Workflow

Use this file as Codex context instead of long prompts. Run one subtask at a time. Use 5.5 low + pursue goal unless the task is explicitly backend-heavy.

## Goal

Make the Tkinter desktop MVP student-friendly for:

* general 2D frame/truss/static structures
* 2D shear-frame dynamic examples with story masses and diaphragms

Pipeline rule:

```text
Tkinter UI -> ModelBuilder -> StructuralModel -> existing validator/solver/export
```

Rules:

* No solver math in UI.
* XML remains backend save/load/export.
* Do not create model-type-specific solver paths.
* Use ModelBuilder for UI-created model objects.
* Commit after each subtask.

## Completed

* 4A support + settlement UI
* 4B nodal load + member UDL + member point-load UI
* canvas redraw/template rendering fix
* object tree + inspector basics
* delete elements and safe connected-node blocking
* 4R0 backend property audit
* 4R0b dynamic mass direction audit
* 4R0c UY-only dynamic mass regression test
* 4R1 new model wizard + shear-frame mass UX
* 4R2 mass symbol refinement
* 4R3 material/section manager UI
* 4R4 mass placement UX clarification
* 4R5 effective EA/EI backend support
* 4R6 effective EA/EI UI exposure
* 4R6b section input mode fix + reset-to-default buttons
* 4R6c direct stiffness section material dependency clarified

Do not break these.

## Current Subtask Order

```text
4R7 — Assign Load right-pane redesign
4R8 — Load/support visualization correction
4C0 — ModelBuilder.add_temperature_load helper
4C — Temperature load UI
4D — General mass + diaphragm assignment UI
```

## Common UI Rule

```text
Left pane = command
Right pane = command settings/properties
Canvas = target click / visual feedback
Bottom/status = instruction and validation messages
Object tree = model contents
```

## Read / Modify Limits

Read as needed:

```text
AGENTS.md
src/model_builder.py
src/parser.py
src/element_physics.py
src/ui_desktop/template_dialog.py
src/ui_desktop/canvas.py
src/ui_desktop/property_panel.py
src/ui_desktop/object_tree.py
src/ui_desktop/main_window.py
src/ui_desktop/dialogs.py
```

UI-only modify list:

```text
src/ui_desktop/template_dialog.py
src/ui_desktop/canvas.py
src/ui_desktop/property_panel.py
src/ui_desktop/object_tree.py
src/ui_desktop/main_window.py
src/ui_desktop/dialogs.py
```

Backend modify list only when subtask explicitly says backend:

```text
src/model_builder.py
src/parser.py
src/element_physics.py
tests/...
```

Do not modify controller/solver/math files unless the subtask explicitly requires it and reports why.

---

## 4R7 — Assign Load Right-Pane Redesign

Purpose: make Assign Load workflow clear before adding temperature loads.

Right pane layout:

```text
Target: Node / Member
```

If Target = Member:

```text
Type: Uniformly Distributed Load / Point Load
Coordinate System: Member Local Axis / Global Axis
```

For Uniformly Distributed Load:

```text
wx
wy
```

For Point Load:

```text
Direction: X / Y
Magnitude P
Position along member: relative 0–1 or distance from i-node
```

If Target = Node:

```text
Type: Nodal Load / Nodal Moment
```

For Nodal Load:

```text
Fx
Fy
```

For Nodal Moment:

```text
Mz
```

Rules:

* 2D forces are X/Y only.
* Moment is Mz only.
* Do not add Z force.
* Keep backend load classes unchanged unless current UI cannot call existing builder methods safely.
* Do not add temperature load here.

Validate:

* Assign nodal Fx/Fy.
* Assign nodal Mz.
* Assign member UDL wx/wy.
* Assign member point load.
* Wrong target is blocked clearly.
* Existing tree/inspector still work.

---

## 4R8 — Load/Support Visualization Correction

Purpose: make symbols match direction/sign convention.

Nodal load rules:

```text
+Fx = arrow right
-Fx = arrow left
+Fy = arrow up
-Fy = arrow down
```

Nodal moment rules:

```text
+Mz = counterclockwise curved arrow
-Mz = clockwise curved arrow
```

Member point load rules:

* Draw one arrow at assigned member position.
* Direction follows sign and selected coordinate system.
* Global X/Y: arrow aligned with global axes.
* Local x/y: arrow aligned with member local axes.

Member UDL rules:

* Draw multiple repeated arrows along the member.
* Add a thin line connecting the distributed arrows.
* Direction follows sign and selected coordinate system.
* Global X/Y: arrows aligned with global axes.
* Local x/y: arrows aligned with member local axes.

Support/settlement rules:

* Fixed/pin/roller symbols remain clear.
* Settlement arrows show actual prescribed displacement direction.
* Symbols must not obscure selected node/member labels.

Rules:

* UI/canvas drawing only.
* No load backend changes.
* No solver math.

Validate:

* Positive and negative Fx/Fy arrows are visually correct.
* Positive and negative Mz are visually correct.
* UDL appears as multiple arrows plus a connecting line.
* Existing support, mass, diaphragm, and selection symbols remain visible.

---

## 4C0 — ModelBuilder Temperature Load Helper

Purpose: add small builder bridge before UI temperature load.

Requirements:

* Add `ModelBuilder.add_temperature_load(...)`.
* Inputs: load case id, element id, Tu, Tb.
* Use existing `TemperatureL` backend class.
* Add one focused test.

Rules:

* No UI changes.
* No thermal FEF/math changes.

---

## 4C — Temperature Load UI

Purpose: expose existing temperature load through Assign Load.

Requirements:

* Assign Load -> Target Member -> Type Temperature.
* Fields: Tu, Tb, load case LC1.
* Store through `ModelBuilder.add_temperature_load`.
* Show red `T` marker on member.
* Tree/inspector display temperature load.
* No FEF math in UI.

---

## 4D — General Mass + Diaphragm Assignment UI

Purpose: support arbitrary dynamic models, not only shear frames.

Requirements:

* Assign Mass edits node mass values:

  * `mass_ux`
  * `mass_uy`
  * `mass_rz` / rotational inertia
* Assign Diaphragm creates UX-sharing groups by typed node ids or click collection.
* Tree/inspector/symbol refresh.
* Wrong target is blocked clearly.

Rules:

* Mass assignment is general nodal mass assignment.
* Shear-frame `Mass per floor` is only a template convenience.
* Do not use legacy names `mass_x`, `mass_y`, `rotational_inertia_rz` in UI.

---

## Validation Commands

For UI subtasks:

```bash
python -m py_compile src/ui_desktop/dialogs.py src/ui_desktop/canvas.py src/ui_desktop/property_panel.py src/ui_desktop/main_window.py src/ui_desktop/object_tree.py src/ui_desktop/template_dialog.py
python -m src.ui_desktop.app
```

For backend subtasks:

```bash
pytest tests/ -q
```

Run full suite only after backend changes or at phase completion.

## Expected Codex Output

```text
Changed files:
- ...

Summary:
- <=8 bullets

Validation:
- commands/tests/manual smoke

TODOs:
- unavoidable only
```

## Abort

Stop and report if:

* more than 5 files need modification
* solver math must move into UI
* EA/EI support requires broad refactor
* temperature load requires solver changes
* more than 3 revision prompts are needed
