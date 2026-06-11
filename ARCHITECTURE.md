# ARCHITECTURE.md

## Target
Python OOP structural analysis program for 2D static and generalized 2D dynamic analysis: modal, RSA, and THA. The engine must be transparent for education and expose intermediate matrices/results.

## Pipeline
```text
Input/UI -> Model -> DOF/Assembly -> Solver -> Results -> Visualization/Export
```

## Package Layout
```text
src/
  core/              # matrix, linear solver, eigen, interpolation, errors
  model/             # StructuralModel, Node, Material, Section, Support, Load, Mass
  elements/          # ElementBase, Truss2D, Beam2D/Frame2D, Spring
  assembly/          # DOFManager, K/M/C/load assembly, boundary reduction
  solvers/           # Static, Modal, RSA, Newmark, SolverRunner
  results/           # StaticResults, ModalResults, RSAResults, THAResults
  io/                # CSV/XML/JSON read-write, report/export helpers
  templates/         # shear frame, cantilever, portal frame examples
  visualization/     # matplotlib figures only
  ui/                # Streamlit forms/views/session state
tests/
```

## Responsibilities
- `StructuralModel`: stores nodes, elements, supports, loads, masses, analysis settings, dirty state, cached matrices.
- `ElementBase`: local stiffness/mass, transformation, global matrices, force recovery.
- `DOFManager`: global DOF map, free/restrained DOFs, reduced mapping. Default node DOFs: `[ux, uy, rz]`.
- Assemblers: build global `K`, `M`, `C`, `F`, `P(t)` and reduced systems.
- Solvers: operate only on assembled matrices/vectors/settings.
- Results: dataclass-style containers; no loose arrays.
- Templates: generate ordinary `StructuralModel` objects only.
- UI: no analysis math; calls engine and displays results.

---

## Solver Contracts
```text
Static:  K u = F
Modal:   K phi = lambda M phi
Dynamic: M u_ddot + C u_dot + K u = P(t)
EQ THA:  P(t) = -M r ag(t)
```

---

## Result Object Contracts (Dataclass Sketches)

These define what each solver produces. Implement in Phase corresponding to each solver.

### StaticResults (Phase 2)
```python
@dataclass
class StaticResults:
    """Static analysis output."""
    K: list  # Full global stiffness matrix (n_dof x n_dof)
    Kff: list  # Reduced stiffness for free DOFs (n_free x n_free)
    F: list  # Full load vector (n_dof x 1)
    Ff: list  # Reduced load vector for free DOFs (n_free x 1)
    
    displacements: dict  # {node_id: [ux, uy, rz]} (full, includes prescribed)
    reactions: dict  # {node_id: [Fx, Fy, Mz]} at supports
    
    # Element forces in local coordinates
    element_forces: dict  # {element_id: [N/Ni, V/Vi, M/Mi, N/Nj, V/Vj, M/Mj]}
    
    # NVM data (for diagrams)
    nvm_data: dict  # {element_id: {"N": [...], "V": [...], "M": [...]}}
    
    dof_map: dict  # {node_id: [dof_ux, dof_uy, dof_rz]}
    load_case_id: str
```

### ModalResults (Phase 4)
```python
@dataclass
class ModalResults:
    """Modal analysis output."""
    K: list  # Full global stiffness (n_dof x n_dof)
    M: list  # Full global mass (n_dof x n_dof)
    
    eigenvalues: list  # lambda (omega^2) values, ascending order
    frequencies: list  # f (Hz)
    periods: list  # T (seconds)
    
    # Mode shapes, mass-orthonormalized: phi^T M phi = I
    mode_shapes: list  # [phi_0, phi_1, ...] each is (n_dof x 1)
    
    # Modal properties
    modal_masses: list  # M_modal,n = phi_n^T M phi_n (should be ~1.0 if normalized)
    participation_factors: list  # Gamma_n = phi_n^T M r / M_modal,n
    effective_masses: list  # M_eff,n = Gamma_n^2
    mass_participation_ratios: list  # M_eff,n / (r^T M r)
    
    # For reference
    influence_vector: list  # r (e.g., [1,0,0,1,0,0,...] for horizontal excitation)
    total_participating_mass: float  # sum(M_eff,n) or r^T M r
    
    num_modes_requested: int
    num_modes_extracted: int
```

