# PROJECT_ROADMAP.md

## Goal
Build a complete but incremental CE 4011 structural analysis program:
```text
OOP model -> static/modal/RSA/THA solvers -> visualization -> Streamlit UI -> docs/tests
```

## Development Rule
One phase at a time. One Codex task = one feature/subsystem + tests + changed-file summary.

---

## Phase 0: Stabilize Docs/Repo ✓ IN PROGRESS

**What:** Review and finalize AGENTS.md, ARCHITECTURE.md, MATH_SPEC.md, TEST_PLAN.md, PROJECT_ROADMAP.md.

**Done when:**
- [ ] All 5 docs committed to project root
- [ ] ARCHITECTURE.md includes result dataclass sketches
- [ ] AGENTS.md includes pre-task checklist and abort criteria
- [ ] MATH_SPEC.md includes RSA coupling formula

---

## Phase 1: Core Model + DOFs

**What:** Review/clean/verify `StructuralModel`, `Node`, `Element`, `Material`, `Section`, `Support`, `Load`, `LumpedMass`, `DOFManager`.

**Files to modify:**
- `src/parser.py` (model classes)
- `src/dof_optimizer.py` (DOFManager)
- (Maybe) `src/model/` folder (create if refactoring into submodule)

**Files to read (context only):**
- `Assignment3.md` (understand existing design)
- `main.py` (see how parser/DOF currently used)

### Phase 1 Complete When:

✓ **Test 1: Simple 2-node frame DOF assignment**
```
Create a 2-node fixed-pin frame.
Verify: 3 DOFs at node 1 (fixed), 2 DOFs at node 2 (pin).
Expected: dof_map = {1: [-1, -1, -1], 2: [0, 1, -1]}
```

✓ **Test 2: Rigid diaphragm (nodes on same floor share UX)**
```
Create 3-story shear frame, all nodes share Y per floor.
Verify: nodes 1,2,3 (floor 1) share dof_ux=0, but have independent dof_uy and dof_rz.
```

✓ **Test 3: Axially rigid members couple all DOFs**
```
Create 2 nodes connected by is_axially_rigid=true element.
Verify: node_j inherits all DOFs from node_i.
```

✓ **Test 4: Active dynamic DOFs (rotational stiffness check)**
```
Create hinged frame with multiple members at node.
Verify: spinning node is suppressed (rz not in active DOFs).
```

✓ **Test 5: Dirty state and caching (Phase 8 prep)**
```
Modify node position, call mark_dirty().
Verify: cached matrices are cleared.
```

**Dependency check:**
```python
def check_phase_1_complete():
    """Verify model and DOFManager are ready for Phase 2."""
    assert hasattr(StructuralModel, 'is_dirty'), "Dirty flag missing"
    assert hasattr(StructuralModel, 'mark_dirty'), "mark_dirty() missing"
    assert DOFManager returns (num_eq, dof_map, free_dofs, restrained_dofs)
```

---

## Phase 2: Static Engine

**What:** Implement/verify Frame/Truss stiffness, transformation, global K, boundary reduction, linear solve, reactions, element forces, N/V/M data.

**Files to modify:**
- `src/element_physics.py` (ensure local stiffness is correct)
- `src/matrix_assembly.py` (K assembly, boundary reduction)
- `src/banded_solver.py` (linear solver)
- `src/post_processor.py` (reactions, element forces)
- `src/results.py` (create StaticResults dataclass, see ARCHITECTURE.md)

**Files to read (context only):**
- `src/parser.py` (model structure)
- `Assignment3.md` (reference implementation)

### Phase 2 Complete When:

✓ **Test 1: Axial bar tip displacement (closed-form)**
```
Axial bar: P=10 kN, L=5 m, E=2e8 kN/m², A=0.01 m²
Expected u = PL/(EA) = 0.0025 m
Tolerance: <0.1%
```

