# ARCHITECTURE.md

## Target

The project is a Python educational structural analysis application for the submitted desktop MVP scope: 2D Static Analysis and 2D Modal Analysis. The application emphasizes transparent intermediate data, a Tkinter model-building workflow, XML reproducibility, and plots/tables suitable for classroom review.

RSA and THA code may remain in the repository as future-extension work, but response-spectrum and time-history workflows are not part of the final submitted desktop scope.

## Pipeline

```text
Desktop/table/template/XML input
  -> ModelBuilder
  -> StructuralModel
  -> DOF mapping and matrix/vector assembly
  -> Static or Modal solver
  -> result objects
  -> Tkinter tables, matplotlib plots, export
```

Solvers are generalized. They receive assembled matrices/vectors and do not branch by structure family. Frames, trusses, shear frames, cantilevers, and benchmark problems are ordinary models or templates.

## Current Physical Layout

The repository intentionally keeps a mostly flat `src/` layout. Logical layers are mapped to files/modules rather than package folders.

```text
src/
  parser.py                  StructuralModel and XML parsing dataclasses/helpers
  model_builder.py           Programmatic/template/UI/XML-backed model construction
  structural_validator.py    Shared validation checks
  controller.py              Thin coordination layer
  dof_optimizer.py           DOF numbering, free/restrained/active dynamic DOFs
  element_physics.py         Element stiffness, transformations, fixed-end effects
  matrix_assembly.py         Global stiffness/load assembly and reduction support
  dynamic_assembly.py        Mass/damping/dynamic matrix assembly
  banded_solver.py           Static linear solve support
  modal_solver.py            Modal eigenproblem, normalization, modal properties
  results.py                 Static/Modal result containers and related data
  post_processor.py          Reactions, member forces, N/V/M recovery
  visualizer.py              Matplotlib model/result plots
  educational_exporter.py    Text-oriented educational exports
  ui/                        Legacy/prototype UI helpers
  ui_desktop/                Tkinter desktop MVP shell, canvas, panels, result views
```

## Layer Responsibilities

- Model/input layer: `parser.py`, `model_builder.py`, and XML helpers define and create models.
- Validation layer: `structural_validator.py` centralizes structural validity checks.
- Assembly layer: `dof_optimizer.py`, `element_physics.py`, `matrix_assembly.py`, and `dynamic_assembly.py` create the numerical systems.
- Solver layer: `banded_solver.py`, static analysis helpers, and `modal_solver.py` solve assembled systems only.
- Results/post-processing layer: `results.py` and `post_processor.py` preserve intermediate data, reactions, element forces, and diagram values.
- Visualization/export layer: `visualizer.py`, result windows, and export helpers consume models plus result objects.
- UI layer: `ui_desktop/` gathers user input and displays results. It does not implement solver math.

## Static Workflow

```text
ModelBuilder/XML/UI input
  -> StructuralModel
  -> StructuralValidator
  -> DOFManager/DOFOptimizer
  -> assemble K and F
  -> apply boundary reduction: Kff uf = Ff
  -> solve displacements
  -> recover full displacement vector, reactions, member-end forces
  -> compute N/V/M data
  -> StaticResults
  -> tables, deformed shape, member diagrams, export
```

Static results preserve the full and reduced systems (`K`, `Kff`, `F`, `Ff`), DOF map, nodal displacements, support reactions, member-end forces, and N/V/M diagram data.

## Modal Workflow

```text
ModelBuilder/XML/UI input with masses
  -> StructuralModel
  -> StructuralValidator
  -> DOF and dynamic assembly
  -> build K/M and reduced or condensed Kff/Mff
  -> condense massless stiffness-coupled DOFs where required
  -> solve K phi = lambda M phi
  -> normalize mode shapes
  -> compute frequencies, periods, participation factors, effective modal mass
  -> ModalResults
  -> modal summary, mode-shape plot, modal matrices, export
```

Modal analysis must not delete stiffness-coupled massless DOFs as a shortcut. They are statically condensed before the eigenproblem. Disconnected zero-mass DOFs may be removed when they do not affect stiffness transfer.

## Desktop UI Workflow

The Tkinter desktop MVP provides model creation and editing, Static/Modal analysis commands, result windows, embedded plots, and visible table/plot export. Canvas/table/template actions should call `ModelBuilder` rather than constructing parser dataclasses directly.

When model data changes after analysis, cached Static and Modal results should be cleared or marked stale so the UI does not display old results as current.

## XML Workflow

XML is the persistence and reproducibility backend:

- Save/export a desktop-created model to XML.
- Load XML into the same `ModelBuilder`/`StructuralModel` pipeline.
- Preserve analysis-relevant model data such as geometry, supports, releases, loads, masses, materials, and sections.

Students should be able to use the desktop workflow without manually writing XML.

## Visualization And Export

Plotting consumes a model plus result object. Required final-scope plots are:

- model preview
- static deformed shape
- axial/shear/moment diagrams
- modal mode shapes

Result windows may export visible result tables as text/CSV and visible plots as PNG where practical. XML model export remains the model persistence path.

## Future Extensions

RSA and THA are future desktop workflows. Any future implementation should reuse the same pipeline: assemble matrices, run generalized solvers, return result objects, then visualize/export through the UI without moving solver math into UI code.
