# Phase 5 Desktop Analysis + Results Integration

> Working name: **Phase 5D**. This is the desktop UI analysis/results phase, not the earlier backend THA phase.

## Current Context

Architecture/UI cleanup is considered complete enough to move on.

Completed context from previous architecture tasks:
- Rigid-link behavior is clarified.
- Flexurally rigid backend implementation is deferred.
- Local/global member loads and local-axis display are implemented.
- Diaphragm assignment is now selection-based.
- Edit tools such as Select/Inspect, Delete, and Replicate belong in the Edit tab.
- Next direction is **analysis integration and results**.

Target workflow for this phase:

```text
analysis integration/results
-> run analysis from desktop UI
-> result selection
-> deformed shape / NVM / mode / RSA / THA plots
-> result tables
-> export/report polish
```

## Non-Negotiable Rules

Read this file before every Phase 5D Codex task.

Also read, only as needed:
- `AGENTS.md`
- `README.md`
- `ARCHITECTURE.md`
- `MATH_SPEC.md`
- relevant files in `src/ui_desktop/`
- relevant solver/result/visualizer files only for the current task

Rules:
1. Keep the current flat `src/` layout unless explicitly told otherwise.
2. Do not move solver math into UI files.
3. UI must call existing controller/solver functions and consume result objects.
4. Do not duplicate Static/Modal/RSA/THA logic by model type.
5. Do not create separate shear-frame-only analysis paths.
6. Preserve existing UI modeling behavior, selection, delete, replicate, diaphragm, local/global load display, XML save/load, and tests.
7. Keep each task small: usually fewer than 5 modified files.
8. Run relevant tests/checks only unless the user asks for the full suite.
9. Every completed Codex task must update this file before reporting completion.

## Required Completion Update — Token-Controlled

At the end of every task, Codex must edit this file, but **must compress the completed task** so future prompts stay small.

Required update steps:

1. Mark the task as `DONE` in **Phase 5D Task Board**.
2. Update **Current Phase State** with only the latest usable behavior. Keep this section short.
3. Add or update one compressed entry in **Condensed Completion Log** using the required one-block format below.
4. Replace the completed task's verbose subsection under **Implementation Strategy** with a compact `DONE SUMMARY` block of no more than 5 bullets.
5. Keep only the current/next unfinished task instructions detailed. Completed tasks must not keep long instructions, long logs, or pasted terminal output.

Required compressed log format:

```markdown
### 5D# — DONE — YYYY-MM-DD
- Files: `file1.py`, `file2.py`
- Result: one sentence describing the behavior now available.
- Checks: `check command`, manual smoke check summary.
- Next/limits: one sentence only.
```

Hard limits for every completion update:
- Completion log entry: max 4 bullets.
- DONE SUMMARY block: max 5 bullets.
- Current Phase State: max 10 bullets total.
- Do not paste traceback/log output unless it is a remaining blocker.
- Do not keep obsolete detailed instructions for completed tasks.

Do not skip this update.

## Current Phase State

- Desktop Analyze tab now has `Run Static Analysis`, calling existing `run_static_analysis(model_canvas.builder.model)`.
- Latest static result/error state is cached on `DesktopMainWindow` as `latest_static_results` / `static_analysis_error`.
- UI reports static success/failure through the existing status log without adding solver math or result tables.
- Desktop entry point supports `python -m src.ui_desktop.app` with the repo's flat `src` imports.
- Next implementation target is 5D2: add a static result selector and read-only basic tables from cached `StaticResults`.

## Codex Reading Budget

To avoid token exhaustion, Codex should read this file selectively:

1. Always read: **Current Context**, **Non-Negotiable Rules**, **Required Completion Update — Token-Controlled**, **Current Phase State**, **Phase 5D Task Board**, and the current task subsection only.
2. Do not reread detailed instructions for tasks already marked `DONE`. Their compressed `DONE SUMMARY` and **Condensed Completion Log** are the source of truth.
3. Before starting a task, if previous tasks are still verbose even though marked `DONE`, first compress them according to the required format.
4. Keep future edits to this file concise. This file is a rolling state file, not a full development diary.


## Phase 5D Task Board

| ID | Task | Status | Scope |
|---|---|---:|---|
| 5D0 | Audit desktop analysis integration entry points | DONE | docs only |
| 5D1 | Add desktop analysis bridge + Run Static | DONE | UI/controller bridge only |
| 5D2 | Add static result selector + basic tables | TODO | UI result browsing |
| 5D3 | Embed static plots: deformed shape + N/V/M | TODO | visualization integration |
| 5D4 | Add Run Modal + modal tables + mode plot | TODO | modal result integration |
| 5D5 | Add Run RSA + RSA result tables/plots | TODO | RSA result integration |
| 5D6 | Add Run THA + ground motion controls + histories | TODO | THA result integration |
| 5D7 | Add export/report polish for visible results | TODO | export/report only |
| 5D8 | Final Phase 5D audit and smoke-test checklist | TODO | verification/docs |

