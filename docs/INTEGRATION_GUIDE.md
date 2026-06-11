# Integration Guide: Patched Documentation + Phase 1 Startup

## What You Got

6 files in `/mnt/user-data/outputs/`:

| File | Size | Purpose |
|------|------|---------|
| **AGENTS.md** | 3.2 KB | Execution discipline: pre-task checklist, abort criteria, quick tests |
| **ARCHITECTURE.md** | 6.8 KB | Dataclass contracts, reserved model attributes, dependency checks |
| **MATH_SPEC.md** | 8.5 KB | Complete math + CQC formula + phase labels + outputs per phase |
| **PROJECT_ROADMAP.md** | 15.2 KB | 9 phases with specific completion tests, sub-task examples, token rules |
| **PATCH_SUMMARY.md** | 4 KB | What changed, why, how to use it |
| **PHASE_1_STARTUP.md** | 6 KB | Phase 1 checklist, 5 completion tests, quick reference |

---

## Integration Steps (5 minutes)

### 1. Backup Your Current Docs
```bash
cd /path/to/project
cp AGENTS.md AGENTS.md.backup
cp ARCHITECTURE.md ARCHITECTURE.md.backup
cp MATH_SPEC.md MATH_SPEC.md.backup
cp PROJECT_ROADMAP.md PROJECT_ROADMAP.md.backup
```

### 2. Copy Patched Files
```bash
cp /mnt/user-data/outputs/AGENTS.md .
cp /mnt/user-data/outputs/ARCHITECTURE.md .
cp /mnt/user-data/outputs/MATH_SPEC.md .
cp /mnt/user-data/outputs/PROJECT_ROADMAP.md .
```

### 3. Keep Helper Docs Handy
```bash
# Copy to your project for reference (not mission-critical)
cp /mnt/user-data/outputs/PATCH_SUMMARY.md docs/  (or keep in project root)
cp /mnt/user-data/outputs/PHASE_1_STARTUP.md docs/
```

### 4. Commit
```bash
git add AGENTS.md ARCHITECTURE.md MATH_SPEC.md PROJECT_ROADMAP.md
git commit -m "docs: patch agent guidance with phase gates, dataclass contracts, execution discipline"
```

---

## Pre-Phase 1 Actions (20 minutes)

### 1. Read PHASE_1_STARTUP.md
Go through "Pre-Phase 1 Steps" section (15 min):
- [ ] Review src/parser.py, src/dof_optimizer.py
- [ ] Create tests/ folder if missing
- [ ] Add stub `is_dirty` and `mark_dirty()` to StructuralModel if missing
- [ ] Verify DOFManager returns correct tuple format
- [ ] Run existing tests to see baseline

### 2. Quick Code Review: Your Current Model
Check your `StructuralModel` definition:
```python
# Does this exist?
@dataclass
class StructuralModel:
    # ... existing fields ...
    is_dirty: bool = True              # <-- ADD IF MISSING
    cached_dof_map: dict = None        # <-- ADD IF MISSING
    cached_K: list = None              # <-- ADD IF MISSING
    cached_M: list = None              # <-- ADD IF MISSING
    
    def mark_dirty(self):              # <-- ADD IF MISSING
        """Mark model as needing rebuild."""
        self.is_dirty = True
```

If missing, add these lines now (takes 2 min).

### 3. Create tests/test_model.py
Copy the skeleton code from PHASE_1_STARTUP.md section "Phase 1 Completion Checklist" into a new file:
```bash
touch tests/test_model.py
# Copy the 5 test skeletons from PHASE_1_STARTUP.md
```

---

## Using the Documentation Effectively

### AGENTS.md (Read First When Starting Any Task)
- **Pre-Task Checklist** (2 min) — use EVERY time before a Codex prompt
  - Do not skip; costs 2 min, saves 2 hours of rework
- **Abort/Revert Criteria** — if stuck after 3 attempts, revert and split task
- **Quick Test Rule** — ensures tests are hand-verifiable and fast
- **Relevant Tests Definition** — clarifies which tests to run (not everything)

### ARCHITECTURE.md (Reference When Defining Results)
- **Result Dataclass Sketches** — shows what each solver produces
  - StaticResults (Phase 2): K/F/displacements/reactions/NVM
  - ModalResults (Phase 4): eigenvalues/frequencies/modes/participation
  - RSAResults (Phase 6): spectrum/modal responses/combined/CQC
  - THAResults (Phase 5): time histories/peak quantities
- **Reserved Model Attributes** — future-proofs StructuralModel for all phases
- **Dependency Checks** — code snippets for phase-to-phase validation

### MATH_SPEC.md (Reference for Physics Implementation)
- All equations for static/modal/RSA/THA
- **CQC Coupling Coefficient** now documented (was missing)
- **Phase labels** show when each equation applies
- **Outputs section** specifies what each phase produces

