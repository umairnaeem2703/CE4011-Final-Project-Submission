# CE 4011 Structural Analysis Application

An educational 2D structural analysis application for building, solving, and visualizing truss, frame, beam, and benchmark models. The final submitted desktop scope is Static Analysis + Modal Analysis only. The project exposes the learning pipeline for those workflows: model input, DOF mapping, stiffness/mass assembly, solver execution, result objects, diagrams, and exportable intermediate data.

The final user-facing direction is a Tkinter desktop MVP. XML remains the backend save/load/export and reproducibility format; students are not expected to manually write XML. Blank, 2D Frame-Truss, and 2D Shear Frame workflows, canvas editing, templates, and table-style backup input all build models through `ModelBuilder`.

## Implemented

- Static analysis for 2D truss, frame, and beam-style models using assembled global stiffness matrices, reduced systems, displacements, reactions, element forces, and axial/shear/moment data.
- Modal analysis with dynamic assembly, mass handling, eigenvalues, frequencies, periods, mode shapes, modal mass, participation factors, and effective modal mass outputs.
- Backend Response Spectrum Analysis (RSA) and Time-History Analysis (THA) modules remain in the repository as future-extension work, but they are not part of the final submitted desktop workflow.
- Educational intermediate outputs, including DOF maps, full and reduced matrices/vectors, solver inputs, solver outputs, and post-processing data for reports and tests.
- XML parsing as the backend model format, including nodes, elements, supports, loads, masses, materials, sections, and analysis settings.
- `ModelBuilder` as the only model creation path for programmatic, table, template, XML, and graphical input; builder-created models can be exported to XML and parsed back, including lumped masses.
- A thin MVC-style controller layer that coordinates model building, validation, XML export, and analysis calls without owning solver math.
- Shared structural validation through `StructuralValidator`.
- Visualization and post-processing through matplotlib, including model preview, deformed shapes, axial/shear/moment diagrams, and mode shapes for the submitted desktop scope.
- A legacy Streamlit local UI/dashboard for XML upload, table/form-based model input, static and dynamic analysis controls, cached results, and visualization display.
- Focused pytest coverage for model input, static analysis, dynamic assembly, modal analysis, RSA, THA/Newmark, UI helpers, and visualization behavior.

## Under Development

- Tkinter desktop MVP with New Model workflows for Blank, 2D Frame-Truss, and 2D Shear Frame.
- Canvas-based 2D model builder on top of `ModelBuilder`.
- Static and Modal access from the desktop UI with embedded result plots and tables.
- More complete export/report flows for classroom use.
- Expanded templates and validation examples for common educational structures.
- Final UI polish, result presentation, and end-to-end ergonomics.
- Final documentation, manuals, and classroom-facing writeups.

## Architecture

The project follows a layered educational pipeline:

```text
Tkinter canvas/tables/templates/XML -> ModelBuilder -> StructuralModel -> DOF/K/M/C/F assembly -> solvers -> result objects -> embedded plots/tables/export
```

Solvers operate on assembled matrices and vectors rather than branching by structure type. Structure families such as shear frames, cantilevers, frames, trusses, and benchmarks are represented as ordinary models or templates. `ModelBuilder` creates all `StructuralModel` instances for internal, table, template, XML, and graphical input, `StructuralValidator` checks model validity, and the controller remains a thin coordination layer. The solver, model input, XML, UI, and visualization responsibilities are kept separate so the numerical workflow remains transparent and testable.

## Repository Map

```text
src/
  flat module layout for parser, ModelBuilder, controller, validation
  assembly, DOF, matrix, static, and modal solver modules; RSA/Newmark backend modules retained for future extension
  result containers, post-processing, educational export, and visualization
  ui/ Tkinter desktop MVP modules; legacy Streamlit dashboard modules may remain as prototypes

data/      XML examples and schema material
tests/     focused unit, integration, UI-helper, and visualization tests
results/   generated reports and figures when analyses are run locally
```