## Implementation Strategy

### 5D1 — Analysis bridge + Run Static

DONE SUMMARY:
- Added `Run Static Analysis` action in the desktop Analyze tab.
- Calls existing `ui.static_analysis.run_static_analysis` on the current `model_canvas.builder.model`.
- Caches success/failure state on `DesktopMainWindow`.
- Reports concise status messages through the existing desktop log.
- No result tables, plotting, Modal, RSA, or THA integration included.

### 5D2 — Static result selector + basic tables

Goal:
- Let the user inspect static results after running Static.

Expected behavior:
- A results area/panel shows available result categories when static results exist.
- Basic categories: displacements, reactions, element forces, and optionally matrices/intermediate data.
- Tables are read-only and regenerated from the stored result object.
- Empty state says to run analysis first.

Avoid:
- Do not add plots yet.
- Do not change static solver result format unless a tiny adapter is necessary.

Minimum checks:
- Static result categories appear after Run Static.
- Selecting each category updates the table.
- Missing/empty results do not crash the UI.

### 5D3 — Static plots: deformed shape + N/V/M

Goal:
- Embed existing visualizer plots in desktop UI for static results.

Expected behavior:
- Deformed shape plot can be displayed from `StaticResults`.
- N/V/M plot can be displayed for selected element or available model data.
- Matplotlib/Tk embedding is contained in UI visualization helpers.
- Plotting consumes model + result objects only.

Avoid:
- Do not rewrite `visualizer.py` unless only adapting API mismatches.
- Do not move plotting math into the property panel or canvas.

Minimum checks:
- Run Static.
- Display deformed shape.
- Display one N/V/M diagram.
- Switching result views does not break canvas/model editing.

### 5D4 — Modal integration

Goal:
- Add desktop UI access to modal analysis and basic modal results.

Expected behavior:
- User can run Modal analysis from desktop UI.
- Modal result object is stored in result state.
- User can inspect frequencies, periods, modal mass, participation factors, and effective mass.
- User can display a selected mode shape plot.
- Static result UI remains unaffected.

Avoid:
- Do not require ground motion for Modal analysis.
- Do not add RSA/THA settings yet.

Minimum checks:
- Generate shear frame with masses.
- Run Modal.
- Frequencies/periods table appears.
- Mode shape plot appears for selected mode.
- Running Modal on a massless model gives a clear error, not a crash.

### 5D5 — RSA integration

Goal:
- Add desktop UI access to existing RSA workflow.

Expected behavior:
- User can run RSA if modal/dynamic data and spectrum settings are available.
- UI exposes only minimal required settings at first.
- RSA result object is stored in result state.
- User can inspect spectrum/modal/combined response summaries.
- RSA plots are available if supported by existing visualizer.

Avoid:
- Do not invent a full building-code spectrum designer if one does not already exist.
- Do not block Static/Modal workflows with RSA settings.

Minimum checks:
- Run RSA on an example that already works in tests/scripts.
- Display basic RSA summary table.
- Display spectrum or combined response plot if available.

### 5D6 — THA integration

Goal:
- Add desktop UI access to existing Newmark/ground-motion THA workflow.

Expected behavior:
- THA controls ask for ground motion only in THA workflow.
- User can select/enter ground motion settings supported by existing backend.
- THA result object is stored in result state.
- User can inspect peak displacement/base shear/OTM summary.
- User can plot displacement/velocity/acceleration histories and base response histories where available.

Avoid:
- Do not make ground motion mandatory for Static or Modal.
- Do not rewrite the Newmark solver.

Minimum checks:
- Run THA with `data/ground_motion.txt` or existing ground-motion sample.
- Display at least one response history plot.
- Invalid/missing ground motion gives a clear error.

### 5D7 — Export/report polish

Goal:
- Export visible results and plots for final deliverables.

Expected behavior:
- Export selected result table to CSV/TXT or copyable text.
- Save current plot to PNG if plot is visible.
- Optional: generate simple analysis summary report from latest results.

Avoid:
- Do not build a complex report generator.
- Do not add heavy dependencies.

Minimum checks:
- Export one table.
- Save one plot.
- File paths/errors are handled clearly.

### 5D8 — Final audit

Goal:
- Verify this phase is ready to close.

Audit checklist:
- Desktop app launches.
- Create/generate a model.
- Assign realistic material/section/support/load/mass data.
- Run Static.
- Inspect static result table.
- Display deformed shape.
- Display N/V/M.
- Run Modal on massed model.
- Inspect modal table.
- Display mode shape.
- Run RSA example if integrated.
- Run THA example if integrated.
- Export at least one table or plot.
- `pytest tests/` passes or failures are documented as pre-existing/out of scope.

