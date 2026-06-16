# PHASE_5.md — Desktop Analysis + Results

## Goal

Connect the Tkinter desktop model builder to existing backend analysis and result visualization.

Workflow:

```text
Desktop model -> Run analysis -> Store result -> Show table/plot -> Export
```

## Rules

* Preserve current flat `src/` layout.
* Do not move solver math into UI.
* Do not create new solver paths by model type.
* Reuse existing backend APIs.
* Modify only files needed for the current task.
* Prefer fewer than 5 changed files.
* Do not read unrelated docs/files.
* Do not write detailed logs here.
* After each task, update only `Current State` and the task status table.

## Previous Phase Summary

Architecture/UI cleanup is complete enough to proceed. Rigid-link behavior is clarified, flexurally rigid backend work is deferred, local/global member loads and local-axis display are implemented, diaphragm assignment is selection-based, and next work is desktop analysis/results integration.

## Current State

5D0, 5D1, 5D2, 5D2B, 5D3A, 5D3B, 5D3C, 5D3D, 5D3E, and 5D3F are complete. The Static Results workflow is stable after audit, including no-result guards, table/viewer launch paths, member-viewer cached refresh, and cursor-only slider updates. The next implementation task is 5D4 Modal.

## Task Status

| Task                                    | Status | One-line Result                                                                                                         |
| --------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| 5D0 Integration entry-point audit       | DONE   | Identified the desktop UI/controller, static backend, result object, and visualization entry points needed for Phase 5. |
| 5D1 Static run from desktop UI          | DONE   | Desktop UI can run Static analysis from the current model, store the result, and show success/error status.             |
| 5D2 Static result tables                | DONE   | Basic read-only static result tables are available for stored Static results.                                           |
| 5D2B Static result readability cleanup  | DONE   | Desktop static result tables now use centralized formatting, unit-aware headers, clearer DOF-map rows, and intermediate K/Kff/F/Ff views. |
| 5D3A Complete Model Static Viewer shell  | DONE   | Added a dedicated static viewer shell entry with reserved deformed-shape and N/V/M modes. |
| 5D3B Complete Model deformed shape + full-model N/V/M | DONE   | Rendered the stored complete-model deformed shape and full-model N/V/M plots inside the Results workflow. |
| 5D3C Individual Member Result Viewer shell | DONE   | Added a separate member-level static result viewer shell with selection-aware workflow tabs. |
| 5D3D Member end forces + member N/V/M    | DONE   | Added selected-member end forces and filtered member N/V/M diagram rendering in the member-review tab. |
| 5D3E Member displacement diagram + location/scroll/max values | DONE   | Added the integrated member review cursor, displacement strip, and current/max value summaries. |
| 5D3F Static Results workflow stabilization audit | DONE   | Audited the Static Results workflow and confirmed stable no-result, table, complete-model viewer, and member-viewer behavior. |
| 5D4 Modal run + mode shape/results       | TODO   |                                                                                                                         |
| 5D5 RSA run + results                   | TODO   |                                                                                                                         |
| 5D6 THA run + histories                 | TODO   |                                                                                                                         |
| 5D7 Export visible tables/plots         | TODO   |                                                                                                                         |
| 5D8 Final smoke audit                   | TODO   |                                                                                                                         |

## Update Rule

After each task, update only:

1. task status from TODO to DONE
2. one-line result
3. Current State in 1–3 sentences

Do not add detailed completion logs.
Do not paste test output.
Do not paste code.
