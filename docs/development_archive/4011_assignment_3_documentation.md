|              | CE 4011 | — Special  |     | Topics   | in Civil |
| ------------ | ------- | ---------- | --- | -------- | -------- |
| Engineering: |         | Structural |     | Analysis | Software |
Development
|     | Assignment | 3: Software     | Design     | Documentation    |         |
| --- | ---------- | --------------- | ---------- | ---------------- | ------- |
|     |            | Object-Oriented | Python     | Implementation   |         |
|     | Supporting | Frame,          | Truss, and | Mixed Structural | Systems |
|     |            | with Automated  | Stability  | Verification     |         |
|     |            | Name:           | Mohammad   | Umair Naeem      |         |
|     | Student    | ID:             | 2416055    |                  |         |
|     |            | Language:       | Python     |                  |         |
|     |            | Date:           | April 13,  | 2026             |         |

Contents
Contents
| 1 System | Overview |     | and Architecture |     |     |     | 1   |
| -------- | -------- | --- | ---------------- | --- | --- | --- | --- |
1.1 Purpose and Scope . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
1.2 Module Inventory . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1
| 2 Q1 | — Functional |     | Requirements |     | and Software | Design | 2   |
| ---- | ------------ | --- | ------------ | --- | ------------ | ------ | --- |
2.1 Object-Oriented Data Model . . . . . . . . . . . . . . . . . . . . . . . . 2
2.2 Frame and Truss Element Stiffness . . . . . . . . . . . . . . . . . . . . 2
2.3 Moment Releases — Static Condensation . . . . . . . . . . . . . . . . . 3
2.4 Fixed-End Forces for Member Loads . . . . . . . . . . . . . . . . . . . 3
2.5 Bandwidth Optimisation — Reverse Cuthill-McKee . . . . . . . . . . . 4
2.6 Global Matrix Assembly and Solver . . . . . . . . . . . . . . . . . . . . 4
2.7 Results Post-Processing and UML Class Diagram . . . . . . . . . . . . 5
| 3 Q2 | — Verification |     | and Testing |     | Strategy |     | 7   |
| ---- | -------------- | --- | ----------- | --- | -------- | --- | --- |
3.1 Testing Philosophy . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
3.2 Unit Tests (test_unit.py) . . . . . . . . . . . . . . . . . . . . . . . . 7
3.3 Interface Tests (test_interface.py) . . . . . . . . . . . . . . . . . . . 7
3.4 Regression Tests (test_regression.py) . . . . . . . . . . . . . . . . . 8
3.5 Test Execution Summary . . . . . . . . . . . . . . . . . . . . . . . . . . 10
| 4 Q3 | — Structural |     | Stability | and | Mechanism | Handling | 12  |
| ---- | ------------ | --- | --------- | --- | --------- | -------- | --- |
4.1 Two-Tier Safety Net . . . . . . . . . . . . . . . . . . . . . . . . . . . . 12
4.2 Topological Validator — Tier 1 . . . . . . . . . . . . . . . . . . . . . . 12
4.3 Error Test Cases (Q3a–Q3e) . . . . . . . . . . . . . . . . . . . . . . . . 13
4.4 Activity Diagram — Stability and Mechanism Handling . . . . . . . . . 17
| 5 Analysis      |     | and Design | Decisions |     |     |     | 18  |
| --------------- | --- | ---------- | --------- | --- | --- | --- | --- |
| 6 Assignment    |     | Summary    |           |     |     |     | 18  |
| A Supplementary |     |            | Material  |     |     |     | 19  |
A.1 Sequence Diagram — Core Analysis Workflow . . . . . . . . . . . . . . 20
A.2 SAP2000 Coordinate System Mapping . . . . . . . . . . . . . . . . . . 20
A.3 Sign Convention References . . . . . . . . . . . . . . . . . . . . . . . . 21
i

|         |         |          |       |     | Chapter |     | 1. System Overview | and Architecture |
| ------- | ------- | -------- | ----- | --- | ------- | --- | ------------------ | ---------------- |
| Chapter |         | 1        |       |     |         |     |                    |                  |
| System  |         | Overview |       |     | and     |     | Architecture       |                  |
| 1.1     | Purpose | and      | Scope |     |         |     |                    |                  |
This document is the software design documentation for a 2D structural analysis engine
built for CE 4011 Assignment 3. The engine solves plane frame, truss, and mixed frame-
truss structures using the Direct Stiffness Method (DSM). Structural models are
read from XML input files, analysed, and the results (nodal displacements, member-end
| forces, | support | reactions) | are | written | to a text | report. |     |     |
| ------- | ------- | ---------- | --- | ------- | --------- | ------- | --- | --- |
One key design choice was to avoid third-party numerical libraries entirely — no NumPy
or SciPy. All matrix operations are written from scratch using Python’s built-in lists,
mainly to show that the underlying algorithms are understood rather than just called.
| The | repository | is available | at: |     |     |     |     |     |
| --- | ---------- | ------------ | --- | --- | --- | --- | --- | --- |
https://github.com/umairnaeem2703/CE4011-Assignment-3-Submission
| 1.2 | Module | Inventory |     |     |     |     |     |     |
| --- | ------ | --------- | --- | --- | --- | --- | --- | --- |
The program is split into nine modules, each with a focused responsibility. Table 1.1
| gives | a brief | summary. |      |                |      |        |                   |              |
| ----- | ------- | -------- | ---- | -------------- | ---- | ------ | ----------------- | ------------ |
|       |         | Table    | 1.1: | Module summary |      | and    | responsibilities. |              |
|       | Module  |          |      | Responsibility |      |        |                   |              |
|       |         |          |      | Parses         | XML; | builds | all data-model    | dataclasses. |
parser.py
structural_validator.pyPre-solve topology checks (missing supports,
|     |                  |     |     | floating | members). |             |            |            |
| --- | ---------------- | --- | --- | -------- | --------- | ----------- | ---------- | ---------- |
|     | dof_optimizer.py |     |     | RCM      | node      | reordering; | active DOF | numbering. |
element_physics.py Local stiffness, FEF vectors, static condensation,
|     |                    |     |     | transformation, |     | force  | recovery.      |      |
| --- | ------------------ | --- | --- | --------------- | --- | ------ | -------------- | ---- |
|     | matrix_assembly.py |     |     | Assembles       |     | global | banded [K] and | {F}. |
banded_solver.py Banded Gaussian elimination with pivot moni-
toring.
1