### RSAResults (Phase 6)
```python
@dataclass
class RSAResults:
    """Response Spectrum Analysis output."""
    spectrum_periods: list  # T values (seconds)
    spectrum_accelerations: list  # Sa(T) values (m/s^2 or g)
    
    # Modal data
    num_modes: int
    periods: list  # T_n for each mode
    
    # Response quantities per mode (before combination)
    modal_response_vectors: list  # {mode_n: {dof: response_value}}
    modal_base_shears: list  # V_base,n per mode
    modal_overturning_moments: list  # OTM_n per mode
    
    # Combined response (SRSS or CQC)
    combination_method: str  # "SRSS" or "CQC"
    combined_response: dict  # {dof: combined_value}
    combined_base_shear: float
    combined_overturning_moment: float
    
    # CQC coupling coefficients (if used)
    rho_matrix: list  # (n_modes x n_modes) coupling factors
    
    damping_ratio: float  # zeta (%)
```

### THAResults (Phase 5)
```python
@dataclass
class THAResults:
    """Time-History Analysis output."""
    time_vector: list  # t values (seconds)
    excitation_history: list  # ag(t) values (input acceleration, m/s^2)
    applied_force_history: list  # P(t) = -M r ag(t) values
    
    # Response histories (n_steps x n_dof)
    displacement_history: list  # u(t)
    velocity_history: list  # u_dot(t)
    acceleration_history: list  # u_ddot(t)
    
    # Base response histories
    base_shear_history: list  # V_base(t)
    overturning_moment_history: list  # OTM(t)
    
    # Peak response quantities (for summary)
    peak_displacement: dict  # {dof: max_absolute_value}
    peak_velocity: dict
    peak_acceleration: dict
    peak_base_shear: float
    peak_overturning_moment: float
    
    # Step table (optional, for reporting a few key time steps)
    step_table: list  # [(t, u, v, a, V_base, OTM), ...] sample steps
    
    # Newmark parameters used
    damping_ratio: float  # zeta
    dt: float  # time step
    num_steps: int
```

---

## Reserved Model Attributes (Implement in Phase Indicated)

Add these to `StructuralModel` definition for future phases:

```python
# Phase 1/Core
self.is_dirty: bool = True  # Mark model as needing rebuild

# Phase 2 (Static Assembly)
self.cached_dof_map: dict = None
self.cached_K: list = None
self.cached_F: list = None
self.cached_Kff: list = None
self.cached_Ff: list = None

# Phase 3 (Dynamic Assembly)
self.cached_M: list = None
self.cached_C: list = None
self.damping_model: str = "rayleigh"  # or "modal", "none"
self.rayleigh_alpha: float = 0.0
self.rayleigh_beta: float = 0.0

# Phase 5+ (THA)
self.excitation_file: str = None  # path to ground motion
self.excitation_direction: str = "x"  # or "y", "z"
self.time_step: float = 0.01
self.num_steps: int = 0

def mark_dirty(self):
    """Called whenever input changes (geometry, loads, supports)."""
    self.is_dirty = True
    self.cached_K = None
    self.cached_M = None
    self.cached_C = None
    self.cached_dof_map = None
```

---

## Dependency Checks (Implement in Each Phase)

Phase solvers must validate that prior phases completed. Examples:

```python
# In modal_solver.py (Phase 4)
def validate_phase_3_complete(model):
    """Verify mass matrix is assembled before modal analysis."""
    assert hasattr(model, 'M') and model.M is not None, \
        "Phase 3 incomplete: mass matrix not assembled. Run assembly first."
    assert len(model.M) == model.num_dofs, \
        "Mass matrix shape mismatch."

# In rsa_solver.py (Phase 6)
def validate_phase_4_complete(results_modal):
    """Verify modal results exist before RSA."""
    assert results_modal is not None, \
        "Phase 4 incomplete: run modal analysis first."
    assert len(results_modal.periods) > 0, \
        "No modal periods extracted."
```

---

## UI Flow (Phase 8)

```text
user input (table/form) -> validate -> mark model dirty 
  -> rebuild model/DOFs (if needed, check is_dirty) 
  -> run selected analysis (static/modal/RSA/THA) 
  -> cache results 
  -> plot/export
```

On subsequent runs, if input unchanged, reuse cached matrices.

---

## Non-Negotiables
- General static and dynamic solvers.
- No duplicated solver logic by structure type.
- No solver math in UI or plotting.
- Preserve sign conventions and intermediate outputs.
- Result objects are dataclasses; solvers populate them completely before returning.
