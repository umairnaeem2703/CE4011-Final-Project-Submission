# CE 4011 Structural Analysis Application

An educational 2D structural analysis application for building, solving, and visualizing truss, frame, beam, and benchmark models. The project is designed to expose the full analysis pipeline for learning: model input, DOF mapping, stiffness/mass/damping assembly, solver execution, result objects, diagrams, and exportable intermediate data.

XML remains the backend save/load and reproducibility format. Students are not expected to manually write XML; table-style input is intended as an editable backup workflow, and future graphical input can be built on top of the same internal model creation path.

## Implemented

- Static analysis for 2D truss, frame, and beam-style models using assembled global stiffness matrices, reduced systems, displacements, reactions, element forces, and axial/shear/moment data.
- Modal analysis with dynamic assembly, mass handling, eigenvalues, frequencies, periods, mode shapes, modal mass, participation factors, and effective modal mass outputs.
- Response Spectrum Analysis (RSA) with spectrum interpolation, modal response vectors, SRSS/CQC combination, and peak response quantities.
- Time-History Analysis (THA) using Newmark average-acceleration integration, ground-motion input handling, displacement/velocity/acceleration histories, and base response histories.
- Educational intermediate outputs, including DOF maps, full and reduced matrices/vectors, solver inputs, solver outputs, and post-processing data for reports and tests.
- XML parsing as the backend model format, including nodes, elements, supports, loads, masses, materials, sections, and analysis settings.
- `ModelBuilder` as the internal API for programmatic, table, template, and future graphical input; builder-created models can be exported to XML and parsed back, including lumped masses.
- A thin MVC-style controller layer that coordinates model building, validation, XML export, and analysis calls without owning solver math.
- Shared structural validation through `StructuralValidator`.
- Visualization and post-processing through matplotlib, including model preview, deformed shapes, axial/shear/moment diagrams, mode shapes, response spectrum plots, and THA histories.
- A Streamlit local UI/dashboard for XML upload, table/form-based model input, static and dynamic analysis controls, cached results, and visualization display.
- Focused pytest coverage for model input, static analysis, dynamic assembly, modal analysis, RSA, THA/Newmark, UI helpers, and visualization behavior.

## Under Development

- Full graphical drawing canvas and richer editable table workflows on top of `ModelBuilder`.
- More complete export/report flows for classroom use.
- Expanded templates and validation examples for common educational structures.
- Final UI polish, result presentation, and end-to-end ergonomics.
- Final documentation, manuals, and classroom-facing writeups.

## Architecture

The project follows a layered educational pipeline:

```text
input tables/XML/templates -> StructuralModel -> DOF/K/M/C/F assembly -> solvers -> result objects -> plots/export
```

Solvers operate on assembled matrices and vectors rather than branching by structure type. Structure families such as shear frames, cantilevers, frames, trusses, and benchmarks are represented as ordinary models or templates. `ModelBuilder` creates `StructuralModel` instances for internal and future table/graphical input, `StructuralValidator` checks model validity, and the controller remains a thin coordination layer. The solver, model input, XML, UI, and visualization responsibilities are kept separate so the numerical workflow remains transparent and testable.

## Repository Map

```text
src/
  flat module layout for parser, ModelBuilder, controller, validation
  assembly, DOF, matrix, modal, RSA, and Newmark solver modules
  result containers, post-processing, educational export, and visualization
  ui/ Streamlit dashboard modules

data/      XML examples and schema material
tests/     focused unit, integration, UI-helper, and visualization tests
results/   generated reports and figures when analyses are run locally
```