## Low-Token Codex Prompt Pattern

Use this pattern for each task:

```markdown
Read `AGENTS.md` and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D# — [task title].

Scope:
- Modify only files needed for this task, preferably <5.
- Preserve existing modeling UI behavior.
- No solver math in UI.
- Reuse existing controller/solver/result/visualizer APIs.
- Do not implement later 5D tasks.

Expected behavior:
- [2-5 bullets copied from this file]

Checks:
- Run relevant tests/compile checks only.
- Manually describe the smoke test I should perform.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark task `DONE`, update Current Phase State, add compressed log entry, and compress this completed task's verbose instructions into a short `DONE SUMMARY`.

Report:
- Changed files
- Checks run
- Short summary
- Known limitations / next task
```

## Suggested Prompt Sequence

### Prompt 5D0

```markdown
Read `AGENTS.md`.

Task: Add `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` to the repo root exactly as provided by the user.

Scope:
- Docs only.
- Do not modify source code.

Checks:
- Confirm file exists.

Required doc update:
- In `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`, mark 5D0 `DONE` and add one compressed entry under **Condensed Completion Log**.

Report:
- Changed files only.
```

### Prompt 5D1

```markdown
Read `AGENTS.md`, `README.md`, and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D1 — add the smallest desktop UI path to run Static analysis from the current model.

Scope:
- Inspect only the relevant desktop UI/controller/static-analysis entry files.
- Modify preferably <5 files.
- Preserve all model-building/editing behavior.
- No solver math in UI.
- Do not implement result tables, plots, Modal, RSA, or THA yet.

Expected behavior:
- User can run Static from the desktop UI.
- Current UI model is validated/used through existing controller/model pathways.
- Latest `StaticResults` is stored in an app-level result state.
- UI shows concise success/error status.

Checks:
- Run relevant tests or compile changed files.
- Manually describe the smoke test I should perform.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark 5D1 `DONE`, update Current Phase State, add a compressed log entry, and replace 5D1's verbose instructions with a short `DONE SUMMARY`.

Report:
- Changed files
- Checks run
- Short summary
- Known limitations / next task
```

### Prompt 5D2

```markdown
Read `AGENTS.md` and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D2 — add a static result selector and read-only basic tables.

Scope:
- Build on the stored `StaticResults` from 5D1.
- Modify preferably <5 UI files.
- Do not add plots or dynamic analyses.
- Do not change solver math.

Expected behavior:
- Results panel has empty state before analysis.
- After Run Static, user can select displacements, reactions, element forces, and available intermediate data.
- Selection updates a read-only table.
- Missing fields do not crash the UI.

Checks:
- Run relevant tests or compile changed files.
- Manually describe the smoke test I should perform.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark 5D2 `DONE`, update Current Phase State, add a compressed log entry, and replace 5D2's verbose instructions with a short `DONE SUMMARY`.

Report changed files, checks, summary, limitations/next task.
```

### Prompt 5D3

```markdown
Read `AGENTS.md` and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D3 — embed static plots: deformed shape and N/V/M.

Scope:
- Reuse existing `visualizer.py` behavior where possible.
- Plotting consumes model + `StaticResults` only.
- Modify preferably <5 files.
- Do not implement Modal/RSA/THA.

Expected behavior:
- After Run Static, user can display deformed shape.
- User can display N/V/M for a selected/available element.
- Plot area handles empty/missing result state cleanly.

Checks:
- Run relevant tests or compile changed files.
- Manually describe the smoke test I should perform.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark 5D3 `DONE`, update Current Phase State, add a compressed log entry, and replace 5D3's verbose instructions with a short `DONE SUMMARY`.

Report changed files, checks, summary, limitations/next task.
```

### Prompt 5D4

```markdown
Read `AGENTS.md` and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D4 — add desktop Modal analysis integration.

Scope:
- Reuse existing modal solver/controller APIs.
- Store latest `ModalResults` in result state.
- Add modal result table and selected mode-shape plot.
- Do not require ground motion.
- Do not implement RSA/THA.

Expected behavior:
- User can run Modal from desktop UI.
- Frequencies/periods/modal participation data are visible in tables.
- Selected mode shape can be plotted.
- Massless/missing-mass model gives clear error instead of crash.

Checks:
- Run relevant modal/UI tests or compile changed files.
- Manually describe the smoke test I should perform.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark 5D4 `DONE`, update Current Phase State, add a compressed log entry, and replace 5D4's verbose instructions with a short `DONE SUMMARY`.

Report changed files, checks, summary, limitations/next task.
```

### Prompt 5D5

