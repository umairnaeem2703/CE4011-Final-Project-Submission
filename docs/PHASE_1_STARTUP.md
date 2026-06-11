# PHASE 1 STARTUP CHECKLIST

## What Phase 1 Does
Review/clean/verify `StructuralModel`, `Node`, `Element`, `Material`, `Section`, `Support`, `Load`, `LumpedMass`, `DOFManager`.

**Goal:** Correct DOF map, free/restrained DOF lists, dirty-state flag, reserved attributes for caching.

---

## Pre-Phase 1 Steps (15 minutes)

### 1. Review Current Code
- [ ] Read `src/parser.py` (current model classes)
- [ ] Read `src/dof_optimizer.py` (current DOFManager)
- [ ] Skim `Assignment3.md` for design philosophy
- [ ] Check `tests/` folder — do test files exist?

### 2. Verify Project Structure
```
Project root should have:
- src/
  - parser.py
  - dof_optimizer.py
  - element_physics.py
  - matrix_assembly.py
  - banded_solver.py
  - post_processor.py
  - main.py
  - etc.
- tests/
  - (test files, or create if missing)
- data/
  - Assignment_4_Q2a.xml
  - Assignment_4_Q2b.xml
- results/ (output folder)
```

If `tests/` doesn't exist, create it:
```bash
mkdir tests
touch tests/__init__.py
touch tests/test_model.py  (for Phase 1)
touch tests/test_static.py  (for Phase 2, empty for now)
```

### 3. Check Current Model Definition
In `src/parser.py`, verify these classes exist:
```python
@dataclass
class Node:
    id: int
    x: float
    y: float
    dofs: List[int] = field(default_factory=list)  # [dof_ux, dof_uy, dof_rz]

@dataclass
class StructuralModel:
    name: str = "Untitled"
    nodes: Dict[int, Node] = field(default_factory=dict)
    elements: Dict[str, Element] = field(default_factory=dict)
    supports: Dict[int, Support] = field(default_factory=dict)
    # ... etc
```

If `StructuralModel` is missing `is_dirty`, add stub:
```python
@dataclass
class StructuralModel:
    # ... existing fields ...
    is_dirty: bool = True  # Phase 1: Add this
    
    def mark_dirty(self):  # Phase 1: Add this method
        """Mark model as needing rebuild."""
        self.is_dirty = True
```

### 4. Run Existing Tests
```bash
cd /path/to/project
pytest tests/ -v
```

**Expected:** Either all pass, or you see which tests already exist.

---

## Phase 1 Completion Checklist

These 5 tests must all pass **and** be hand-verifiable in <5 minutes each.

### ✓ Test 1: Simple 2-Node Frame DOF Assignment
**What:** Fixed-pin portal frame.
**Expected:** Node 1 (fixed) = [-1, -1, -1], Node 2 (pin) = [0, 1, -1]

**Hand calculation:** 
- Node 1: 3 DOFs × 0 (fixed) = 0 active, so dofs = [-1, -1, -1]
- Node 2: 2 DOFs active (ux, uy), so dofs = [0, 1, -1]
- Total: 2 active DOFs

**Test code skeleton:**
```python
def test_simple_frame_dof_assignment():
    """2-node frame, node 1 fixed, node 2 pinned."""
    model = StructuralModel(name="simple_frame")
    # Create node 1 (fixed), node 2 (pin), frame element
    # Set support: node 1 fixed, node 2 pin
    optimizer = DOFOptimizer(model)
    num_eq, dof_map = optimizer.optimize()
    
    assert num_eq == 2, f"Expected 2 equations, got {num_eq}"
    assert dof_map[1] == [-1, -1, -1], "Node 1 should be fully fixed"
    assert dof_map[2] == [0, 1, -1], "Node 2 should be pinned (uy restrained)"
```

---

