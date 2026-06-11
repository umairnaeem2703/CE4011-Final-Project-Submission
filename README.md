# Structural Analysis Solver

A matrix-based 2D structural analysis solver for **truss**, **frame**, and **beam** models defined in XML — built entirely with standard Python libraries (no NumPy required). Includes static analysis, dynamic modal analysis, and frequency-response computation.

---

## Features

- **XML-driven models** — define nodes, elements, constraints, and loads in a clean XML schema
- **DOF optimization** — Reverse Cuthill-McKee reordering minimizes bandwidth for efficient solving
- **Banded system solver** — custom banded stiffness matrix assembly and linear solver
- **Advanced constraints** — Rigid Diaphragm and Axially Rigid member support via Union-Find
- **Dynamic analysis** — modal extraction, natural frequencies, mode shapes, and damped modal-superposition response
- **Rich visualizations** — deformed geometry and NVM (Axial/Shear/Moment) diagrams with SAP2000-compatible conventions

---

## Quick Start

### Prerequisites

- Python 3.10+
- `matplotlib` (for diagram generation)

### Setup & Run

```bash
# Activate your virtual environment
.venv\Scripts\activate

# Run the analysis on the default test files in ./data/
python src/main.py
```

Results (reports, deformed plots, NVM diagrams) are written to `./results/`.

---

## Analysis Workflow

Each load case is processed through the following pipeline:

1. **Parse XML** — load nodes, elements, constraints, and loads
2. **Optimize DOF Numbering** — Reverse Cuthill-McKee reordering
3. **Assemble System Matrix** — banded global stiffness matrix and load vector
4. **Solve Linear System** — custom banded solver → nodal displacements
5. **Dynamic Analysis** — modal extraction (natural frequencies and mode shapes) and modal-superposition response computed by `modal_solver.py` (supports damping and modal combination).
6. **Post-Process** — member forces and support reactions
7. **Generate Visuals** — reports, NVM diagrams, deformed shape plots

---

## Visualization

### Deformed Shape

Computed via the `visualizer.py` pipeline:

- **Recover Full DOFs** — merges active solver DOFs with restrained boundary conditions
- **Transform Displacements** — converts to element local coordinates
- **Hermite Interpolation** — cubic interpolation for transverse, linear for axial displacement
- **Global Mapping** — back-transforms with a visual scale factor

### NVM Diagrams (Axial · Shear · Moment)

| Feature | Detail |
|---|---|
| Sign convention | SAP2000-compatible (moment on tension side) |
| Coloring | Green = positive, Red = negative |
| Labeling | Auto-tagged absolute max/min peaks per element |
| Scaling | Auto-scales to structure dimensions; optional user override |
| Distributed loads | Parabolic curves via high-resolution step intervals |

---

## Advanced Constraints

### Rigid Diaphragm

Enforces rigid floor-slab behavior — nodes sharing the same Y-elevation share a single master UX DOF while retaining independent UY and RZ.

### Axially Rigid Members

Members tagged `is_axially_rigid="true"` couple all DOFs (UX, UY, RZ) between end nodes via a Union-Find (DSU) structure, simulating rigid links or composite elements.

### DOF Assignment Strategy

| Level | Scope | Shared DOFs |
|---|---|---|
| Rigid Diaphragm Masters | Per floor (same Y) | UX only |
| Axially Rigid Masters | Per connected component | UX, UY, RZ |
| Independent Nodes | All others | UX, UY, RZ (unique) |

Slave nodes inherit their master's DOF indices, naturally reducing system size.

---

## Project Structure

```
src/
├── main.py                 # Entry point & run_analysis()
├── parser.py               # XML model parsing
├── dof_optimizer.py        # DOF numbering (RCM & Union-Find)
├── matrix_assembly.py      # Stiffness matrix assembly
├── banded_solver.py        # Custom banded linear solver
├── modal_solver.py         # Modal analysis & dynamic response
├── post_processor.py       # Results & reporting
├── element_physics.py      # Element stiffness calculations
├── structural_validator.py # Model validation
├── math_utils.py           # Organic linear algebra utilities
└── visualizer.py           # Deformed shape & NVM diagrams

data/                       # Input XML files
├── Assignment_4_Q2a.xml
├── Assignment_4_Q2b.xml
└── SCHEMA.xml              # XML schema documentation

results/                    # Generated reports and PNG plots
tests/                      # Unit and integration test suite
```