✓ **Test 2: Cantilever beam tip deflection (Euler-Bernoulli)**
```
Cantilever: P=10 kN, L=3 m, E=2e8, I=1e-4 m⁴
Expected u_tip = PL³/(3EI) ≈ 0.0045 m
Tolerance: <1%
```

✓ **Test 3: Portal frame reactions (Assignment 3 benchmark)**
```
Run Assignment 3 Example 2 (portal frame).
Verify all reactions match within 2% vs SAP2000 reference.
```

✓ **Test 4: Member-end forces in local coordinates**
```
Extract N, V, M from a simply-supported beam with point load.
Verify moments at mid-span match textbook values.
Tolerance: <2%
```

✓ **Test 5: N/V/M diagram data structure**
```
Verify nvm_data contains axial, shear, moment arrays per element.
Visualize one element using visualizer.py.
```

**Dependency check:**
```python
def check_phase_2_complete(results_static):
    """Verify static solver produced correct outputs."""
    assert results_static.K is not None and len(results_static.K) > 0
    assert results_static.F is not None
    assert results_static.displacements is not None
    assert results_static.reactions is not None
    assert results_static.element_forces is not None
    assert results_static.nvm_data is not None
```

---

## Phase 3: Dynamic Assembly

**What:** Implement lumped mass assembly, damping assembly (Rayleigh), active dynamic DOFs, reduced system for THA/RSA.

**Files to modify:**
- `src/matrix_assembly.py` (add M and C assembly)
- `src/parser.py` (LumpedMass class, damping settings)
- `src/element_physics.py` (lumped mass per element)
- `src/results.py` (extend StaticResults or create DynamicAssemblyData)

**Files to read (context only):**
- `MATH_SPEC.md` (mass/damping formulae)
- Assignment 4 (if it uses M)

### Phase 3 Complete When:

✓ **Test 1: Lumped mass assembly for cantilever with point mass**
```
Cantilever L=3 m, E=2e8, I=1e-4.
Element mass: rho=7850 kg/m³, A=0.01 m²  → m_element ≈ 0.236 kg
Point mass at tip: 10 kg
Total: 10 + 0.118 = ~10.12 kg at tip DOF
Verify M[tip_uy, tip_uy] ≈ 10.118 kg
Tolerance: <1%
```

✓ **Test 2: Rayleigh damping coefficients**
```
Frame: omega_1 ≈ 10 rad/s, omega_2 ≈ 20 rad/s, zeta = 5%
Compute alpha, beta from MATH_SPEC formula.
Verify: C = alpha*M + beta*K produces target damping in modes 1 and 2.
```

✓ **Test 3: Active dynamic DOFs (exclude massless nodes)**
```
Frame with point masses at only 2 of 5 nodes.
Verify: active_dynamic_dofs only includes DOFs with mass.
```

✓ **Test 4: Reduced M, C, K for free DOFs**
```
Simple frame with 6 total DOFs, 3 restrained.
Verify Mff, Cff, Kff are 3×3 and correctly partitioned.
```

✓ **Test 5: Massless DOF static condensation reduces stiffness**
```
Create a 2-DOF spring system with one massless DOF coupled to a stiff DOF.
Verify: K_eff = Kaa - Kam Kmm^-1 Kma is smaller than the direct Kaa value,
         showing the condensed stiffness is the reduced dynamic stiffness.
```

✓ **Test 6: Density unit conversion (kg to tonne)**
```
Use rho = 7850 kg/m³ and convert to t/m³.
Verify: rho_tonne = 7.85 t/m³ (1 tonne = 1000 kg).
Ensure unit_system handling is consistent in dynamic assembly.
```

**Dependency check:**
```python
def check_phase_3_complete(model, assembly_data):
    """Verify mass and damping assembled before modal."""
    assert assembly_data.M is not None, "Mass matrix missing"
    assert assembly_data.Mff is not None, "Reduced M missing"
    assert len(assembly_data.M) == model.num_dofs
```

