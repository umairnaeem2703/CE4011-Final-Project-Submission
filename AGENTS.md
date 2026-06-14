# AGENTS.md

## Mission
Build CE 4011 educational structural analysis software with OOP static/dynamic solvers, spreadsheet-style input, XML save/load, model preview, visualization, tests, and concise docs.

## Token Rules
- Work one feature/subsystem per task.
- Inspect only files needed for the current task.
- Do not scan/rewrite the whole repo unless explicitly asked.
- Prefer small patches; reuse existing APIs and names.
- Keep plans/results <=10 bullets.
- Do not paste long code/logs; summarize and list changed files.

## Core Architecture Rule
Pipeline:
```text
input tables/XML/templates -> StructuralModel -> DOF/K/M/C/F assembly -> solvers -> result objects -> plots/export
```
Solvers must receive matrices/vectors and must not branch by structure type. Shear frames, cantilevers, frames, trusses, and benchmarks are models/templates, not separate solver families.

## Input Workflow Architecture
- Preserve the current flat `src/` layout unless explicitly asked to refactor.
- Do not create `src/model/`, `src/io/`, `src/assembly/`, or `src/solvers/` package folders unless explicitly requested.
- `ModelBuilder` is the internal model creation API for programmatic, table, template, and future graphical input.
- Future graphical/table input should call `ModelBuilder` rather than directly constructing parser dataclasses.
- XML is the backend save/load and reproducibility format; students should not be expected to manually write XML.
- `Controller` is a thin coordination layer only. It must not contain solver math or Streamlit-specific code.
- Reuse `StructuralValidator` for model validation; do not replace validation with parallel logic.

## Dependency Rules
- Core numerical solver: Python standard library only unless approved.
- Visualization: matplotlib allowed.
- UI: Streamlit allowed.
- Tests: pytest allowed.
- Avoid numpy/scipy/sympy/pandas in solver core.

## Layer Rules
- `StructuralModel` stores/validates data only; it does not solve or plot.
- UI collects input, validates fields, builds model, calls solver, displays results; no solver math in UI.
- View/UI code and `Controller` must not contain solver math.
- Plotting consumes model + result objects only.
- Solvers operate on assembled matrices/vectors and return result objects/intermediate data.
- Keep solver, model, IO, UI, and visualization separate.

## Required Outputs
Preserve educational intermediate data:
- Static: DOF map, K/Kff, F/Ff, displacements, reactions, element forces, N/V/M data.
- Modal: K/M, eigenvalues, frequencies, periods, mode shapes, modal mass, participation factors, effective modal mass. Massless stiffness-coupled DOFs shall be statically condensed before modal analysis; direct deletion is only permitted for disconnected zero-mass DOFs.
- RSA: spectrum values, modal response vectors, SRSS/CQC results, peak displacement/drift/base shear/OTM where meaningful.
- THA: Newmark time vector, force/excitation history, u/v/a histories, base shear/OTM histories, step table where practical.

## Visualization
`visualizer.py` is the reference for plotting behavior. Preserve its logic/sign conventions and adapt only API mismatches. Required plots: model preview, deformed shape, axial/shear/moment diagrams, mode shapes, response spectrum, THA histories.

## Testing
Every numerical change needs focused tests or verification examples. Prefer small hand-checkable cases.

---

## Pre-Task Checklist (2 minutes)

**Before starting ANY task**, complete this checklist:

- [ ] **Phase N-1 Complete?** All previous phase tests pass (run `pytest tests/`)
- [ ] **Files to Modify** — List <5 files (abort if >5; break into smaller tasks)
- [ ] **Files to Read** — List 1–3 files for context only (do not modify)
- [ ] **In Scope?** Changes stay within phase folder/module (e.g., Phase 1 doesn't touch solver/)
- [ ] **Tests Exist?** At least 1 focused test defined for this change

**Abort if any checklist item fails.** Do not proceed.

---

## Abort / Revert Criteria

**If a task requires >3 Codex prompts** (i.e., multiple revision rounds):

1. **STOP.** Revert all changes to the last passing commit state.
2. **Break it smaller.** Split task into 2–3 discrete sub-tasks, each <1 hour of work.
3. **One sub-task per prompt.** Do not batch.
4. **Verify each sub-task** with its focused test before moving to the next.
5. **Only then continue** to the next sub-task.

**Example:** If Phase 4 (Modal) is failing after 3 attempts, revert modal_solver.py, then:
- Prompt 1: Implement eigenvalue solver only, test on SDOF
- Prompt 2: Add mode shape normalization, test on cantilever
- Prompt 3: Add participation factors, test on 3-story frame

---

## Quick Test Rule

Every test must be **hand-computable and fast**:

- **Setup code** <20 lines (plain Python, no build scripts)
- **Reference result** < 1 page hand-calculation or closed-form formula
- **Single logical assertion** (or very few: <5)
- **Runtime** < 0.5 seconds
- **Example:**
  ```python
  def test_axial_bar_displacement():
      """Verify: Axial bar tip displacement u = PL/(EA)."""
      P, L, E, A = 10, 5, 2e8, 0.01
      u_expected = (P * L) / (E * A)
      u_computed = run_analysis(...)  # < 10 lines
      assert abs(u_computed - u_expected) < 0.001 * u_expected
  ```

**Do not** write tests with >100 lines of data setup or that require external software.

---

## Relevant Tests Definition

When a task says "run relevant tests", apply this rule:

**Relevant tests** = (files modified) + (modules that import modified files)

**Examples:**
- Modify `dof_optimizer.py` → run `test_dof*.py` + `test_assembly.py` (assembly uses DOFs)
- Modify `modal_solver.py` → run `test_modal*.py` + `test_dynamic_assembly.py`
- Modify `visualizer.py` → run visualization-specific checks (no need to re-run static solver tests)

**Never run the full test suite** unless explicitly asked or Phase completion is required.

---

## Do Not
- Do not duplicate static/modal/RSA/THA logic by model type.
- Do not move solver math into Streamlit/UI.
- Do not remove intermediate variables needed for reports/tests.
- Do not skip pre-task checklist (2 minutes well spent prevents 2 hours of rework).
- Do not commit changes if relevant tests do not pass.