### ✓ Test 2: Rigid Diaphragm (Nodes on Same Floor Share UX)
**What:** 3-story building, all nodes per floor at same Y coordinate.
**Expected:** Nodes on floor 1 share dof_ux, but have unique dof_uy, dof_rz.

**Hand calculation:**
- Floor 1: Y=0, nodes A, B, C → master node A
  - Node A: dofs = [0, 1, 2] (active UX, UY, RZ)
  - Node B: dofs = [0, 3, 4] (shares UX from A, unique UY, RZ)
  - Node C: dofs = [0, 5, 6] (shares UX from A, unique UY, RZ)
- Total active DOFs: 7 (not 9)

**Test code skeleton:**
```python
def test_rigid_diaphragm_floor_sharing():
    """3 nodes on same floor share UX DOF."""
    model = StructuralModel()
    # Create 3 nodes at Y=0 (same floor)
    # Mark as rigid diaphragm (or auto-detect from Y-coordinate)
    optimizer = DOFOptimizer(model)
    num_eq, dof_map = optimizer.optimize()
    
    ux_a, ux_b, ux_c = dof_map[1][0], dof_map[2][0], dof_map[3][0]
    assert ux_a == ux_b == ux_c, "All nodes on floor should share UX"
    assert dof_map[1][1] != dof_map[2][1], "But UY should differ"
```

---

### ✓ Test 3: Axially Rigid Members Couple All DOFs
**What:** Two nodes connected by `is_axially_rigid=true` element.
**Expected:** Node j inherits all DOFs from node i.

**Hand calculation:**
- Node i: dofs = [0, 1, 2]
- Node j (slave): dofs = [0, 1, 2] (same as i)
- Total active: 3 DOFs

**Test code skeleton:**
```python
def test_axially_rigid_member_coupling():
    """Axially rigid member couples i and j DOFs."""
    model = StructuralModel()
    # Create 2 nodes, element with is_axially_rigid=True
    optimizer = DOFOptimizer(model)
    num_eq, dof_map = optimizer.optimize()
    
    dofs_i = dof_map[1]
    dofs_j = dof_map[2]
    assert dofs_i == dofs_j, "Slave node should inherit master DOFs"
```

---

### ✓ Test 4: Active Dynamic DOFs (Suppress Spinning Node)
**What:** Hinged frame with multiple members meeting at node → no rotational stiffness.
**Expected:** Spinning node's RZ is suppressed (not in active DOFs).

**Hand calculation:**
- Node with 3 hinged members = no moment continuity
- _has_rotational_stiffness() returns False
- dof_rz not assigned (stays -1)

**Test code skeleton:**
```python
def test_spinning_node_suppressed():
    """Multiple hinged members at free node → no rz DOF."""
    model = StructuralModel()
    # Create 3 frame members meeting at node 2 (all with release_end)
    # Node 2 is free (not supported)
    optimizer = DOFOptimizer(model)
    num_eq, dof_map = optimizer.optimize()
    
    dofs_node2 = dof_map[2]
    assert dofs_node2[2] == -1, "Spinning node should not have rz DOF"
```

---

### ✓ Test 5: Dirty State and Cache Clearing
**What:** Change node position, call `mark_dirty()`, verify caches cleared.
**Expected:** `is_dirty=True`, cached matrices are `None`.

**Hand calculation:**
- After mark_dirty(), cached_K, cached_M, cached_dof_map should all be None
- is_dirty should be True

**Test code skeleton:**
```python
def test_dirty_state_clears_cache():
    """Modifying model sets is_dirty=True and clears cached matrices."""
    model = StructuralModel()
    # ... setup model ...
    # Simulate cached matrices (in real Phase 2, these will be set)
    model.cached_K = [[1, 0], [0, 1]]  # dummy
    model.cached_dof_map = {1: [0, 1, 2]}  # dummy
    
    # Now modify and mark dirty
    model.nodes[1].x = 5.0  # change coordinate
    model.mark_dirty()
    
    assert model.is_dirty == True
    # In Phase 2, cached matrices will be explicitly cleared:
    assert model.cached_K is None or not model.is_dirty
```