```markdown
Read `AGENTS.md` and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D5 — add desktop RSA integration using existing backend capability.

Scope:
- Reuse existing RSA solver/result APIs.
- Add only minimal settings needed to run an existing RSA example/workflow.
- Store latest `RSAResults` in result state.
- Add basic RSA summary table and available plot.
- Do not implement THA.

Expected behavior:
- User can run RSA where required modal/dynamic inputs exist.
- Missing spectrum/settings show clear error.
- RSA results are selectable in the results panel.

Checks:
- Run relevant RSA/UI tests or compile changed files.
- Manually describe the smoke test I should perform.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark 5D5 `DONE`, update Current Phase State, add a compressed log entry, and replace 5D5's verbose instructions with a short `DONE SUMMARY`.

Report changed files, checks, summary, limitations/next task.
```

### Prompt 5D6

```markdown
Read `AGENTS.md` and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D6 — add desktop THA integration using existing Newmark/ground-motion backend.

Scope:
- Reuse existing THA and ground-motion APIs.
- Ground motion controls belong only to THA workflow.
- Store latest `THAResults` in result state.
- Add peak summary and available history plots.
- Do not change Static/Modal/RSA behavior.

Expected behavior:
- User can run THA with an existing ground-motion file such as `data/ground_motion.txt` if available.
- Missing/invalid ground motion gives a clear error.
- THA result summaries and histories are selectable.

Checks:
- Run relevant THA/UI tests or compile changed files.
- Manually describe the smoke test I should perform.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark 5D6 `DONE`, update Current Phase State, add a compressed log entry, and replace 5D6's verbose instructions with a short `DONE SUMMARY`.

Report changed files, checks, summary, limitations/next task.
```

### Prompt 5D7

```markdown
Read `AGENTS.md` and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D7 — add small export/report polish for visible results.

Scope:
- Export visible result table to CSV/TXT or copyable text.
- Save current plot to PNG if a plot exists.
- Keep it lightweight; no complex report generator.
- Do not change solver behavior.

Expected behavior:
- User can export one visible table.
- User can save one visible plot.
- Errors/empty states are clear.

Checks:
- Run relevant tests or compile changed files.
- Manually describe the smoke test I should perform.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark 5D7 `DONE`, update Current Phase State, add a compressed log entry, and replace 5D7's verbose instructions with a short `DONE SUMMARY`.

Report changed files, checks, summary, limitations/next task.
```

### Prompt 5D8

```markdown
Read `AGENTS.md` and `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md`.

Task: Phase 5D8 — final audit of desktop analysis/results integration.

Scope:
- No new features unless fixing a blocking regression.
- Run the Phase 5D audit checklist in the md file.
- Update docs only if needed.

Checks:
- Run `pytest tests/` if practical; otherwise run relevant tests and explain why.
- Compile relevant UI files.
- Provide a manual smoke-test checklist for me.

Required doc update:
- Update `PHASE_5_DESKTOP_ANALYSIS_RESULTS.md` using **Required Completion Update — Token-Controlled**: mark 5D8 `DONE` if audit passes, update Current Phase State, add final compressed log entry, and compress any remaining completed verbose task sections.

Report changed files, checks, summary, and remaining limitations.
```

## Condensed Completion Log

Codex appends one compressed entry per completed task. Keep entries short. Do not paste long code, logs, or full test output.

### 5D0 — DONE — 2026-06-16
- Files: `PHASE_5.md`
- Result: Audited desktop entry points, existing Static/Modal/RSA/THA helper APIs, result dataclasses, and visualizer functions usable by desktop UI.
- Checks: `pytest tests/` passed; targeted reads of `src/ui_desktop/app.py`, `src/ui_desktop/main_window.py`, `src/controller.py`, `src/ui/static_analysis.py`, `src/ui/dynamic_analysis.py`, `src/results.py`, `src/main.py`, solver entry symbols, and `src/visualizer.py`.
- Next/limits: Start 5D1 by wiring the existing static helper into the desktop Analyze tab; no source code was changed.

### 5D1 — DONE — 2026-06-16
- Files: `src/ui_desktop/app.py`, `src/ui_desktop/main_window.py`, `tests/test_ui_desktop_static.py`, `PHASE_5.md`
- Result: Desktop users can run Static analysis from the Analyze tab, with latest `StaticResults` cached and success/failure shown in the status log.
- Checks: `python -m py_compile src\ui_desktop\main_window.py src\ui_desktop\app.py`; `pytest tests\test_ui_desktop_static.py tests\test_ui_static.py`; `python -m src.ui_desktop.app` reached Tk main loop and timed out as expected.
- Next/limits: 5D2 should add result selection and tables; no plots or dynamic analyses are wired yet.

### Template

```markdown
### 5D# — DONE — YYYY-MM-DD
- Files: `...`
- Result: ...
- Checks: ...
- Next/limits: ...
```