### PROJECT_ROADMAP.md (Your Execution Plan)
- **Phases 1–9** — overall timeline
- **Phase N Completion Tests** — specific gates (5 tests per phase)
- **Codex Prompt Template** — use when writing prompts
- **Token Management Rules** — 1–3 prompts per phase; if >3, revert & split

### PATCH_SUMMARY.md (What Changed & Why)
- Read if curious about improvements
- Reference if things seem unfamiliar

### PHASE_1_STARTUP.md (Your Next Action)
- Read entire file (10 min)
- Complete pre-Phase 1 checklist (20 min)
- When ready, write Phase 1 task prompt using template at end

---

## Sample First Phase 1 Prompt

**Use this template when you're ready to start Phase 1:**

```markdown
I'm ready to start Phase 1 (Core Model + DOFs).

Read AGENTS.md, ARCHITECTURE.md, MATH_SPEC.md.

## Pre-Task Checklist
- [x] Phase 0 complete (docs reviewed and committed)
- [x] Modified files: src/parser.py, src/dof_optimizer.py, tests/test_model.py (3 files)
- [x] Read-only files: Assignment3.md (for context)
- [x] In scope: Model & DOF layer only
- [x] Tests defined: 5 completion tests in PHASE_1_STARTUP.md

## Current Status
[DESCRIBE YOUR CURRENT MODEL STRUCTURE]
- Does StructuralModel already have is_dirty? [YES/NO]
- Does DOFManager.optimize() return (num_eq, dof_map, free_dofs, restrained_dofs)? [YES/NO]
- Do test files exist in tests/? [YES/NO]
- Are there existing Assignment 3 tests I should ensure pass? [YES/NO + LIST]

## Task
Implement/fix Phase 1 to pass these 5 completion tests:
1. test_simple_frame_dof_assignment
2. test_rigid_diaphragm_floor_sharing
3. test_axially_rigid_member_coupling
4. test_spinning_node_suppressed
5. test_dirty_state_clears_cache

Preserve all existing Phase 2+ solver code (no modifications).

## Expected Output
- Phase 1 completion tests all pass
- tests/test_model.py contains 5 passing tests
- StructuralModel has is_dirty, mark_dirty(), reserved cache attributes
- No new dependencies introduced

## Questions
[ANSWER THE "CURRENT STATUS" QUESTIONS ABOVE]
```

---

## How Codex Will Help From Here

When you use this prompt, Codex will:

1. **Follow Pre-Task Checklist** (2 min review)
2. **Implement Phase 1** — clean model/DOF layer
3. **Write 5 focused tests** — hand-checkable in <5 min each
4. **Run tests** — verify they all pass
5. **Report changes** in ≤10 bullets:
   - Files modified: src/parser.py, src/dof_optimizer.py, tests/test_model.py
   - Added: is_dirty flag, mark_dirty() method, 5 completion tests
   - Tests passing: all 5 ✓
   - Token usage: estimate

---

## After Phase 1 Passes

1. **Run full test suite:**
   ```bash
   pytest tests/test_model.py -v
   ```

2. **Commit:**
   ```bash
   git commit -m "feat: Phase 1 - Core model with DOF management and dirty-state tracking"
   ```

3. **Move to Phase 2** using PROJECT_ROADMAP.md "Phase 2: Static Engine" section
   - Follow same pattern: read docs, use pre-task checklist, write prompt, run tests

---

## Token Budget Estimate

- **Phase 1:** 1–2 Codex prompts (small, self-contained)
- **Phase 2:** 1–2 prompts (static assembly + solver)
- **Phase 3:** 1 prompt (mass/damping assembly)
- **Phase 4:** 2–3 prompts (modal is complex)
- **Phase 5:** 2 prompts (Newmark THA)
- **Phase 6:** 2 prompts (RSA + CQC)
- **Phase 7:** 1–2 prompts (visualization)
- **Phase 8:** 2–3 prompts (Streamlit UI)
- **Phase 9:** 1 prompt (docs/examples)

**Total estimate:** 13–18 prompts across all phases (vs. infinite without structure).

With abort/revert rule, if any phase exceeds 3 prompts, you split and retry. This caps wasteful loops.

---

## You're Ready!

**Next action:**
1. Copy 4 patched .md files to project root ✓
2. Read PHASE_1_STARTUP.md (10 min) ✓
3. Complete pre-Phase 1 checklist (20 min)
4. Write Phase 1 prompt (5 min)
5. Run Phase 1 task (1–2 Codex prompts)
6. Move to Phase 2

**Good luck! You have a solid plan now.**

If you hit a snag, re-read AGENTS.md "Abort/Revert Criteria" — designed to get you unstuck fast.
