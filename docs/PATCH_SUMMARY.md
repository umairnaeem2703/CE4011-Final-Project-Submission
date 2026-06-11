# Documentation Patch Summary

## Overview
Updated 4 core agent guidance documents to address critical gaps identified during code review. Focus: execution discipline, phase completion gates, and result object contracts.

---

## Changes by File

### 1. AGENTS.md
**Added:**
- **Pre-Task Checklist (2 min)** — stops bad starts before they waste tokens
  - Phase N-1 tests pass?
  - Modified files list (<5)
  - Read-only context files (1-3)
  - Scope check (stay within phase bounds)
  - Test definition exists?

- **Abort/Revert Criteria** — breaks thrashing loops
  - If >3 prompts on one task → STOP
  - Revert to last pass state
  - Break into smaller sub-tasks
  - Do one sub-task per prompt
  - Only then continue

- **Quick Test Rule** — prevents token sprawl in testing
  - <20 lines setup
  - Closed-form reference or <1-page hand calc
  - Single logical assertion (or <5)
  - Runtime <0.5 sec

- **Relevant Tests Definition** — clarifies which tests to run
  - Run tests for modified files + dependent modules
  - Example: change modal_solver → test_modal* + test_dynamic_assembly
  - Do NOT re-run full suite unless explicitly asked

**Preserved:** All existing rules (architecture, dependency, layer, required outputs).

---

### 2. ARCHITECTURE.md
**Added:**
- **Result Object Contracts** — prevents mid-phase architecture surprises
  - `StaticResults` dataclass sketch (Phase 2)
    - K/Kff, F/Ff, displacements, reactions, element forces, NVM data, DOF map
  - `ModalResults` dataclass sketch (Phase 4)
    - K/M, eigenvalues, frequencies, periods, mode shapes, modal masses, participation factors, effective masses, influence vector, total mass
  - `RSAResults` dataclass sketch (Phase 6)
    - Spectrum, modal responses (before/after combination), SRSS/CQC, base shear/OTM, damping ratio, rho matrix
  - `THAResults` dataclass sketch (Phase 5)
    - Time vector, excitation/force histories, displacement/velocity/acceleration histories, base shear/OTM histories, peak quantities, step table, Newmark parameters

- **Reserved Model Attributes** — future-proofs StructuralModel
  - `is_dirty` (bool) — rebuild marker for Phase 8
  - Cached matrices: `cached_K`, `cached_M`, `cached_C`, `cached_dof_map`, `cached_F/Ff`
  - `mark_dirty()` method
  - Dynamic assembly settings: damping model, Rayleigh alpha/beta
  - THA settings: excitation file, direction, time step, num steps

- **Dependency Checks** — gives example code for phase-to-phase validation
  - Phase 3 → Phase 4 check (M assembled?)
  - Phase 4 → Phase 6 check (modal results exist?)

- **UI Flow (Phase 8 preview)** — shows caching/rebuild logic

**Preserved:** All existing layer/solver/non-negotiables rules.

---

### 3. MATH_SPEC.md
**Added:**
- **CQC Coupling Coefficient (Chopra formula)** — was missing from original
  ```
  rho_ij = (8*zeta²*sqrt(1-zeta²)*(r_ij + 4*zeta²*r_ij³)) / 
           ((1-r_ij²)² + 4*zeta²*r_ij²*(1+r_ij²))
  where r_ij = omega_i / omega_j
  ```
  Includes edge case (omega_i == omega_j → rho_ij = 1.0)

- **Phase labels on major sections** — clarifies when each math topic applies
  - Phase 2: Stiffness, Assembly, Static, Element recovery
  - Phase 3: Mass, Damping
  - Phase 4: Modal
  - Phase 5: Newmark, Earthquake excitation
  - Phase 6: RSA, Spectrum, Combination

- **Output/Outputs sections** — specifies what each phase produces
  - Static: displacements, reactions, element forces, N/V/M data
  - Modal: eigenvalues, frequencies, periods, modes, modal masses, participation, effective masses
  - RSA: spectrum, modal vectors, combined response via SRSS/CQC, base shear/OTM
  - THA: time vector, excitation/force history, u/v/a histories, base shear/OTM histories, peak quantities, optional step table