---

## How to Run Phase 1 Task

### Step 1: Prepare
- Copy patched `AGENTS.md`, `ARCHITECTURE.md`, `MATH_SPEC.md`, `PROJECT_ROADMAP.md` to your project root.
- Read AGENTS.md section "Pre-Task Checklist."

### Step 2: Use Pre-Task Checklist (2 min)
- [ ] Phase 0 (docs) done? Yes (you just read them)
- [ ] Modified files: parser.py, dof_optimizer.py, tests/test_model.py (3 files ✓)
- [ ] Read-only files: Assignment3.md (context) (1 file ✓)
- [ ] In scope? Yes, Phase 1 = model/DOF layer only (no solver touched) ✓
- [ ] Tests exist? Yes, 5 tests defined above ✓

### Step 3: Create Phase 1 Task Prompt
Use this template:

```markdown
Read AGENTS.md, ARCHITECTURE.md, MATH_SPEC.md.
Task: PHASE 1 — Core Model + DOFs

Pre-Task Checklist:
- [x] Phase 0 complete (docs reviewed)
- [x] Modified files: src/parser.py, src/dof_optimizer.py, tests/test_model.py
- [x] Read-only files: Assignment3.md
- [x] In scope: Model & DOF layer only (no solver changes)
- [x] Tests exist: 5 completion tests defined below

Expected outputs:
1. test_simple_frame_dof_assignment — 2-node fixed-pin frame
2. test_rigid_diaphragm_floor_sharing — 3 nodes share UX
3. test_axially_rigid_member_coupling — all DOFs coupled
4. test_spinning_node_suppressed — hinged node has no rz
5. test_dirty_state_clears_cache — is_dirty flag works

Run relevant tests. Report changed files + test results in <=10 bullets.
```

### Step 4: After Task Completes
Run:
```bash
pytest tests/test_model.py -v
```

**All 5 tests must pass.** If any fail, use AGENTS.md "Abort/Revert" rule:
- Do not proceed to Phase 2
- Revert changes
- Request sub-task clarification
- Do one sub-task per prompt

---

## Quick Reference: What Phase 1 Should NOT Touch

❌ Do not modify `element_physics.py` (Phase 2)
❌ Do not modify `matrix_assembly.py` (Phase 2)
❌ Do not modify `banded_solver.py` (Phase 2)
❌ Do not modify `visualizer.py` (Phase 7)
❌ Do not add sparse/numpy dependencies (violates AGENTS.md)

---

## Quick Reference: What Phase 1 SHOULD Add/Fix

✅ Add `is_dirty: bool = True` to `StructuralModel`
✅ Add `mark_dirty()` method to `StructuralModel`
✅ Add reserved cache attributes (see ARCHITECTURE.md):
```python
cached_dof_map: dict = None
cached_K: list = None
cached_M: list = None
# ... etc
```
✅ Verify `DOFManager.optimize()` returns `(num_equations, dof_map, free_dofs, restrained_dofs)`
✅ Create `tests/test_model.py` with 5 completion tests
✅ Ensure all 5 tests pass

---

## When Phase 1 is Complete

You will have:
- ✅ Clean model dataclasses with dirty-state tracking
- ✅ Correct DOF assignment (free, restrained, coupled, diaphragm)
- ✅ 5 passing tests that hand-verify in <5 min each
- ✅ Reserved attributes for caching (Phase 2+ will populate)
- ✅ Ready to move to Phase 2 (Static Engine)

**Estimated time:** 1–2 Codex prompts (should be small, self-contained phase).

---

## Questions Before Starting?

- Do you have existing test files? (If yes, where?)
- Is your current `DOFManager` in a separate file, or inside parser.py?
- Do you already track dirty state in your model?

**Answer these before the first Phase 1 prompt** — saves revision loops.
