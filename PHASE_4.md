# PHASE 4

Use this file as Codex context instead of a long prompt. Run subtasks one by one. Use 5.5 low + pursue goal unless a subtask fails twice.

## Phase Goal

Expose assignment features in the Tkinter desktop MVP:

- supports + support settlements
- nodal loads
- member UDLs
- member point loads
- member temperature loads
- lumped nodal masses
- diaphragm groups

Architecture:

```text
Tkinter UI -> ModelBuilder -> StructuralModel -> existing validator/solver/export
```

No solver math in UI. XML remains backend save/load/export. Keep solvers generalized.

## Current UI Assumptions

Before starting:

- `python -m src.ui_desktop.app` launches.
- Left commands exist: Select / Inspect, Draw Node, Draw Member, Assign Support, Assign Load, Assign Mass, Assign Diaphragm, Delete.
- Right panel is context-sensitive.
- Object tree exists.
- Canvas has working `redraw_model()`.
- Shear frame templates render correctly.
- Delete works for elements and blocks connected node deletion safely.

Do not break these.

## Read / Modify Limits

Read only:

```text
AGENTS.md
src/model_builder.py
src/parser.py
src/ui_desktop/main_window.py
src/ui_desktop/canvas.py
src/ui_desktop/property_panel.py
src/ui_desktop/object_tree.py
```

Modify only:

```text
src/ui_desktop/dialogs.py
src/ui_desktop/main_window.py
src/ui_desktop/canvas.py
src/ui_desktop/property_panel.py
src/ui_desktop/object_tree.py
```

Only modify `src/model_builder.py` if a tiny wrapper is truly missing and backend dataclasses/export already support the feature. Stop and report before doing so. Do not modify parser/controller/solver/math files.

## UI Rule

```text
Left = command
Right = settings/properties
Canvas = target click
Bottom = instruction/status
Object tree = model contents
```

Use one `Assign Load` command. Do not add separate left tools for every load type.

## Assignment Workflows

### Support + Settlement

Right panel fields:

```text
support type: fixed / pin / roller_x / roller_y / custom
custom restraints: ux, uy, rz
settlement/prescribed displacement: ux, uy, rz
```

Behavior:

- User chooses settings, then clicks node.
- Use `ModelBuilder.add_support` or existing compatible path.
- Store settlements if backend supports them.
- Redraw support symbol and settlement marker.
- Refresh tree and inspector.

Stop if settlement exists in parser/export but not ModelBuilder and no safe wrapper exists.

### Unified Load

Right panel fields:

```text
target: Node / Member
type:
  Node -> Nodal Force/Moment
  Member -> UDL / Point Load / Temperature Load
load case: LC1
```

Node load:

```text
Fx, Fy, Mz
use ModelBuilder.add_nodal_load
```

Member UDL:

```text
wx, wy, coordinate convention if supported, fef_condition if required
use ModelBuilder.add_member_udl
```

Member point load:

```text
P/components, distance or ratio a/L, direction if supported, fef_condition if required
use ModelBuilder.add_member_point_load
```

Temperature load:

```text
Tu, Tb
or DeltaT_uniform / DeltaT_gradient if backend expects that
load case: LC1
```

Use existing backend thermal support. Do not compute thermal FEF in UI. Add only a tiny `ModelBuilder.add_temperature_load` wrapper if backend already has `TemperatureL` and export support.

### Mass

Right panel fields should match backend:

```text
mass_x, mass_y, rotational_inertia_rz
```

Fallback:

```text
mass, direction: x / y / both
```

Behavior:

- User clicks node.
- Use `ModelBuilder.add_lumped_mass`.
- Redraw mass as small red square.
- Refresh tree and inspector.

### Diaphragm

Right panel/dialog:

```text
group id
node ids or click-to-select nodes
Apply / Clear
```

Behavior:

- Use `ModelBuilder.add_diaphragm_group`.
- Redraw simple diaphragm tag/marker.
- Refresh tree and inspector.

MVP may accept comma-separated node ids.

## Object Tree

Groups:

```text
Nodes
Elements
Supports
Loads
Masses
Diaphragms
```

Loads may be grouped as:

```text
LC1 / Nodal
LC1 / UDL
LC1 / Point
LC1 / Temperature
```