**Preserved:** All existing equations and sign conventions.

---

### 4. PROJECT_ROADMAP.md
**Added:**
- **Phase 0 (Stabilize Docs)** — formal completion checkpoint
  - Verify 5 docs committed
  - Verify dataclass sketches in place
  - Verify AGENTS.md has checklist/abort
  - Verify MATH_SPEC.md has RSA formula

- **Specific Phase Completion Tests** — gates, not vague requirements
  - Each phase lists 5 "Complete When" tests
  - Each test is <5 min hand-calculable reference
  - Example Phase 1 Test 1: 2-node frame DOF assignment
    ```
    Expected: dof_map = {1: [-1, -1, -1], 2: [0, 1, -1]}
    Tolerance: exact match
    ```
  - Example Phase 2 Test 1: Axial bar (closed-form u = PL/EA)
    ```
    Tolerance: <0.1%
    ```
  - Example Phase 4 Test 2: Cantilever first mode
    ```
    Tolerance: <5% vs textbook
    ```

- **Dependency Checks** — code snippets for phase-to-phase validation
  - Each phase has a `check_phase_N_complete()` assertion block
  - Used between phases to prevent silent failures

- **Sub-task Breakdown Example** — shows how to revert if stuck
  - Phase 5 (THA) example: if stuck after 3 attempts
    - Revert modal_solver.py
    - Prompt 1: eigenvalue solver only on SDOF
    - Prompt 2: mode shape normalization on cantilever
    - Prompt 3: participation factors on 3-story frame

- **Codex Prompt Template** — fills in AGENTS.md template for each phase
  - Read X, Y, Z docs
  - Checklist: Phase N-1? File lists? Scope? Tests?
  - Expected outputs: test names
  - Run relevant tests
  - Report <=10 bullets

- **Token Management Rules** — phase-specific guidance
  - Per phase: estimate 1–3 prompts
  - If >3 prompts: revert, break smaller, one sub-task per prompt
  - Test early to reduce revision loops

---

## How to Use

### For Phase 1 Startup

1. **Read all 4 patched files** (10 min)
2. **Verify your current codebase:**
   - Does `StructuralModel` have `is_dirty` attribute? (Add stub if missing)
   - Does `DOFManager` return `(num_eq, dof_map, free_dofs, restrained_dofs)`? (Verify signature)
   - Do test files exist in `tests/`? (Create if missing)
3. **Use the Phase 1 "Complete When" checklist** — these are your gates
4. **For each Codex prompt**, use the **Pre-Task Checklist** (2 min) before writing the prompt

### For Future Phases

- Do not skip the pre-task checklist.
- If a prompt needs >3 revisions, revert and break into sub-tasks.
- Use the phase-specific completion tests to verify before moving on.
- Use dependency checks between phases to catch integration issues early.

---

## Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Execution clarity** | "Phase 2 is done" — unclear | 5 specific tests that must pass |
| **Abort criteria** | None; could thrash indefinitely | >3 attempts → revert & split |
| **Result objects** | Undefined; solver doesn't know what to output | Dataclass sketches in ARCHITECTURE.md |
| **Test scope** | "Run relevant tests" — ambiguous | Explicit rule: modified files + dependents |
| **Phase dependencies** | Implicit; errors silent | Dependency check code snippets |
| **Token control** | No limits; could spiral | Estimate 1–3 prompts/phase, abort if exceeded |

---

## Files Ready to Use

All patched files are in `/mnt/user-data/outputs/`:
- `AGENTS.md` (3.2 KB) — execution discipline
- `ARCHITECTURE.md` (6.8 KB) — dataclass contracts + model structure
- `MATH_SPEC.md` (8.5 KB) — complete math + RSA formula + phase labels
- `PROJECT_ROADMAP.md` (15.2 KB) — phase gates + completion tests + sub-task examples

**Next step:** Copy these to your project root (overwrite existing .md files).

---

## What's NOT Changed

- Core architecture rules (solver generalization, layer separation, no numpy in core)
- MATH_SPEC physics (all equations remain unchanged)
- Visualization philosophy (adapt visualizer.py, don't rewrite)
- Testing philosophy (hand-computable, small tests)

These remain your north star; the patches add **discipline** and **checkpoints**.