|        |     | Chapter | 2. Q1          | — Functional | Requirements | and Software | Design |
| ------ | --- | ------- | -------------- | ------------ | ------------ | ------------ | ------ |
|        |     |         | Table 1.1      | (continued)  |              |              |        |
| Module |     |         | Responsibility |              |              |              |        |
post_processor.py Recovers member forces, reactions; writes re-
port.
| math_utils.py |     |     | Pure-Python | matrix              | utilities. |         |     |
| ------------- | --- | --- | ----------- | ------------------- | ---------- | ------- | --- |
| main.py       |     |     | Entry       | point; orchestrates | pipeline;  | handles | ex- |
ceptions.
| Chapter             | 2          |        |            |              |     |     |     |
| ------------------- | ---------- | ------ | ---------- | ------------ | --- | --- | --- |
| Q1 —                | Functional |        |            | Requirements |     |     | and |
| Software            |            | Design |            |              |     |     |     |
| 2.1 Object-Oriented |            |        | Data Model |              |     |     |     |
All input data is stored in Python dataclass structures defined in parser.py. Using
dataclasses enforces immutability after parsing and keeps the initialisation code clean.
Themainclassesare: Material(E),Section(A,I),Node(coordinates,assignedDOFs),
Element(unifiedfortruss/frame,withoptionalreleaseflags),Support(booleanrestraint
per DOF), PointLoad, UDL, MemberPointLoad, LoadCase, and StructuralModel (root
aggregate).
All models are described in an XML format governed by data/SCHEMA.xml. The schema
hierarchymirrorsthedataclasshierarchydirectly, whichkeepstheparserstraightforward.
Support types are specified as named shorthands (fixed, pin, roller_x, roller_y) or
asexplicitDOFflags. MemberloadsspecifytheirFEFconditionviathefef_condition
attribute so the solver never has to guess the boundary condition from context.
| 2.2 Frame | and | Truss | Element | Stiffness |     |     |     |
| --------- | --- | ----- | ------- | --------- | --- | --- | --- |
A truss element carries axial force only, with a 4×4 local stiffness matrix built entirely
from the axial term EA/L. The zero rows and columns for u and r are retained so
y z
that the same assembly and transformation routines apply uniformly to both element
types. A frame element carries axial force, shear, and bending moment in a 6 × 6
2

