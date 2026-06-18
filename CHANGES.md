This file is an implementation specification, not a brainstorming document. Codex must implement only the listed items and must not broaden the task into visual polish, controller refactoring, solver changes, XML schema changes, or RSA/THA UI work.

Read `AGENTS.md`, `PHASE_4_COMPLETION_AUDIT.md`, `PHASE_5.md`, and only the Tkinter desktop files needed for this task, especially:

* `src/ui_desktop/main_window.py`
* `src/ui_desktop/property_panel.py`
* `src/ui_desktop/canvas.py`
* `src/ui_desktop/template_dialog.py`
* `src/ui_desktop/object_tree.py`
* any result-viewer/helper files directly referenced by `main_window.py`

Task: Final desktop architecture cleanup for the revised Static + Modal submission scope.

Context:
The final submitted project scope is:

* Static Analysis
* Modal Analysis

RSA and THA are deferred/future work and must not be exposed in the submitted desktop UI.

Important rules:

* Do not change solver math.
* Do not change static/modal result dataclasses unless strictly necessary.
* Do not change XML schema.
* Do not touch `src/controller.py`.
* Preserve the current flat `src/` layout.
* Keep changes focused and preferably under 5 files.
* Do not clean result aliases such as `latest_static_results/latest_static_result` or `latest_modal_results/latest_modal_result` unless existing tests clearly cover the change.
* Do not add PDF/report automation.
* Do not refactor the whole UI.

Implement the following UI cleanup decisions:

1. New Model workflow

   * Expose only:

     * `Blank Model`
     * `2D Shear Frame Template`
   * Remove or rename the vague `2D General Structure` option.
   * `Blank Model` should create the existing seeded blank/general builder behavior if that is how the current app starts a usable empty model.
   * Do not add a 2D Frame-Truss template unless it already exists cleanly and is already wired.

2. Stale result invalidation

   * When the model is edited after analysis, automatically clear old static and modal results.
   * This includes edits such as node/member creation, deletion, movement, replication, coordinate edits, supports, loads, masses, diaphragms, material/section/member property changes, and XML/new model loading.
   * After clearing, any open result window should refresh to a clear message such as:
     `Results were cleared because the model changed. Run analysis again.`
   * Static Results should no longer show old static results after model edits.
   * Modal Results should no longer show old modal results after model edits.
   * If the model already has dirty-state handling, reuse it. Do not create a parallel heavy cache system.

3. View menu cleanup

   * Remove the visible disabled `Window Select` item from the View menu.
   * Do not remove the internal canvas window-selection behavior if it is already working.

4. Move workflow cleanup

   * Remove `Move Selection` as a separate Edit menu command.
   * Fold move controls into `Select / Inspect`.
   * Expose dx/dy move controls in the selected-object inspector/property panel.
   * Keep existing movement behavior if possible; only change how the user reaches it.
   * Do not break coordinate editing or replication.

5. Top-level Results menu

   * Keep only:

     * `Static Results`
     * `Modal Results`
   * Do not add top-level result entries for deformed shape, N/V/M, mode shapes, or matrices.
   * Those should remain inside the Static Results or Modal Results windows.

6. Result-window exports

   * Add export actions inside the relevant result windows, not as a new global Export menu.
   * Required export types:

     * XML model export is already handled by Save XML; leave it as is.
     * TXT and/or CSV export for visible result tables.
     * PNG export for visible plots.
   * Static result window should support exporting currently visible static table data to TXT/CSV where practical.
   * Modal result window should support exporting currently visible modal table data to TXT/CSV where practical.
   * Plot views should support exporting the current plot to PNG where practical.
   * Keep export behavior simple and classroom-oriented. Do not add PDF generation.

7. Material/section workflow

   * Do not deeply refactor material/section assignment now.
   * Only make minimal label/wording cleanup if needed for clarity.
   * Do not redesign dialogs.

8. Validation behavior

   * Do not perform a broad validation refactor in this task.
   * If analysis already runs without automatic validation, leave major validation changes for a separate prompt unless a small non-invasive check is already available.
   * Do not introduce solver-side changes.

Tests/checks:

* Add or update focused UI tests where practical for:

  * New Model options expose `Blank Model` and `2D Shear Frame Template`.
  * `Window Select` is no longer visible in View.
  * `Move Selection` is no longer a separate Edit command.
  * Static/modal results are cleared after a representative model edit.
  * Static Results and Modal Results remain available as top-level results actions.
* Run:

  * `python -m py_compile` on modified Python files
  * focused desktop UI tests
  * relevant static/modal UI tests
* Do not require full `pytest tests/` to pass if there are known unrelated pre-existing failures, but report them clearly.

Report:

* Changed files.
* UI actions removed/renamed.
* How stale-result clearing works.
* Export actions added and their formats.
* Tests run and results.
* Any limitations left for final submission.


Out of scope:
- controller.py refactor
- solver math changes
- XML schema changes
- RSA/THA desktop UI exposure
- PDF/report automation
- visual theme polish
- broad material/section workflow redesign