Refresh tree after every assignment. Tree click should select node/member or log load/support/mass details.

## Inspector

Node inspector should show:

```text
id, x, y
support + settlement
nodal loads
mass
diaphragm group
```

Member inspector should show:

```text
id, type, node i, node j, material, section
UDL / point / temperature loads
```

## Canvas Symbols

Keep simple:

```text
supports: fixed/pin/roller/custom
settlement: Δ marker
nodal load: arrow
UDL: repeated small arrows
member point load: single arrow
temperature:  red T marker
mass: small red square
diaphragm: label/dashed marker
```

Robustness matters more than style.

## Error Handling

Wrong target:

```text
Assign Support on member -> "click a node"
Nodal Load on member -> "click a node"
Member Load on node -> "click a member"
Mass on member -> "click a node"
```

Invalid numeric input: show status and do not mutate model.

Unsupported backend feature: disable visibly or stop and report exact missing method/signature.

## Subtasks

### Task 4A — Support + Settlement

Modify:

```text
property_panel.py
canvas.py
object_tree.py
main_window.py
```

Implement:

- support assignment by node click
- settlement fields
- support/settlement symbols
- tree refresh
- inspector details

Validate:

- assign fixed support
- assign settlement
- inspect node
- tree updates
- Draw/Delete still work

### Task 4B — Nodal Load + Member UDL + Member Point Load

Modify:

```text
property_panel.py
canvas.py
object_tree.py
main_window.py
dialogs.py if needed
```

Implement:

- unified Assign Load panel
- nodal load
- member UDL
- member point load
- symbols/tree/inspector
- wrong-target blocking

Validate:

- nodal load on node
- UDL on member
- point load on member
- wrong targets blocked
- redraw preserves symbols

### Task 4C — Temperature Load

Modify:

```text
property_panel.py
canvas.py
object_tree.py
main_window.py
dialogs.py if needed
```

Maybe modify:

```text
model_builder.py
```

only for tiny wrapper if backend support already exists.

Implement:

- temperature option in Assign Load
- store via backend
- T marker on member
- tree/inspector display

Validate:

- assign temperature load to frame member
- confirm it appears in model/load case
- XML export works if already supported
- no thermal FEF math in UI

### Task 4D — Mass + Diaphragm

Modify:

```text
property_panel.py
canvas.py
object_tree.py
main_window.py
dialogs.py if needed
```

Implement:

- mass assignment
- diaphragm assignment
- symbols/tree/inspector
- wrong-target blocking

Validate:

- mass on node
- diaphragm group on floor nodes
- redraw preserves symbols
- Draw/Delete still work

## Validation Commands

Run after each subtask:

```bash
python -c "from src.ui_desktop.dialogs import SupportDialog; print('dialogs ok')"
python -c "from src.ui_desktop.canvas import ModelCanvas; print('canvas ok')"
python -c "from src.ui_desktop.property_panel import PropertyPanel; print('panel ok')"
python -c "from src.ui_desktop.main_window import MainWindow; print('main ok')"
python -c "from src.ui_desktop.object_tree import ObjectTreePanel; print('tree ok')"
python -m py_compile src/ui_desktop/dialogs.py src/ui_desktop/canvas.py src/ui_desktop/property_panel.py src/ui_desktop/main_window.py src/ui_desktop/object_tree.py
```

Run relevant tests. Full suite only for phase completion or backend changes:

```bash
pytest tests/ -q
```

Manual smoke:

```bash
python -m src.ui_desktop.app
```

Check:

```text
New -> 2D Shear Frame
assign support + settlement
assign nodal load
assign UDL
assign point load
assign temperature load
assign mass
assign diaphragm
symbols appear
tree updates
Select / Inspect shows details
Draw Node / Draw Member / Delete still work
Save XML/export works if existing button supports it
```

## Expected Codex Output

```text
Changed files:
- ...

Summary:
- <=8 bullets

Validation:
- imports
- compile
- tests/smoke

Implemented:
- list done features

Placeholders/TODO:
- only unavoidable items
```

## Abort

Stop and report if:

- ModelBuilder signature is unclear.
- settlement backend path is unclear.
- temperature backend path is unclear.
- feature requires solver changes.
- more than 5 files need modification.
- more than 3 revision prompts are needed.