---

## Phase 4: Modal Solver

**What:** Generalized eigenvalue solver, frequencies/periods/modes, normalization, participation/effective mass.

**Files to modify:**
- `src/modal_solver.py` (or `src/modal_solver.py`)
- `src/results.py` (ModalResults dataclass from ARCHITECTURE.md)
- Add modal solver entry point in `src/main.py`

**Files to read (context only):**
- `MATH_SPEC.md` (modal equations, normalization)
- Assignment 4 (modal_solver.py reference)
- `src/matrix_assembly.py` (understand M, K assembly)

### Phase 4 Complete When:

✓ **Test 1: SDOF system (mass + spring)**
```
m=1 kg, k=100 N/m
Expected: omega = sqrt(k/m) = 10 rad/s, f = 1.592 Hz
Tolerance: <0.1%
```

✓ **Test 2: Cantilever first mode**
```
Cantilever L=1 m, E=2e8, I=1e-4, rho*A=100 kg/m
Compare first frequency to textbook approximation (λ₁ ≈ 3.516, ω = sqrt(λ₁²EI/m)).
Tolerance: <5%
```

✓ **Test 3: 3-story shear frame frequencies and mode shapes**
```
Run modal analysis, extract 3 periods.
Compare to Assignment 4 MATLAB reference or hand-calculation.
Verify: T₁ < T₂ < T₃
Tolerance: periods <2%, mode shapes visually match (scaled).
```

✓ **Test 4: Mass normalization**
```
Verify: phi_n^T * M * phi_n = 1.0 for all modes (within 1e-6).
```

✓ **Test 5: Participation factors and effective mass**
```
For horizontal excitation r = [1,0,0,1,0,0,...]:
Compute Gamma_n, M_eff,n.
Verify: sum(M_eff,n) ≈ total participating mass (r^T*M*r).
Tolerance: <1%
```

**Dependency check:**
```python
def check_phase_4_complete(results_modal):
    """Verify modal solver output structure."""
    assert len(results_modal.frequencies) > 0
    assert len(results_modal.periods) > 0
    assert len(results_modal.mode_shapes) > 0
    assert all(abs(modefreq) > 0 for modefreq in results_modal.frequencies)
    assert len(results_modal.participation_factors) == len(results_modal.frequencies)
```

---

## Phase 5: Ground Motion Input + Time-History Analysis (Newmark)

**What:** Newmark average acceleration solver, earthquake excitation, response histories (u, v, a, base shear, OTM), Convert user-selected acceleration units to internal solver units, Build excitation force history P(t) = -M r ag(t), Return THAResults.

**Files to modify:**

- src/ground_motion.py
- tests/test_time_history.py
- `src/newmark_solver.py` (create new file)
- `src/results.py` (THAResults dataclass)
- `src/main.py` (add THA entry point)

**Files to read (context only):**
- `MATH_SPEC.md` (Newmark equations, earthquake loading)
- Assignment 4 (if THA reference provided)

### Phase 5 Complete When:

✓ **Test 1: Read two-column time + acceleration file**
Input: time in column 1, acceleration in column 2, cm/s².
Verify time_vector, raw acceleration, dt, and acceleration_si.

✓ **Test 2: Read acceleration-only file with user dt**
Input: one acceleration value per line, dt = 0.004.
Verify generated time_vector length and spacing.

✓ **Test 3: Unit conversion and scale factor**
Verify:
1 g = 9.80665 m/s²
100 cm/s² = 1 m/s²
1000 mm/s² = 1 m/s²
scale_factor is applied after unit conversion.

✓ **Test 4: Earthquake force history**
For a simple mass matrix and r vector, verify:
P(t) = -M r ag(t).

✓ **Test 5: Newmark THA result histories and peaks**
Run a small SDOF or simple frame.
Verify displacement_history, velocity_history, acceleration_history, time_vector, peak values, dt, num_steps, and THAResults metadata.

