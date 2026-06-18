# AGENTS.md

## Mission

Maintain the CE 4011 educational structural analysis desktop MVP for final submitted scope: Static Analysis, Modal Analysis, Tkinter model building/results, XML reproducibility, visualization, and concise documentation.

## Scope Rules

- Final submitted analyses are Static and Modal only.
- RSA and THA may remain as future-extension backend work, but do not expose them as final desktop scope unless explicitly requested.
- Preserve the current flat `src/` layout unless a refactor is explicitly approved.
- Prefer small, focused patches that reuse existing APIs, names, and result objects.
- Do not change solver behavior as part of UI or documentation cleanup.

## Architecture Rules

Pipeline:

```text
Tkinter canvas/tables/templates/XML -> ModelBuilder -> StructuralModel -> DOF/K/M/F assembly -> solvers -> result objects -> plots/tables/export
```

- `ModelBuilder` is the model creation API for programmatic, template, table, XML, and graphical input.
- `StructuralModel` stores model data and validation state; it does not solve or plot.
- Solvers operate on assembled matrices/vectors and return result objects/intermediate data.
- UI code collects input, validates fields, calls model/solver APIs, and displays results. UI code must not contain solver math.
- `Controller` remains a thin coordination layer and must not own solver math or UI toolkit-specific logic.
- XML is the backend save/load/export and reproducibility format; users should not be expected to hand-write XML.
- Reuse `StructuralValidator` for model validation instead of duplicating validation logic.

## Dependency Rules

- Core numerical solver: Python standard library only unless explicitly approved.
- Visualization: matplotlib is allowed.
- UI: Tkinter is the final desktop MVP. Streamlit may remain only as legacy/prototype code.
- Tests: pytest is allowed.
- Avoid numpy/scipy/sympy/pandas in solver core.

## Required Educational Outputs

- Static: DOF map, `K`, `Kff`, `F`, `Ff`, displacements, reactions, element forces, and N/V/M data.
- Modal: `K`, `M`, reduced/condensed dynamic matrices where available, eigenvalues, frequencies, periods, mode shapes, modal mass, participation factors, effective modal mass, and mass participation ratios.
- Massless stiffness-coupled DOFs must be condensed before modal analysis. Direct deletion is only acceptable for disconnected zero-mass DOFs.

## Testing And Maintenance

- Every numerical change needs a focused, hand-checkable test or verification example.
- For non-numerical changes, run the narrowest relevant checks and report exactly what was run.
- Do not remove intermediate data needed by reports, tests, or educational inspection.
- Do not duplicate static/modal logic by model type; shear frames, cantilevers, frames, trusses, and benchmarks are models/templates, not separate solver families.