|     |     |     | Chapter |     | 2. Q1 — | Functional | Requirements |     | and | Software | Design |
| --- | --- | --- | ------- | --- | ------- | ---------- | ------------ | --- | --- | -------- | ------ |
Euler-Bernoulli stiffness matrix whose non-zero entries are formed from the terms EA/L,
12EI/L3, 6EI/L2, 4EI/L, and 2EI/L. The global element matrix is obtained via
[K] = [T]T[k] [T], where [T] is the standard rotation matrix using direction cosines
| e          | local |          |     |     |        |              |     |     |     |     |     |
| ---------- | ----- | -------- | --- | --- | ------ | ------------ | --- | --- | --- | --- | --- |
| c = ∆x/L   | and s | = ∆y/L.  |     |     |        |              |     |     |     |     |     |
| 2.3 Moment |       | Releases |     | —   | Static | Condensation |     |     |     |     |     |
Internal hinges are specified in the XML as <release end="i" dof="Mz"/>. The
element-level stiffness matrix is condensed before assembly using the Guyan (static
condensation) method. Partitioning into retained (r) and condensed (c) DOFs:
|     | ˆ      |     |      | ]−1[k |     | ˆ   |        |      | ]−1{f |     |       |
| --- | ------ | --- | ---- | ----- | --- | --- | ------ | ---- | ----- | --- | ----- |
|     | [k ] = | [k  | ]−[k | ][k   | ],  | {f  | } = {f | }−[k | ][k   | }   | (2.1) |
|     |        | rr  | rc   | cc    | cr  |     | r      | rc   | cc    | c   |       |
Setting {f } = {0} enforces zero moment at the hinge. The condensed matrix is
c
zero-padded back to 6×6 for compatibility with the global assembly loop. Doing this at
element level keeps the global system clean — there’s no need to track which equations
| to remove     | after | assembly. |        |     |        |     |       |     |     |     |     |
| ------------- | ----- | --------- | ------ | --- | ------ | --- | ----- | --- | --- | --- | --- |
| 2.4 Fixed-End |       |           | Forces | for | Member |     | Loads |     |     |     |     |
Member loads are converted to statically equivalent nodal forces using FEF formulae.
The sign convention: transverse reactions positive upward, end moments positive CCW;
| w and P | carry the   | algebraic |     | sign     | of the applied |     | load.        |         |           |     |     |
| ------- | ----------- | --------- | --- | -------- | -------------- | --- | ------------ | ------- | --------- | --- | --- |
|         | Table       | 2.1:      | FEF | formulae | for a          | UDL | of intensity | w       | over span | L.  |     |
|         | Condition   |           |     | F        | M              |     | F            | M       |           |     |     |
|         |             |           |     |          | y,i            | z,i | y,j          |         | z,j       |     |     |
|         |             |           |     |          | −wL2/12        |     |              | +wL2/12 |           |     |     |
|         | fixed-fixed |           |     | wL/2     |                |     | wL/2         |         |           |     |     |
+wL2/8
|     | pin-fixed |     |     | 3wL/8 | 0      |     | 5wL/8 |     |     |     |     |
| --- | --------- | --- | --- | ----- | ------ | --- | ----- | --- | --- | --- | --- |
|     | fixed-pin |     |     | 5wL/8 | −wL2/8 |     | 3wL/8 | 0   |     |     |     |
|     | pin-pin   |     |     | wL/2  | 0      |     | wL/2  | 0   |     |     |     |
For a concentrated member load P at distance a from node_i (with b = L−a), the
|             |      |     |     | Pb2(3a | b)/L3 |     |     | Pab2/L2. |     |           |       |
| ----------- | ---- | --- | --- | ------ | ----- | --- | --- | -------- | --- | --------- | ----- |
| fixed-fixed | FEFs | are | F = |        | +     | and | M   | =        |     | The other | three |
|             |      |     | y,i |        |       |     | z,i |          |     |           |       |
boundary conditions follow analogously. The axial component of any member load is
| split proportionally |     | between |     | the | two end nodes. |     |     |     |     |     |     |
| -------------------- | --- | ------- | --- | --- | -------------- | --- | --- | --- | --- | --- | --- |
3

|               |     |     | Chapter      |     | 2. Q1 | — Functional | Requirements |               | and Software | Design |
| ------------- | --- | --- | ------------ | --- | ----- | ------------ | ------------ | ------------- | ------------ | ------ |
| 2.5 Bandwidth |     |     | Optimisation |     |       | — Reverse    |              | Cuthill-McKee |              |        |
Tokeepthebandedsolverefficient, theDOFOptimizerreordersnodesusingtheReverse
Cuthill-McKee (RCM) algorithm: build an adjacency graph from active nodes, start
from the lowest-degree node, run BFS expanding neighbours by ascending degree, then
reverse the BFS sequence. DOFs are then assigned in this order. For the 26-element
truss in Test 1, RCM reduced the semi-bandwidth from 14 to approximately 5, cutting
| stored values | from | 196 | to 70 | — a | 64% | reduction. |     |     |     |     |
| ------------- | ---- | --- | ----- | --- | --- | ---------- | --- | --- | --- | --- |
A subtle case arises when multiple hinged frame members meet at a free node with no
moment-continuous connection: the rotational DOF has zero stiffness. The method
_has_rotational_stiffness() checks for this and suppresses the spinning DOF so it
| never enters | the | global | system. |          |     |     |        |     |     |     |
| ------------ | --- | ------ | ------- | -------- | --- | --- | ------ | --- | --- | --- |
| 2.6 Global   |     | Matrix |         | Assembly |     | and | Solver |     |     |     |
MatrixAssembler.assemble() iterates over all elements in one pass: compute local
stiffness and FEF, apply static condensation if needed, rotate to global coordinates,
then scatter into the upper-triangular banded matrix. FEFs are subtracted from the
| load vector: | {F} | =   | {P}   | −{FEF}. |     |     |     |     |     |     |
| ------------ | --- | --- | ----- | ------- | --- | --- | --- | --- | --- | --- |
|              |     | net | nodal |         |     |     |     |     |     |     |
BandedSolver then solves [K]{D} = {F} using in-place banded Gaussian elimination.
For each pivot row k, the multiplier is ℓ = K /K and elimination is restricted to
|     |     |     |     |     |     | ik ki | kk  |     |     |     |
| --- | --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- |
the semi-bandwidth m. Back-substitution follows. At each step, the diagonal pivot is
monitored:
|     | if  | |K  | | < 1×10−10 |     | :   | raise UnstableStructureError |     |     |     | (2.2) |
| --- | --- | --- | ----------- | --- | --- | ---------------------------- | --- | --- | --- | ----- |
kk
This threshold sits well above machine epsilon (≈ 2.2×10−16) but far below any physical
stiffness value, so it reliably catches true zero-energy modes without false positives.
| if abs(pivot) |     | <   | 1e-10: |     |     |     |     |     |     |     |
| ------------- | --- | --- | ------ | --- | --- | --- | --- | --- | --- | --- |
1
| 2 raise | UnstableStructureError( |      |      |           |     |             |            |     |                 |     |
| ------- | ----------------------- | ---- | ---- | --------- | --- | ----------- | ---------- | --- | --------------- | --- |
| 3       | f"Mechanism             |      |      | detected! |     | Instability | found      |     | at Equation/DOF |     |
|         |                         | {k}. | "    |           |     |             |            |     |                 |     |
| 4       | "Ensure                 |      | your | structure |     | is fully    | restrained |     | and adequately  |     |
braced."
5 )
|     |     | Listing | 2.1: | Pivot | check | in banded_solver.py. |     |     |     |     |
| --- | --- | ------- | ---- | ----- | ----- | -------------------- | --- | --- | --- | --- |
4

|     |         |                 | Chapter | 2. Q1 | — Functional |     | Requirements | and Software | Design |
| --- | ------- | --------------- | ------- | ----- | ------------ | --- | ------------ | ------------ | ------ |
| 2.7 | Results | Post-Processing |         |       | and          | UML | Class        | Diagram      |        |
PostProcessor reconstructs the full nodal displacement vector (inserting zeros for
| restrained | DOFs) | then | recovers | member-end |     | forces: |     |     |     |
| ---------- | ----- | ---- | -------- | ---------- | --- | ------- | --- | --- | --- |
ˆ
|     |     | {f′} | = [k′]{d′} | +{f | } , | {d′} | = [T]{d} |          | (2.3) |
| --- | --- | ---- | ---------- | --- | --- | ---- | -------- | -------- | ----- |
|     |     |      | e c        | e   | e   |      | e        | e,global |       |
Support reactions are computed by back-transforming element local forces and summing
contributions at each support node, then subtracting any applied nodal loads.
The class structure is shown in the full-page UML diagram below.
5

Figure 2.1: UML Class Diagram showing all data-model classes, analysis classes, and their relationships.

|         |                |     | Chapter | 3. Q2 — Verification | and Testing | Strategy |
| ------- | -------------- | --- | ------- | -------------------- | ----------- | -------- |
| Chapter | 3              |     |         |                      |             |          |
| Q2      | — Verification |     | and     | Testing              | Strat-      |          |
egy
| 3.1 Testing | Philosophy |     |     |     |     |     |
| ----------- | ---------- | --- | --- | --- | --- | --- |
The verification strategy follows three tiers: unit tests validate individual physics cal-
culations in isolation; interface tests check that module boundaries integrate correctly;
regression tests confirm end-to-end numerical accuracy against SAP2000 v16.1.1.
All tests use Python’s built-in unittest framework. Numerical tolerances are δ =
D
1×10−3 m (displacement) and δ = 0.5 kN (force/moment), which accounts for the
F
minor difference between the Euler-Bernoulli DSM formulation and SAP2000’s default
| Timoshenko | beam model.    |                |                 |     |     |     |
| ---------- | -------------- | -------------- | --------------- | --- | --- | --- |
| 3.2 Unit   | Tests          | (test_unit.py) |                 |     |     |     |
| Three unit | tests directly | exercise       | ElementPhysics. |     |     |     |
Test 1 — Local Stiffness Matrix. For a frame element with E = 2×108 kN/m2,
A = 0.01 m2, I = 10−4 m4, L = 5 m, the expected shear stiffness is 12EI/L3 =
1920 kN/m and rotational stiffness 4EI/L = 16000 kN·m/rad. Both values are verified
| with assertAlmostEqual(..., |     | places=3). |     |     |     |     |
| --------------------------- | --- | ---------- | --- | --- | --- | --- |
Test 2 — Fixed-End Forces. Thesameelementwithw = −10kN/m(fixed-fixed)
y
should give F = −25 kN and M = −20.833 kN·m. Both values are verified.
|     | y,i |     | z,i |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
Test 3 — Coordinate Transformation. An inclined element from (0,0) to (3,4)
gives c = 0.6, s = 0.8. A local axial force of 10 kN transforms to global components
| F = 6.0       | kN, F = 8.0 | kN. Verified        | with assertAlmostEqual. |     |     |     |
| ------------- | ----------- | ------------------- | ----------------------- | --- | --- | --- |
| x             | y           |                     |                         |     |     |     |
| 3.3 Interface | Tests       | (test_interface.py) |                         |     |     |     |
Interface tests check using a minimal two-element truss model built
MatrixAssembler
programmatically. With EA/L = 2 × 106 kN/m per element, Node 2’s u diagonal
x
|     | 4×106 |     |     |     |     | 2×106 |
| --- | ----- | --- | --- | --- | --- | ----- |
should be (contributions from both elements) and Node 3’s u diagonal
x
(one element only). The off-diagonal coupling between them should be −2×106 kN/m.
A second test adds a vertical frame element with a UDL and checks that the FEF
contribution appears correctly in the global load vector at the expected DOF positions.
7

|     |            |     |       | Chapter              | 3. Q2 | — Verification | and Testing |     | Strategy |
| --- | ---------- | --- | ----- | -------------------- | ----- | -------------- | ----------- | --- | -------- |
| 3.4 | Regression |     | Tests | (test_regression.py) |       |                |             |     |          |
Regression tests run the full pipeline end-to-end on three example structures and
compare against SAP2000 exports. A _parse_sap2000() helper applies the coordinate
mapping U → u , U → u , and R → −r (sign-inverted to match CCW convention).
|       | 1          | x   | 3 y    | 2 z                |     |       |       |     |     |
| ----- | ---------- | --- | ------ | ------------------ | --- | ----- | ----- | --- | --- |
| 3.4.1 | Regression |     | Test 1 | — 5-Panel X-Braced |     | Pratt | Truss |     |     |
A 26-member truss, 20 m span, 4 m height, pin at Node 1 and roller at Node 6. Two
−5 kN loads at top-chord nodes. Key results are compared in Table 3.1.
Figure 3.1: SAP2000 model: 5-panel Pratt truss with applied point loads at top chord.
|          | Table | 3.1: | Regression | Test 1: SAP2000 |         | vs. solver | comparison. |     |       |
| -------- | ----- | ---- | ---------- | --------------- | ------- | ---------- | ----------- | --- | ----- |
| Quantity |       |      | Location   |                 | SAP2000 |            | Solver      |     | Pass? |
✓
| Reaction | F   |     | Node | 1   | 5.000 | kN  | 5.000 kN |     |     |
| -------- | --- | --- | ---- | --- | ----- | --- | -------- | --- | --- |
y
| Displacement |     | u   | Node | 9   | −0.012236m≈ |     | −0.012236 | m   | ✓   |
| ------------ | --- | --- | ---- | --- | ----------- | --- | --------- | --- | --- |
y
| Axial | force | T1  | Node | 1 end | 2.739 | kN  | ≈2.739 | kN  | ✓   |
| ----- | ----- | --- | ---- | ----- | ----- | --- | ------ | --- | --- |
✓
| Axial | force      | T11 | Node   | 1 end          | 10.478 | kN       | ≈10.478 | kN  |     |
| ----- | ---------- | --- | ------ | -------------- | ------ | -------- | ------- | --- | --- |
| 3.4.2 | Regression |     | Test 2 | — Portal Frame | with   | Diagonal | Brace   |     |     |
A 4-member 2D frame (columns 3 m, beam 4 m, diagonal brace), pin at Node 1, roller
| at Node | 4, combined |     | lateral-vertical | loading. |     |     |     |     |     |
| ------- | ----------- | --- | ---------------- | -------- | --- | --- | --- | --- | --- |
8

|     |     |     |     | Chapter | 3. Q2 | — Verification | and | Testing | Strategy |
| --- | --- | --- | --- | ------- | ----- | -------------- | --- | ------- | -------- |
Figure 3.2: SAP2000 model: portal frame with diagonal brace and combined lateral-
| vertical | loading. |      |            |                 |           |        |             |     |       |
| -------- | -------- | ---- | ---------- | --------------- | --------- | ------ | ----------- | --- | ----- |
|          | Table    | 3.2: | Regression | Test 2: SAP2000 | vs.       | solver | comparison. |     |       |
| Quantity |          |      | Location   |                 | SAP2000   |        | Solver      |     | Pass? |
| Reaction | F        |      | Node       | 1               | −20.000kN |        | ≈ −20.000   | kN  | ✓     |
x
✓
| Reaction | F   |     | Node | 4   | 25.000 | kN  | ≈25.000 | kN  |     |
| -------- | --- | --- | ---- | --- | ------ | --- | ------- | --- | --- |
y
| Displacement |     | u   | Node | 2   | 0.032005m |     | ≈0.032005 | m   | ✓   |
| ------------ | --- | --- | ---- | --- | --------- | --- | --------- | --- | --- |
x
| Moment | M   | F1  | Node | 1 end | −3.536kN·m≈ |     | −3.536 | kN·m | ✓   |
| ------ | --- | --- | ---- | ----- | ----------- | --- | ------ | ---- | --- |
i
✓
| Shear | F1         |     | Both   | stations            | 14.371 | kN        | ≈14.371 | kN  |     |
| ----- | ---------- | --- | ------ | ------------------- | ------ | --------- | ------- | --- | --- |
| 3.4.3 | Regression |     | Test 3 | — Mixed Frame-Truss |        | Structure |         |     |     |
A four-span continuous beam (fixed at both ends) supported at two intermediate points
by inclined truss members, with a member point load at mid-span of segment F2.
9

|     |     |     |     | Chapter |     | 3. Q2 | — Verification |     | and | Testing | Strategy |
| --- | --- | --- | --- | ------- | --- | ----- | -------------- | --- | --- | ------- | -------- |
Figure 3.3: SAP2000 model: continuous beam with inclined truss supports and member
point load.
|          | Table | 3.3: Regression |          | Test     | 3: SAP2000 |          | vs. solver | comparison. |        |     |       |
| -------- | ----- | --------------- | -------- | -------- | ---------- | -------- | ---------- | ----------- | ------ | --- | ----- |
| Quantity |       |                 | Location |          |            | SAP2000  |            |             | Solver |     | Pass? |
| Reaction | F     |                 | Node     | 1 (fixed | end        | −4.603kN |            | ≈           | −4.603 | kN  | ✓     |
x
a)
✓
| Reaction | F   |     | Node | 1   |     | −5.948kN |     | ≈   | −5.948 | kN  |     |
| -------- | --- | --- | ---- | --- | --- | -------- | --- | --- | ------ | --- | --- |
y
| Moment | reaction | M   | Node | 1   |     | 23.530kN·m |     | ≈23.530 |     | kN·m | ✓   |
| ------ | -------- | --- | ---- | --- | --- | ---------- | --- | ------- | --- | ---- | --- |
z
✓
| Axial | force T1, | T2  | Both | truss |     | −18.414kN |     | ≈   | −18.414 | kN  |     |
| ----- | --------- | --- | ---- | ----- | --- | --------- | --- | --- | ------- | --- | --- |
members
| Moment | M F1 |     | Node | 2 end |     | −47.843kN·m≈ |     | −47.843 |     | kN·m | ✓   |
| ------ | ---- | --- | ---- | ----- | --- | ------------ | --- | ------- | --- | ---- | --- |
j
| 3.5 Test | Execution |       | Summary |          |      |       |          |     |          |     |        |
| -------- | --------- | ----- | ------- | -------- | ---- | ----- | -------- | --- | -------- | --- | ------ |
|          |           | Table | 3.4:    | Complete | test | suite | summary. |     |          |     |        |
| File     |           | Test  | Name    |          |      |       | Type     |     | Verified |     | Status |
Against
✓
| test_unit.py |     | test_local_k_standard_ |     |     |     |     | Unit |     | Analytical |     |     |
| ------------ | --- | ---------------------- | --- | --- | --- | --- | ---- | --- | ---------- | --- | --- |
frame
✓
|     |     | test_fef_uniform_ |     |     |     |     | Unit |     | Analytical |     |     |
| --- | --- | ----------------- | --- | --- | --- | --- | ---- | --- | ---------- | --- | --- |
distributed_load
|     |     | test_transformation_matrix |     |     |     |     | Unit |     | Analytical |     | ✓   |
| --- | --- | -------------------------- | --- | --- | --- | --- | ---- | --- | ---------- | --- | --- |
10

|      |           | Chapter   | 3. Q2       | — Verification | and Testing | Strategy |
| ---- | --------- | --------- | ----------- | -------------- | ----------- | -------- |
|      |           | Table 3.4 | (continued) |                |             |          |
| File | Test Name |           |             | Type           | Verified    | Status   |
Against
✓
| test_        | test_assembly_global_ |     |     | Interface | Analytical |     |
| ------------ | --------------------- | --- | --- | --------- | ---------- | --- |
| interface.py | stiffness_mapping     |     |     |           |            |     |
✓
|     | test_assembly_global_load_ |     |     | Interface | Analytical |     |
| --- | -------------------------- | --- | --- | --------- | ---------- | --- |
vector
| test_ | test_regression_01_truss |     |     | Regression | SAP2000 | ✓   |
| ----- | ------------------------ | --- | --- | ---------- | ------- | --- |
regression.py
|     | test_regression_02_frame |     |     | Regression | SAP2000 | ✓   |
| --- | ------------------------ | --- | --- | ---------- | ------- | --- |
✓
|     | test_regression_03_mixed |                |              | Regression | SAP2000 |     |
| --- | ------------------------ | -------------- | ------------ | ---------- | ------- | --- |
|     | Figure                   | 3.4: Unit      | test console | outputs.   |         |     |
|     | Figure                   | 3.5: Interface | test console | outputs.   |         |     |
|     | Figure 3.6:              | Regression     | test console | outputs.   |         |     |
11

|              |            |        | Chapter | 4. Q3 | — Structural |     | Stability | and Mechanism |       | Handling |
| ------------ | ---------- | ------ | ------- | ----- | ------------ | --- | --------- | ------------- | ----- | -------- |
| Chapter      | 4          |        |         |       |              |     |           |               |       |          |
| Q3 —         | Structural |        |         |       | Stability    |     |           | and           | Mech- |          |
| anism        | Handling   |        |         |       |              |     |           |               |       |          |
| 4.1 Two-Tier |            | Safety | Net     |       |              |     |           |               |       |          |
The engine uses a two-tier instability detection system to catch problems before they
| produce silent | wrong | answers: |     |     |     |     |     |     |     |     |
| -------------- | ----- | -------- | --- | --- | --- | --- | --- | --- | --- | --- |
1. Tier 1 — Topological Pre-Solver Validation (StructuralValidator): runs
after DOF assignment, before any matrix is built. Catches configurations that are
| structurally | unsolvable |     | from geometry |     | alone. |     |     |     |     |     |
| ------------ | ---------- | --- | ------------- | --- | ------ | --- | --- | --- | --- | --- |
2. Tier 2 — Numerical In-Solver Monitoring (BandedSolver): checks diagonal
pivots during Gaussian elimination. Catches instabilities that topology cannot
| predict, | such as | mechanisms | from | hinge | configurations. |     |     |     |     |     |
| -------- | ------- | ---------- | ---- | ----- | --------------- | --- | --- | --- | --- | --- |
Both tiers raise UnstableStructureError, which propagates to main.py for a clean
| error message                  | and | graceful | exit.     |      |       |        |           |     |     |     |
| ------------------------------ | --- | -------- | --------- | ---- | ----- | ------ | --------- | --- | --- | --- |
| 4.2 Topological                |     |          | Validator | —    | Tier  | 1      |           |     |     |     |
| StructuralValidator.validate() |     |          |           | runs | three | checks | in order: |     |     |     |
Check 1 — Zero Supports. If the supports list is empty the stiffness matrix is
rank-deficient by at least three rigid body modes. Detected immediately.
Check 2 — Missing Horizontal Restraint. If no support has restrain_ux =
the structure can sway freely. This catches the classic roller-roller error (Q3a).
True
Check 3 — Floating Sub-Structures. An adjacency graph is built from element
connectivity. BFS identifies connected components; any component with no supported
node is a floating sub-structure. The offending member IDs are listed in the error
message.
| 1 for component |                  | in  | components: |                     |     |     |     |        |            |     |
| --------------- | ---------------- | --- | ----------- | ------------------- | --- | --- | --- | ------ | ---------- | --- |
|                 |                  |     | any(n       | in                  |     |     |     | for in |            |     |
| 2 has_support   |                  | =   |             | self.model.supports |     |     |     | n      | component) |     |
| if              | not has_support: |     |             |                     |     |     |     |        |            |     |
3
|     | floating_members |     |     | = sorted( |     |     |     |     |     |     |
| --- | ---------------- | --- | --- | --------- | --- | --- | --- | --- | --- | --- |
4
|     | el.id |     | for el | in self.model.elements.values() |     |     |     |     |     |     |
| --- | ----- | --- | ------ | ------------------------------- | --- | --- | --- | --- | --- | --- |
5
|     | if  | el.node_i.id |     | in  | component |     | or el.node_j.id |     | in  |     |
| --- | --- | ------------ | --- | --- | --------- | --- | --------------- | --- | --- | --- |
6
component
12

|     |                      |                | Chapter  |      | 4. Q3                      | — Structural  | Stability and | Mechanism |      | Handling |
| --- | -------------------- | -------------- | -------- | ---- | -------------------------- | ------------- | ------------- | --------- | ---- | -------- |
| 7   | )                    |                |          |      |                            |               |               |           |      |          |
| 8   | fatal_errors.append( |                |          |      |                            |               |               |           |      |          |
| 9   |                      | f"Member(s)    |          | [{’, | ’.join(floating_members)}] |               |               |           | form | a        |
|     |                      |                | floating | "    |                            |               |               |           |      |          |
|     |                      | "sub-structure |          |      | with                       | no supports." |               |           |      |          |
10
)
11
Listing 4.1: BFS floating sub-structure check in structural_validator.py.
| 4.3      | Error  | Test          | Cases | (Q3a–Q3e) |        |       |     |     |     |     |
| -------- | ------ | ------------- | ----- | --------- | ------ | ----- | --- | --- | --- | --- |
| Five XML | models | exercise      | all   | detection | paths. |       |     |     |     |     |
| 4.3.1    | Q3a —  | Roller-Roller |       | Portal    |        | Frame |     |     |     |     |
A 3-member portal frame with roller_x at both base nodes. No support restrains the
x-direction, so the frame can sway freely under the 10 kN lateral load. Caught by Tier
| 1, Check | 2.     |      |      |               |     |              |              |     |        |     |
| -------- | ------ | ---- | ---- | ------------- | --- | ------------ | ------------ | --- | ------ | --- |
|          | Figure | 4.1: | Q3a: | Roller-roller |     | portal frame | — structural |     | model. |     |
Figure 4.2: Q3a: Console output showing detected instability — no horizontal restraint.
| 4.3.2 | Q3b — | Disconnected |     |     | Columns | (Floating | Sub-Structure) |     |     |     |
| ----- | ----- | ------------ | --- | --- | ------- | --------- | -------------- | --- | --- | --- |
Two vertical columns share no elements or supports — the right column (F2, Nodes
3–4) has no supports at all. Caught by Tier 1, Check 3; F2 is identified as the floating
member.
13

|     |             | Chapter | 4. Q3        | — Structural | Stability and | Mechanism | Handling |
| --- | ----------- | ------- | ------------ | ------------ | ------------- | --------- | -------- |
|     | Figure 4.3: | Q3b:    | Disconnected | columns      | — structural  | model.    |          |
Figure 4.4: Q3b: Console output — floating sub-structure detected for member F2.
| 4.3.3 Q3c | — L-Frame | and | Cantilever | Column | (Stable) |     |     |
| --------- | --------- | --- | ---------- | ------ | -------- | --- | --- |
Two disconnected but independently supported sub-structures. The validator prints:
“INFO: 2 disconnected sub-structures detected. All parts are independently supported
| and solvable.” | Analysis | proceeds | normally. |     |     |     |     |
| -------------- | -------- | -------- | --------- | --- | --- | --- | --- |
Figure 4.5: Q3c: L-frame and cantilever column — stable disconnected structure.
14

|     |     | Chapter | 4. Q3 — | Structural Stability | and Mechanism | Handling |
| --- | --- | ------- | ------- | -------------------- | ------------- | -------- |
Figure 4.6: Q3c: Console output — both sub-structures solved successfully.
| 4.3.4 Q3d | — A-Frame | Truss | (Properly | Supported) |     |     |
| --------- | --------- | ----- | --------- | ---------- | --- | --- |
Two truss members meeting at an apex node, pins at both base nodes. The structure is
determinate and both translational rigid body modes are eliminated. Solves correctly,
confirming correct handling of minimal truss support conditions.
|     | Figure | 4.7: Q3d: | A-frame truss | — properly | supported. |     |
| --- | ------ | --------- | ------------- | ---------- | ---------- | --- |
Figure 4.8: Q3d: Console output — A-frame truss solved successfully.
15

|           |              | Chapter | 4. Q3 — Structural | Stability and | Mechanism | Handling |
| --------- | ------------ | ------- | ------------------ | ------------- | --------- | -------- |
| 4.3.5 Q3e | — Three-Span | Beam    | with Internal      | Hinge         |           |          |
A three-span beam with an end-j release on element E2 (hinge at Node 3 side of span
2–3). Element E3 connects from Node 3 without a release, so Node 3 retains rotational
stiffness through E3 and a spinning node singularity is avoided. Static condensation
| correctly reduces | E2 to | a 5-DOF | element. The |     |     | check |
| ----------------- | ----- | ------- | ------------ | --- | --- | ----- |
_has_rotational_stiffness()
| confirms this | before DOF | assignment. |     |     |     |     |
| ------------- | ---------- | ----------- | --- | --- | --- | --- |
Figure 4.9: Q3e: Three-span beam with internal hinge — structural model.
Figure 4.10: Q3e: Console output — internal hinge handled correctly via static
condensation.
16

|              | Chapter | 4. Q3 — Structural | Stability and | Mechanism | Handling |
| ------------ | ------- | ------------------ | ------------- | --------- | -------- |
| 4.4 Activity | Diagram | — Stability        | and Mechanism | Handling  |          |
Figure 4.11: Activity Diagram: Structural Stability Verification and Mechanism Han-
dling.
17

|          |     |     |        | Chapter   | 6. Assignment | Summary |
| -------- | --- | --- | ------ | --------- | ------------- | ------- |
| Chapter  | 5   |     |        |           |               |         |
| Analysis |     | and | Design | Decisions |               |         |
Memory-Efficient Banded Storage. Storingonlytheuppertriangleofthesymmetric
global stiffness matrix in a banded array saves significant memory. For a system with N
N2
active equations and semi-bandwidth m, storage goes from (full) to N×m (banded).
For the 26-member truss in Test 1 (N = 14, m ≈ 5), this gives 70 stored values versus
196 — a 64% saving. For larger structures the savings grow quadratically since m ≪ N
| in typical | structural | models. |     |     |     |     |
| ---------- | ---------- | ------- | --- | --- | --- | --- |
Numerical Tolerance for Pivot Detection. The pivot threshold of 1 × 10−10
10−16)
sits well above machine epsilon (≈ 2.2 × but far below any realistic stiffness
value (103–109 kN/m). This prevents false positives from floating-point round-off in
well-conditioned systems while still reliably catching true zero-energy modes.
FEF Condition Decoupling. The fef_condition attribute in the XML explicitly
tells the solver which FEF formula to use, rather than having the solver try to infer
the boundary condition from the element’s neighbourhood. This avoids ambiguity in
complex models and matches the decision process used in manual matrix analysis.
Unified Element Dataclass. A single Element dataclass handles both truss and
frame elements via the type attribute. ElementPhysics dispatches on this attribute
internally. This avoids a class hierarchy for elements and simplifies the assembly loop,
| which      | does not need | to know | the element type | ahead of time. |     |     |
| ---------- | ------------- | ------- | ---------------- | -------------- | --- | --- |
| Chapter    | 6             |         |                  |                |     |     |
| Assignment |               |         | Summary          |                |     |     |
This assignment delivered a fully self-contained, object-oriented Python 3 engine for two-
dimensional structural analysis using the Direct Stiffness Method. The key contributions
| are summarised | below. |     |     |     |     |     |
| -------------- | ------ | --- | --- | --- | --- | --- |
Software Architecture. The codebase is structured as a six-stage linear pipeline
— parsing, validation, DOF optimisation, matrix assembly, banded solving, and post-
processing — with each stage encapsulated in a dedicated class. All inter-module
communication passes through well-defined data-model dataclasses, ensuring clean
18

|            |             |                  | Appendix | A. Supplementary | Material |
| ---------- | ----------- | ---------------- | -------- | ---------------- | -------- |
| separation | of concerns | and testability. |          |                  |          |
Element Physics. Both Euler-Bernoulli frame elements (6-DOF, 6×6 stiffness matrix)
and axial truss elements (4-DOF, 4×4 stiffness matrix) are supported within a single,
unified formulation. Coordinate transformation, Fixed-End Force derivation for UDLs
and member point loads, and static condensation for internal moment releases (Guyan
reduction) are all implemented from first principles without external libraries.
Bandwidth Optimisation. The Reverse Cuthill-McKee algorithm reorders nodes
to minimise the semi-bandwidth, enabling the global stiffness matrix to be stored and
solved as a compact banded array. For typical structural models this reduces memory
| usage by | 60–90% compared | to full-matrix | storage. |     |     |
| -------- | --------------- | -------------- | -------- | --- | --- |
Stability Detection. A two-tier safety net catches instabilities before they produce
silent incorrect results. Tier 1 (topological) identifies missing horizontal restraints and
floating sub-structures prior to assembly. Tier 2 (numerical) monitors diagonal pivots
during Gaussian elimination and raises UnstableStructureError at the first near-zero
pivot, reliably detecting mechanisms that topology analysis alone cannot identify.
Verification. Three regression tests against SAP2000 v16.1.1 — covering a 26-member
Pratt truss, a portal frame with diagonal brace, and a mixed frame-truss beam —
confirm numerical accuracy within 10−3 m for displacements and 0.5 kN for forces. Five
Q3 error-case models systematically exercise every instability detection path.
| Appendix      | A   |          |     |     |     |
| ------------- | --- | -------- | --- | --- | --- |
| Supplementary |     | Material |     |     |     |
19

|     |          |     |         |        | Appendix | A.       | Supplementary | Material |
| --- | -------- | --- | ------- | ------ | -------- | -------- | ------------- | -------- |
| A.1 | Sequence |     | Diagram | — Core | Analysis | Workflow |               |          |
Figure A.1: UML Sequence Diagram showing inter-module message flow for a complete
analysis run, including the alt block for UnstableStructureError.
| A.2 | SAP2000 |     | Coordinate | System | Mapping |     |     |     |
| --- | ------- | --- | ---------- | ------ | ------- | --- | --- | --- |
SAP2000usesa3DXZ-planeconvention. The_parse_sap2000()methodintest_regression.py
applies the following mapping to align with the solver’s 2D x-y convention:
|     |         | Table     | A.1: SAP2000 | to solver | coordinate     | mapping. |         |     |
| --- | ------- | --------- | ------------ | --------- | -------------- | -------- | ------- | --- |
|     | SAP2000 |           |              | Solver    | Notes          |          |         |     |
|     | U       | (global   | X)           | u         | Direct map     |          |         |     |
|     | 1       |           |              | x         |                |          |         |     |
|     | U       | (global   | Z)           | u         | Direct map     |          |         |     |
|     | 3       |           |              | y         |                |          |         |     |
|     | R       | (rotation | about Y)     | −r        | Sign inversion | (CW      | vs CCW) |     |
|     | 2       |           |              | z         |                |          |         |     |
20

|     |         |                       | Appendix | A. Supplementary | Material |
| --- | ------- | --------------------- | -------- | ---------------- | -------- |
|     |         | Table A.1 (continued) |          |                  |          |
|     | SAP2000 | Solver Notes          |          |                  |          |
|     | F       | F Direct              | map      |                  |          |
1 x
|     | F   | F Direct | map |     |     |
| --- | --- | -------- | --- | --- | --- |
3 y
|     | M   | −M Sign | inversion |     |     |
| --- | --- | ------- | --------- | --- | --- |
2 z
| A.3 | Sign Convention | References |     |     |     |
| --- | --------------- | ---------- | --- | --- | --- |
Global axes: x horizontal (positive right), y vertical (positive up), r rotation posi-
z
tive CCW. Element local axes run from node_i to node_j. Frame DOF ordering is
[u , u , r , u , u , r ]T; truss elements use [u , u , u , u ]T. All units are
| x,i y,i | z,i x,j y,j | z,j | x,i y,i | x,j y,j |     |
| ------- | ----------- | --- | ------- | ------- | --- |
| kN and  | metres.     |     |         |         |     |
All FEF computations in element_physics.py treat w and P as signed quantities
(negative for downward loads). The FEF vector components are positive in the local
element coordinate directions: F and F positive upward in local y; M and M
|     |     | y,i y,j |     |     | z,i z,j |
| --- | --- | ------- | --- | --- | ------- |
positive CCW. FEFs are subtracted from the applied load vector during assembly:
| {F} | = {P} −{FEF}. |     |     |     |     |
| --- | ------------- | --- | --- | --- | --- |
| net | nodal         |     |     |     |     |
21