**Dependency check:**
```python
def check_phase_5_complete(results_tha):
    """Verify THA output structure."""
    assert len(results_tha.time_vector) > 0
    assert len(results_tha.displacement_history) == len(results_tha.time_vector)
    assert len(results_tha.velocity_history) == len(results_tha.time_vector)
    assert len(results_tha.acceleration_history) == len(results_tha.time_vector)
    assert results_tha.peak_base_shear is not None
```

---

## Phase 6: Response Spectrum Analysis (RSA)

**What:** Spectrum interpolation, modal responses, SRSS/CQC combination, base shear/OTM.

**Files to modify:**
- `src/rsa_solver.py` (create new file)
- `src/results.py` (RSAResults dataclass)
- `src/main.py` (add RSA entry point)
- `src/core/interpolation.py` (1D spectrum interpolation utility, if not present)

**Files to read (context only):**
- `MATH_SPEC.md` (RSA and CQC formula)
- Assignment 4 (SeismoSignal reference, if available)

### Phase 6 Complete When:

✓ **Test 1: Spectrum interpolation**
```
Spectrum: T = [0, 0.5, 1, 2, 3], Sa = [0.1, 0.2, 0.3, 0.25, 0.15] g
Query: T=0.75 (between 0.5 and 1)
Expected (linear interp): Sa(0.75) ≈ 0.25 g
Tolerance: <0.01 g
```

✓ **Test 2: Modal response vectors (single mode)**
```
Mode 1: f₁=1 Hz, Gamma₁=0.5, phi₁ = [1, 0.5] (normalized)
Spectrum: Sa(1 Hz) = 0.3 g
Expected q₁_max = Gamma₁ * Sa / omega² ≈ 0.5 * 0.3 / (2π)²
         u₁_max = phi₁ * q₁_max
Tolerance: machine precision
```

✓ **Test 3: SRSS combination**
```
Two modes: R₁ = 10 mm, R₂ = 5 mm
Expected SRSS = sqrt(10² + 5²) ≈ 11.18 mm
Tolerance: machine precision
```

✓ **Test 4: CQC coupling coefficient (rho_ij)**
```
Modes: omega₁=1, omega₂=2 rad/s, zeta=5%
Compute rho_12 using MATH_SPEC formula.
Verify: 0 < rho_12 < 1 and symmetric (rho_ij = rho_ji).
```

✓ **Test 5: CQC combination**
```
Two modes: R₁=10, R₂=5, rho_12=0.6
Expected CQC = sqrt(R₁² + R₂² + 2*rho_12*R₁*R₂) ≈ 13.1
Compare to SRSS (11.18) — CQC should be larger for correlated modes.
Tolerance: machine precision
```

**Dependency check:**
```python
def check_phase_6_complete(results_rsa):
    """Verify RSA output structure."""
    assert len(results_rsa.periods) > 0
    assert len(results_rsa.spectrum_periods) > 0
    assert results_rsa.combined_response is not None
    assert results_rsa.combination_method in ["SRSS", "CQC"]
```

---

## Phase 7: Visualization

**What:** Use/adapt existing `visualizer.py`: preview, deformed shape, N/V/M, mode shapes, spectrum, THA histories.

**Files to modify:**
- `src/visualization/` (organize visualizer if needed)
- Update plot functions to consume result dataclasses (StaticResults, ModalResults, RSAResults, THAResults)

**Files to read (context only):**
- `src/visualizer.py` (existing implementation)
- AGENTS.md (preserve sign conventions)

### Phase 7 Complete When:

✓ **Test 1: Model preview (nodes, elements, supports)**
```
Plot simple frame on matplotlib.
Verify: nodes labeled, elements drawn, supports shown.
```

✓ **Test 2: Deformed shape with scale factor**
```
Plot undeformed + deformed frame from StaticResults.
Verify: deformed shape visually matches expected bending.
Verify: supports are fixed in place.
```

✓ **Test 3: N/V/M diagrams (color-coded)**
```
Plot N, V, M on three subplots for one frame.
Verify: positive regions green, negative red.
Verify: diagrams match nvm_data in StaticResults.
```

✓ **Test 4: Mode shape visualization**
```
Plot deformed geometry for mode 1 from ModalResults.
Verify: shape matches expected pattern (e.g., cantilever first mode = smooth curve).
Verify: scale reasonable (not too large/small).
```

✓ **Test 5: THA response history plots**
```
Plot u(t), v(t), a(t), V_base(t) from THAResults.
Verify: time axis labels correct.
Verify: y-axis units shown (m, m/s, m/s², kN, etc.).
```

---

## Phase 8: Streamlit UI

**What:** Input tables/forms, model preview, analysis run buttons, result tables, plots, export.

**Files to modify / create:**
- `src/ui/app.py` (main Streamlit app)
- `src/ui/pages/` (input, results, export pages)
- `src/io/export.py` (report generation)

**Files to read (context only):**
- ARCHITECTURE.md (StructuralModel.is_dirty, caching)
- All result dataclasses
- `src/visualization/`

### Phase 8 Complete When:

✓ **Test 1: Model input and validation**
```
User enters 2-node frame in table.
Verify: StructuralModel built correctly.
Verify: invalid input (zero-length element) rejected.
```

✓ **Test 2: Run static analysis button**
```
Click "Run Static", inspect results table.
Verify: displacements, reactions, member forces displayed.
Verify: no solver math in UI code (calls solver module only).
```

✓ **Test 3: Cached rebuild (dirty state)**
```
User changes load (mark dirty), runs static again.
Verify: DOFs not recomputed if geometry unchanged.
Verify: results updated (load changed).
```

✓ **Test 4: Plot display**
```
Run modal analysis, display mode 1 shape.
Verify: plot renders in Streamlit.
Verify: user can toggle between modes 1, 2, 3.
```

✓ **Test 5: Export report**
```
Generate PDF or text report with analysis summary.
Verify: includes DOF map, K/M matrices, eigenvalues, mode shapes, etc.
Verify: formatting is readable.
```

---

## Phase 9: Final Docs/Examples

**What:** Installation manual, user manual, example inputs/outputs, verification tables.

**Files to create:**
- `INSTALL.md` (Python version, dependencies, setup)
- `USER_MANUAL.md` (walkthrough with 1–2 complete examples)
- `docs/VERIFICATION.md` (benchmark comparisons vs SAP2000/MATLAB/textbook)
- `examples/` folder (sample XML files, expected outputs)

### Phase 9 Complete When:

✓ User can install and run from scratch without Codex prompts.
✓ At least 2 complete worked examples (truss, frame).
✓ All Assignment 3/4 test cases documented and passing.

---

## Codex Prompt Template (Use for Each Task)

```text
Read AGENTS.md, ARCHITECTURE.md, MATH_SPEC.md.
Task: <PHASE N — specific feature>

Pre-Task Checklist:
- [ ] Phase N-1 tests all pass
- [ ] Modified files: <list <=5 files>
- [ ] Read-only files: <list 1-3 files>
- [ ] Scope: <folder or module bounds>

Expected outputs:
- <test name 1>
- <test name 2>
- <test name 3>

Run relevant tests. Report changed files + results in <=10 bullets.
```

---

## Token Management Rules

- **Per phase:** Estimate 1–3 Codex prompts (smaller phases may need 1, larger may need 3).
- **If >3 prompts:** Revert changes, break into smaller sub-tasks.
- **Test early:** Write test first, then implement. Reduces revision loops.
- **Prefer small PRs:** Review and merge each phase before starting the next.

---

## Non-Negotiables
- General static and dynamic solvers.
- No duplicated solver logic by structure type.
- No solver math in UI or plotting.
- Preserve sign conventions and intermediate outputs.
