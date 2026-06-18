CE 4011
| Special    | Topics         | in Civil    | Engineering |        |
| ---------- | -------------- | ----------- | ----------- | ------ |
| Structural | Analysis       | Software    | Development |        |
|            | Assignment     |             | #4          |        |
| Software   | Implementation |             |             | Report |
|            | Structural     | FEA         | Solver      |        |
|            | Feature        | Extensions  |             |        |
|            | Student        | Information |             |        |
| Name:      | Mohammad       | Umair       | Naeem       |        |
|            | Student        | ID:         |             |        |
2416055
| Term: | Spring     | Semester, | 2025(cid:21)2026 |     |
| ----- | ---------- | --------- | ---------------- | --- |
|       | Department | of Civil  | Engineering      |     |

| Assignment | #4  |     |     |     | CE 4011 | - Structural | Analysis Software |
| ---------- | --- | --- | --- | --- | ------- | ------------ | ----------------- |
1 Introduction
This report documents the design, implementation, and validation of the Assignment #4
structural FEA solver extension, developed for CE 4011 (cid:22) Structural Analysis Software
Development. The primary contributions of this assignment are the addition of two ad-
vanced loading capabilities to the existing 2D frame/truss solver: (1) thermal loading, en-
compassing both uniform temperature changes and linear thermal gradients across cross-
sections, and (2) support settlement analysis, enabling prescribed nodal displacements
to be incorporated as kinematic boundary conditions in the global system. The imple-
mentation follows an object-oriented design philosophy, introducing a new TemperatureL
load class, an extended Support dataclass, and a matrix partitioning solver strategy. All
results have been rigorously validated against the industry-standard SAP2000 FEA soft-
ware for two benchmark problems (Q2a: settlement case, Q2b: thermal loading case).
A comprehensive testing suite (cid:22) including unit tests, interface tests, and backward-
compatibility regression tests (cid:22) con(cid:28)rms correctness and reliability.
All assignment source code, XML input (cid:28)les, and test scripts are publicly available at
| the following | GitHub | repository: |     |     |     |     |     |
| ------------- | ------ | ----------- | --- | --- | --- | --- | --- |
https://github.com/umairnaeem2703/CE4011-Assignment-4-Submission
| 2 Revisions     |     | to the | Core | Architecture |         |                 |     |
| --------------- | --- | ------ | ---- | ------------ | ------- | --------------- | --- |
| 2.1 Motivation: |     | Static | XML  | to           | Dynamic | Class Structure |     |
The foundation of the Assignment #4 enhancements lies in a fundamental architectural
transitionfrompurelystaticXMLinputde(cid:28)nitionstoarobust, extensibleobject-oriented
datamodel. Theoriginalimplementationreliedon(cid:28)xedXMLattributestoencodeFixed-
End Force (FEF) conditions directly, which limited expressivity and scalability.
| 2.2 The       | FEF | Decoupling  | Strategy   |     |     |     |     |
| ------------- | --- | ----------- | ---------- | --- | --- | --- | --- |
| 2.2.1 Problem |     | with Static | Attributes |     |     |     |     |
In the previous design, thermal and settlement e(cid:27)ects were scattered across rigid XML
schemas. Fixed-End Forces (FEF) were computed as static, immutable properties of
elements(cid:22)(cid:28)xed at parse time with no dynamic reconciliation or extension mechanism.
| 2.2.2 Solution: |     | Specialized | TemperatureL |     | Class |     |     |
| --------------- | --- | ----------- | ------------ | --- | ----- | --- | --- |
To address this, the refactored architecture introduces a specialized TemperatureL class
that inherits from the abstract MemberLoad base class. This decoupling brings several
critical advantages:
(cid:136)
Single Responsibility: Thermal FEF logic is isolated in a dedicated class.
(cid:136) Extensibility: New load types (e.g., soil pressure, humidity e(cid:27)ects) can be added
| without | modifying | core | element | physics. |     |     |     |
| ------- | --------- | ---- | ------- | -------- | --- | --- | --- |
(cid:136)
| Testability: |     | Thermal | calculations | are | independently | veri(cid:28)able. |     |
| ------------ | --- | ------- | ------------ | --- | ------------- | ----------------- | --- |
(cid:136)
Mathematical Clarity: The physics is explicitly codi(cid:28)ed in the FEF() method.
1

| Assignment |          | #4  |     |     |        |      | CE         | 4011 | - Structural | Analysis Software |
| ---------- | -------- | --- | --- | --- | ------ | ---- | ---------- | ---- | ------------ | ----------------- |
| 2.3        | Enhanced |     |     | XML | Parser | with | Expressive |      | Tags         |                   |
The new XML schema supports richer semantics through dedicated <support> and
| <load> | tags: |     |     |     |     |     |     |     |     |     |
| ------ | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:136) SupportElement: Encapsulatesbothrestraint(cid:29)ags(restrain_ux,restrain_uy,
restrain_rz) and prescribed settlement values (settlement_ux, settlement_uy,
settlement_rz).
(cid:136)
LoadElement: Polymorphicallyinstantiatestheappropriateloadclass(NodalLoad,
|     | PointLoad, |     | UniformlyDL, |     | TemperatureL). |     |     |     |     |     |
| --- | ---------- | --- | ------------ | --- | -------------- | --- | --- | --- | --- | --- |
This design enables the parser to dynamically construct the correct object graph at
runtime, respecting the inheritance hierarchy and enabling polymorphic load assembly.
| 2.4 | Domain       |       | Model       |         | Class      | Hierarchy |            |         |            |     |
| --- | ------------ | ----- | ----------- | ------- | ---------- | --------- | ---------- | ------- | ---------- | --- |
| The | domain       | model | now         | cleanly | separates: |           |            |         |            |     |
|     | 1. Geometric |       | Entities:   |         | Material,  | Section,  | Node,      | Element |            |     |
|     | 2. Boundary  |       | Conditions: |         | Support    | (with     | settlement |         | extension) |     |
3. Load Hierarchy: AbstractLoadclasswithconcreteimplementations(NodalLoad,
|     | PointLoad,   |     | UniformlyDL, |     | TemperatureL) |     |                 |     |     |     |
| --- | ------------ | --- | ------------ | --- | ------------- | --- | --------------- | --- | --- | --- |
|     | 4. Container |     | Structures:  |     | LoadCase,     |     | StructuralModel |     |     |     |
This modular design directly supports the advanced features required in Assignment
| #4: | thermal         | loading |     | and settlement-induced |        |     | forces. |     |     |     |
| --- | --------------- | ------- | --- | ---------------------- | ------ | --- | ------- | --- | --- | --- |
| 3   | Object-Oriented |         |     |                        | Design |     |         |     |     |     |
This section documents the complete UML architecture of the developed solver. The de-
sign employs standard object-oriented patterns including inheritance (Load hierarchy),
composition (StructuralModel aggregates all entities), and polymorphism (FEF compu-
| tation | via | abstract | Load | interface). |     |     |     |     |     |     |
| ------ | --- | -------- | ---- | ----------- | --- | --- | --- | --- | --- | --- |
2

| Assignment | #4       |        | CE 4011 | - Structural | Analysis Software |
| ---------- | -------- | ------ | ------- | ------------ | ----------------- |
| 3.1 Class  | Diagram: | Domain | Model   |              |                   |
Figure 1: Domain Model UML Class Diagram. Shows the structural hierarchy: Material,
Section, Node, Element form the geometric basis. Support and Load subclasses de(cid:28)ne
boundary conditions and applied forces. LoadCase and StructuralModel provide con-
tainer semantics.
| 3.2 Class | Diagram: | Analysis | Logic |     |     |
| --------- | -------- | -------- | ----- | --- | --- |
Figure 2: Analysis Logic UML Diagram. Depicts the solver pipeline: XMLParser con-
structs the StructuralModel, GlobalAssembler builds the global sti(cid:27)ness matrix (K) and
load vector (F), Solver solves KD = F, and PostProcessor extracts and formats results.
3

| Assignment | #4       |        | CE 4011      | - Structural | Analysis Software |
| ---------- | -------- | ------ | ------------ | ------------ | ----------------- |
| 3.3 Class  | Diagram: | System | Architecture |              |                   |
Figure 3: System Architecture Diagram. Illustrates the full software stack with module
dependencies: parser.pyde(cid:28)nesdatamodels, element_physics.pycomputeslocalsti(cid:27)ness
and FEF, matrix_assembly.py assembles global matrices, banded_solver.py solves the
| linear system, | and post_processor.py |     | extracts results. |     |     |
| -------------- | --------------------- | --- | ----------------- | --- | --- |
4

| Assignment   | #4       |                       | CE 4011 | - Structural | Analysis Software |
| ------------ | -------- | --------------------- | ------- | ------------ | ----------------- |
| 3.4 Activity | Diagram: | Solver Work(cid:29)ow |         |              |                   |
Figure 4: Activity Diagram showing the high-level control (cid:29)ow: Parse XML → Assemble
global matrices → Apply boundary conditions → Solve linear system → Post-process and
output results.
5

| Assignment |          | #4  |          |     |             |     | CE 4011  | - Structural | Analysis Software |     |
| ---------- | -------- | --- | -------- | --- | ----------- | --- | -------- | ------------ | ----------------- | --- |
| 3.5        | Sequence |     | Diagram: |     | Interaction |     | Protocol |              |                   |     |
Figure 5: Sequence Diagram depicting the message passing sequence during thermal
load analysis. The Client instructs the Solver to process a model; internally, the Solver
coordinates parsing, assembly, solving, and post-processing in the correct sequence.
| 4 Q1  | (cid:22)    | Feature |     | Implementation |               |       |     |     |     |     |
| ----- | ----------- | ------- | --- | -------------- | ------------- | ----- | --- | --- | --- | --- |
| 4.1   | Temperature |         |     | Loading        |               | (Part | a)  |     |     |     |
| 4.1.1 | Linear      | Thermal |     | Pro(cid:28)le  | Decomposition |       |     |     |     |     |
Thermal loads on structural members are characterized by a temperature distribution
across the cross-section. For a linear pro(cid:28)le de(cid:28)ned by temperatures at the top (T ) and
u
bottom (T ) surfaces, the exact decomposition into uniform and gradient components is:
b
∆T
|     |     |     |     |     | T       | = T | +   |     |     | (1) |
| --- | --- | --- | --- | --- | ------- | --- | --- | --- | --- | --- |
|     |     |     |     |     | uniform |     | u   |     |     |     |
2
| where the   | temperature |               | di(cid:27)erence |             | is:      |                |     |     |     |     |
| ----------- | ----------- | ------------- | ---------------- | ----------- | -------- | -------------- | --- | --- | --- | --- |
|             |             |               |                  |             |          | ∆T = T         | −T  |     |     | (2) |
|             |             |               |                  |             |          |                | b u |     |     |     |
| 4.1.2       | Fixed-End   |               | Force            | Formulation |          |                |     |     |     |     |
| The thermal |             | pro(cid:28)le | induces          | two         | distinct | e(cid:27)ects: |     |     |     |     |
Axial Thermal Force The uniform temperature change causes thermal strain:
|     |     |     |     |     | F = | α·T     | ·E ·A |     |     | (3) |
| --- | --- | --- | --- | --- | --- | ------- | ----- | --- | --- | --- |
|     |     |     |     |     | T   | uniform |       |     |     |     |
6

|     | Assignment |     | #4  |     |     |     |     |     | CE  | 4011 | - Structural | Analysis | Software |     |
| --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | ------------ | -------- | -------- | --- |
where:
(cid:136)
|     | α   | = coe(cid:30)cient |     | of  | linear | thermal |     | expansion |     |     |     |     |     |     |
| --- | --- | ------------------ | --- | --- | ------ | ------- | --- | --------- | --- | --- | --- | --- | --- | --- |
(cid:136)
|     | T   |     | = uniform |     | temperature |     | component |     |     |     |     |     |     |     |
| --- | --- | --- | --------- | --- | ----------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
uniform
(cid:136)
|     | E   | = Young’s |     | modulus |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:136)
|     | A   | = cross-sectional |     |     | area |     |     |     |     |     |     |     |     |     |
| --- | --- | ----------------- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Thermal Moment (Frame Elements Only) The temperature gradient induces cur-
|     | vature, | generating |     | a bending |     | moment: |     |     |     |     |     |     |     |     |
| --- | ------- | ---------- | --- | --------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
α·∆T
|     |     |     |     |     |     |     | M = |     | ·E  | ·I  |     |     |     | (4) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     | T   | d   |     |     |     |     |     |     |
where:
|     | (cid:136) d | = section |     | depth | (distance |     | between | extreme |     | (cid:28)bers) |     |     |     |     |
| --- | ----------- | --------- | --- | ----- | --------- | --- | ------- | ------- | --- | ------------- | --- | --- | --- | --- |
(cid:136)
|     | I   | = second |     | moment | of  | inertia |     |     |     |     |     |     |     |     |
| --- | --- | -------- | --- | ------ | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
Truss elements, lacking bending sti(cid:27)ness, experience only the axial component. Frame el-
ements subject all six Fixed-End Forces, adjusted for boundary conditions ((cid:28)xed, pinned,
|     | or released | ends).         |     |     |     |              |     |     |       |     |     |     |     |     |
| --- | ----------- | -------------- | --- | --- | --- | ------------ | --- | --- | ----- | --- | --- | --- | --- | --- |
|     | 4.1.3       | Implementation |     |     | in  | TemperatureL |     |     | Class |     |     |     |     |     |
Listing??demonstratestheexactdecompositionandFEFcomputationintheTemperatureL
class:
@dataclass
1
| 2   | class | TemperatureL(MemberLoad): |     |       |     |             |     |     |           |     |         |     |     |     |
| --- | ----- | ------------------------- | --- | ----- | --- | ----------- | --- | --- | --------- | --- | ------- | --- | --- | --- |
| 3   | Tu:   | float                     |     | = 0.0 | #   | Temperature |     |     | at top    |     | surface |     |     |     |
|     | Tb:   | float                     |     | = 0.0 | #   | Temperature |     |     | at bottom |     | surface |     |     |     |
4
5
| 6   | def | FEF(self,   |     |     | fef_condition: |     |      | str, | L:  | float) | ->          | list: |       |     |
| --- | --- | ----------- | --- | --- | -------------- | --- | ---- | ---- | --- | ------ | ----------- | ----- | ----- | --- |
|     |     | """Computes |     |     | thermal        |     | FEF: | F_T  | =   | alpha  | * T_uniform |       | * E * | A,  |
7
|     |     | M_T | =   | (alpha | *   | delta_T |     | / d) | * E | *   | I""" |     |     |     |
| --- | --- | --- | --- | ------ | --- | ------- | --- | ---- | --- | --- | ---- | --- | --- | --- |
8
| 9   |     | fef | =   | [[0.0] | for | _   | in  | range(6)] |     |     |     |     |     |     |
| --- | --- | --- | --- | ------ | --- | --- | --- | --------- | --- | --- | --- | --- | --- | --- |
10
|     |     | E   | = self.element.material.E |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | ------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
11
| 12  |     | alpha |                          | = self.element.material.alpha |     |     |     |     |     |     |     |     |     |     |
| --- | --- | ----- | ------------------------ | ----------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13  |     | A     | = self.element.section.A |                               |     |     |     |     |     |     |     |     |     |     |
|     |     | I     | = self.element.section.I |                               |     |     |     |     |     |     |     |     |     |     |
14
|     |     | d   | = self.element.section.d |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | ------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
15
16
| 17  |     | #       | Exact | decomposition |         |     |           |     |     |     |     |     |     |     |
| --- | --- | ------- | ----- | ------------- | ------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
|     |     | delta_T |       | =             | self.Tb |     | - self.Tu |     |     |     |     |     |     |     |
18
| 19  |     | T_uniform |     |     | = self.Tu |     | +   | (delta_T |     | / 2.0) |     |     |     |     |
| --- | --- | --------- | --- | --- | --------- | --- | --- | -------- | --- | ------ | --- | --- | --- | --- |
20
|     |     | #   | Axial | thermal |     | force |     |     |     |     |     |     |     |     |
| --- | --- | --- | ----- | ------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
21
|     |     | F_T | =   | alpha | *   | T_uniform |     | *   | E * A |     |     |     |     |     |
| --- | --- | --- | --- | ----- | --- | --------- | --- | --- | ----- | --- | --- | --- | --- | --- |
22
| 23  |     | fef[0][0] |     |     | = -F_T |     |     |     |     |     |     |     |     |     |
| --- | --- | --------- | --- | --- | ------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
7

| Assignment |     |           | #4  |     |     |     |     |     | CE 4011 | - Structural |     | Analysis | Software |     |
| ---------- | --- | --------- | --- | --- | --- | --- | --- | --- | ------- | ------------ | --- | -------- | -------- | --- |
| 24         |     | fef[3][0] |     | =   | F_T |     |     |     |         |              |     |          |          |     |
25
|     |     | #   | Trusses |     | have | only | axial | thermal |     | effects |     |     |     |     |
| --- | --- | --- | ------- | --- | ---- | ---- | ----- | ------- | --- | ------- | --- | --- | --- | --- |
26
|     |     |     |                   |     |     |     |     | ’     | ’   |     |     |     |     |     |
| --- | --- | --- | ----------------- | --- | --- | --- | --- | ----- | --- | --- | --- | --- | --- | --- |
| 27  |     | if  | self.element.type |     |     |     | ==  | truss | :   |     |     |     |     |     |
|     |     |     | return            |     | fef |     |     |       |     |     |     |     |     |     |
28
29
| 30  |     | #   | Moment   | magnitude |     |         | for frame |      | elements |      |      |        |     |     |
| --- | --- | --- | -------- | --------- | --- | ------- | --------- | ---- | -------- | ---- | ---- | ------ | --- | --- |
| 31  |     | M_T | = (alpha |           | *   | delta_T | /         | d) * | E *      | I if | d != | 0 else | 0.0 |     |
32
|     |     | #   | Adjust | FEF | based |     | on end | releases |     |     |     |     |     |     |
| --- | --- | --- | ------ | --- | ----- | --- | ------ | -------- | --- | --- | --- | --- | --- | --- |
33
| 34  |     | if  | fef_condition |     |     | ==     | "fixed-fixed": |     |     |     |     |     |     |     |
| --- | --- | --- | ------------- | --- | --- | ------ | -------------- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     | fef[2][0]     |     |     | = -M_T |                |     |     |     |     |     |     |     |
35
|     |     |     | fef[5][0] |     |     | = M_T |     |     |     |     |     |     |     |     |
| --- | --- | --- | --------- | --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
36
| 37  |     | #   | ... additional |     |     | boundary |     | condition |     | cases | ... |     |     |     |
| --- | --- | --- | -------------- | --- | --- | -------- | --- | --------- | --- | ----- | --- | --- | --- | --- |
38
|     |     | return |     | fef |     |     |     |     |     |     |     |     |     |     |
| --- | --- | ------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
39
|       |     |          | Listing        | 1:  | Thermal |     | Load FEF | Decomposition |     |     | (parser.py) |     |     |     |
| ----- | --- | -------- | -------------- | --- | ------- | --- | -------- | ------------- | --- | --- | ----------- | --- | --- | --- |
| 4.1.4 |     | Physical | Interpretation |     |         |     |          |               |     |     |             |     |     |     |
(cid:136)
Anincreaseinuniformtemperaturecausesuniformexpansion,inducingcompressive
|     | axial | force | in  | restrained |     | elements. |     |     |     |     |     |     |     |     |
| --- | ----- | ----- | --- | ---------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:136)
A positive thermal gradient (T > T ) causes larger expansion at the bottom sur-
|     |     |     |     |     |     |     | b   | u   |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
face, inducing compression in the bottom (cid:28)bers and tension in the top (cid:28)bers. The
|     | moment |     | acts | to cause | negative |     | curvature | (hogging). |     |     |     |     |     |     |
| --- | ------ | --- | ---- | -------- | -------- | --- | --------- | ---------- | --- | --- | --- | --- | --- | --- |
(cid:136) In fully restrained members, support reactions must balance these thermal forces
and moments.
(cid:136)
In partially restrained or free members, displacements and deformations occur to
|       | accommodate |         |              | the         | thermal | strains. |       |     |     |     |     |     |     |     |
| ----- | ----------- | ------- | ------------ | ----------- | ------- | -------- | ----- | --- | --- | --- | --- | --- | --- | --- |
| 4.2   |             | Support |              | Settlements |         |          | (Part | b)  |     |     |     |     |     |     |
| 4.2.1 |             | Matrix  | Partitioning |             |         | Strategy |       |     |     |     |     |     |     |     |
Rather than constructing and storing the full global sti(cid:27)ness matrix (which would waste
memory on zero blocks for prescribed DOFs), the solver employs a matrix partitioning
strategy:
|                      |     |     |     |     |              | (cid:20) |                              | (cid:21)(cid:20) | (cid:21) (cid:20) | (cid:21) |     |                   |     |     |
| -------------------- | --- | --- | --- | --- | ------------ | -------- | ---------------------------- | ---------------- | ----------------- | -------- | --- | ----------------- | --- | --- |
|                      |     |     |     |     |              | K        | K                            | D                | F                 |          |     |                   |     |     |
|                      |     |     |     |     |              | aa       | ar                           | a                | =                 | a        |     |                   |     | (5) |
|                      |     |     |     |     |              | K        | K                            | D                | F                 |          |     |                   |     |     |
|                      |     |     |     |     |              | ra       | rr                           | r                |                   | r        |     |                   |     |     |
|                      |     |     |     |     | denoteactive |          | (unconstrained)andrestrained |                  |                   |          |     |                   |     |     |
| wheresubscriptsaandr |     |     |     |     |              |          |                              |                  |                   |          |     | (prescribed)DOFs. |     |     |
K
| Only | the | active | portion |     | aa is | assembled |      | and solved: |      |     |     |     |     |     |
| ---- | --- | ------ | ------- | --- | ----- | --------- | ---- | ----------- | ---- | --- | --- | --- | --- | --- |
|      |     |        |         |     |       | K         | D =  | F −K        | D    |     |     |     |     | (6) |
|      |     |        |         |     |       |           | aa a | a           | ar r |     |     |     |     |     |
D
The right-hand side incorporates the known prescribed displacements r (settle-
ments).
8

| Assignment |     |                    | #4  |     |     |         |     |        | CE  | 4011 | - Structural | Analysis | Software |     |
| ---------- | --- | ------------------ | --- | --- | --- | ------- | --- | ------ | --- | ---- | ------------ | -------- | -------- | --- |
| 4.2.2      |     | Settlement-Induced |     |     |     | Element |     | Forces |     |      |              |          |          |     |
At the element level, settlement forces are computed directly from the element displace-
| ment | vector |     | and local | sti(cid:27)ness |     | matrix:   |     |          |        |     |     |     |     |     |
| ---- | ------ | --- | --------- | --------------- | --- | --------- | --- | -------- | ------ | --- | --- | --- | --- | --- |
|      |        |     |           |                 |     | f         |     | = [k]·{u |        | }   |     |     |     |     |
|      |        |     |           |                 |     | unbalance |     |          | settle |     |     |     |     | (7) |
where [k] is the local element sti(cid:27)ness and {u } contains the full displacement vector
settle
| (incorporating |     |                  | prescribed |     | settlements |           | at       | restrained |     | supports).    |     |     |     |     |
| -------------- | --- | ---------------- | ---------- | --- | ----------- | --------- | -------- | ---------- | --- | ------------- | --- | --- | --- | --- |
| 4.2.3          |     | Post-Processing: |            |     |             | Stitching | Complete |            |     | Displacements |     |     |     |     |
The post-processor reconstructs the complete global displacement (cid:28)eld by merging active
| and | prescribed                       |     | DOFs. |     | Listing | ?? shows |     | this implementation: |     |     |     |     |     |     |
| --- | -------------------------------- | --- | ----- | --- | ------- | -------- | --- | -------------------- | --- | --- | --- | --- | --- | --- |
| def | _build_full_displacements(self): |     |       |     |         |          |     |                      |     |     |     |     |     |     |
1
"""
2
3 Maps the solved active DOF displacements back to all nodes,
|     | including |     |     | prescribed |     | settlement |     |     | values |     | at restrained |     | DOFs. |     |
| --- | --------- | --- | --- | ---------- | --- | ---------- | --- | --- | ------ | --- | ------------- | --- | ----- | --- |
4
"""
5
| 6   | for | n_id, |          | node | in  | self.model.nodes.items(): |                       |     |     |     |     |     |     |     |
| --- | --- | ----- | -------- | ---- | --- | ------------------------- | --------------------- | --- | --- | --- | --- | --- | --- | --- |
| 7   |     | disp  | =        | []   |     |                           |                       |     |     |     |     |     |     |     |
|     |     | for   | dof_idx, |      | dof | in                        | enumerate(node.dofs): |     |     |     |     |     |     |     |
8
| 9   |     |     | if  | dof | >=     | 0:   |     |     |        |       |     |     |     |     |
| --- | --- | --- | --- | --- | ------ | ---- | --- | --- | ------ | ----- | --- | --- | --- | --- |
| 10  |     |     |     | #   | Active | DOF: |     | use | solved | value |     |     |     |     |
disp.append(self.D_active[dof][0])
11
else:
12
| 13  |     |     |     | #       | Restrained |     | DOF:                          |     | check | for | prescribed |     | settlement |     |
| --- | --- | --- | --- | ------- | ---------- | --- | ----------------------------- | --- | ----- | --- | ---------- | --- | ---------- | --- |
| 14  |     |     |     | support |            | =   | self.model.supports.get(n_id) |     |       |     |            |     |            |     |
|     |     |     |     | if      | support    |     | is                            | not | None: |     |            |     |            |     |
15
| 16  |     |     |     |     | if  | dof_idx |             | ==  | 0 and | support.restrain_ux: |          |            |     |     |
| --- | --- | --- | --- | --- | --- | ------- | ----------- | --- | ----- | -------------------- | -------- | ---------- | --- | --- |
| 17  |     |     |     |     |     | #       | X-direction |     | with  |                      | possible | settlement |     |     |
disp.append(support.settlement_ux)
18
|     |     |     |     |     | elif | dof_idx |     | ==  | 1 and |     | support.restrain_uy: |     |     |     |
| --- | --- | --- | --- | --- | ---- | ------- | --- | --- | ----- | --- | -------------------- | --- | --- | --- |
19
| 20  |     |     |     |     |      | #                                  | Y-direction |     | with  |     | possible             | settlement |     |     |
| --- | --- | --- | --- | --- | ---- | ---------------------------------- | ----------- | --- | ----- | --- | -------------------- | ---------- | --- | --- |
| 21  |     |     |     |     |      | disp.append(support.settlement_uy) |             |     |       |     |                      |            |     |     |
|     |     |     |     |     | elif | dof_idx                            |             | ==  | 2 and |     | support.restrain_rz: |            |     |     |
22
| 23  |     |     |     |     |     | #                | Rotation |     | restrained |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ---------------- | -------- | --- | ---------- | --- | --- | --- | --- | --- |
| 24  |     |     |     |     |     | disp.append(0.0) |          |     |            |     |     |     |     |     |
else:
25
disp.append(0.0)
26
| 27  |     |                          |     | else: |                  |     |     |     |      |     |     |     |     |     |
| --- | --- | ------------------------ | --- | ----- | ---------------- | --- | --- | --- | ---- | --- | --- | --- | --- | --- |
| 28  |     |                          |     |       | disp.append(0.0) |     |     |     |      |     |     |     |     |     |
|     |     | self.displacements[n_id] |     |       |                  |     |     | =   | disp |     |     |     |     |     |
29
Listing 2: Settlement Displacement Stitching (post rocessor.py)
p
| 4.2.4 |     | Extended |     | Support |     | Dataclass |     |     |     |     |     |     |     |     |
| ----- | --- | -------- | --- | ------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
To support settlements, the Support dataclass has been extended with three additional
| attributes |     | representing |     |     | prescribed |     | displacements: |     |     |     |     |     |     |     |
| ---------- | --- | ------------ | --- | --- | ---------- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- |
9

| Assignment |     |     | #4  |     |     |     |     | CE  | 4011 | - Structural | Analysis Software |
| ---------- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | ------------ | ----------------- |
1 @dataclass
| class |     | Support: |     |     |     |     |     |     |     |     |     |
| ----- | --- | -------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
2
| 3   | node:        |     | Node |      |         |     |     |     |     |     |     |
| --- | ------------ | --- | ---- | ---- | ------- | --- | --- | --- | --- | --- | --- |
| 4   | restrain_ux: |     |      | bool | = False |     |     |     |     |     |     |
|     | restrain_uy: |     |      | bool | = False |     |     |     |     |     |     |
5
|     | restrain_rz: |     |     | bool | = False |     |     |     |     |     |     |
| --- | ------------ | --- | --- | ---- | ------- | --- | --- | --- | --- | --- | --- |
6
| 7   | settlement_ux: |     |     | float |     | = 0.0 |     | # Prescribed |     | displacement |     |
| --- | -------------- | --- | --- | ----- | --- | ----- | --- | ------------ | --- | ------------ | --- |
| 8   | settlement_uy: |     |     | float |     | = 0.0 |     | # Prescribed |     | displacement |     |
|     | settlement_rz: |     |     | float |     | = 0.0 |     | # Prescribed |     | rotation     |     |
9
|       |     |          | Listing        | 3:  | Extended |     | Support | Dataclass |     | (parser.py) |     |
| ----- | --- | -------- | -------------- | --- | -------- | --- | ------- | --------- | --- | ----------- | --- |
| 4.2.5 |     | Physical | Interpretation |     |          |     |         |           |     |             |     |
(cid:136)
Prescribed settlements simulate real-world scenarios: foundation settlements, sup-
|     | port | displacement, |     | or  | fabrication-induced |     |     | o(cid:27)sets. |     |     |     |
| --- | ---- | ------------- | --- | --- | ------------------- | --- | --- | -------------- | --- | --- | --- |
(cid:136) The global system must equilibrate; support reactions balance applied loads and
|     | settlement-induced |     |     | member |     | forces. |     |     |     |     |     |
| --- | ------------------ | --- | --- | ------ | --- | ------- | --- | --- | --- | --- | --- |
(cid:136)
Member-end forces at settlements are non-zero (unlike simple supports) because
|     | the | members | must | resist | the | kinematic |     | constraints. |     |     |     |
| --- | --- | ------- | ---- | ------ | --- | --------- | --- | ------------ | --- | --- | --- |
(cid:136)
Secondary e(cid:27)ects emerge: secondary moments in frames due to horizontal loads
combined with vertical settlements, redistribution of forces to sti(cid:27)er load paths.
| 5   | Q2         | (cid:22) | Numerical |             |     | Analysis |     | and |     | Validation |     |
| --- | ---------- | -------- | --------- | ----------- | --- | -------- | --- | --- | --- | ---------- | --- |
| 5.1 | Validation |          |           | Methodology |     |          |     |     |     |            |     |
All numerical results have been validated against the industry-standard SAP2000 FEA
| solver | using |     | a specialized | test | utility | that | accounts |     | for: |     |     |
| ------ | ----- | --- | ------------- | ---- | ------- | ---- | -------- | --- | ---- | --- | --- |
(cid:136)
Coordinate System Transformations: SAP2000 uses the X-Z global plane; our
|     | solver | uses | X-Y. | The | transformation |     | is  | applied | systematically. |     |     |
| --- | ------ | ---- | ---- | --- | -------------- | --- | --- | ------- | --------------- | --- | --- |
(cid:136) Local-to-Global Force Transformations: Member forces are output in local
(element) coordinates and must be rotated to global for comparison.
(cid:136)
Tolerance Strategy: Hybridrelative/absolutetoleranceaccommodatesbothlarge
|       | and  | small   | value         | regimes | (1% | relative, | 1e-6 | absolute). |     |     |     |
| ----- | ---- | ------- | ------------- | ------- | --- | --------- | ---- | ---------- | --- | --- | --- |
| 5.2   | Part |         | a: Settlement |         |     | Analysis  |      |            |     |     |     |
| 5.2.1 |      | Problem | Statement     |         |     |           |      |            |     |     |     |
A hybrid structure comprising a concrete moment-resisting frame and a suspended steel
truss system is analyzed under static loads with support settlements. Speci(cid:28)cally:
(cid:136)
Geometry: Concrete frame (nodes A, B, C, D) with steel truss (nodes D, E, F)
|     | pinned |     | at top. |     |     |     |     |     |     |     |     |
| --- | ------ | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
10

| Assignment |                      | #4  |           |     |     |           |        | CE  | 4011  | - Structural | Analysis Software |
| ---------- | -------------------- | --- | --------- | --- | --- | --------- | ------ | --- | ----- | ------------ | ----------------- |
|            | (cid:136) Materials: |     | Concrete: |     | E   | = 30 GPa; | Steel: | E   | = 200 | GPa.         |                   |
|            |                      |     |           |     | c   |           |        | s   |       |              |                   |
(cid:136) Sections: Frame members: A = 0.3 m2, I = 0.0075 m4; Truss members: A = 0.01
m2.
(cid:136)
Applied Loads: Concentrated vertical load of 50 kN at node C.
(cid:136)
Settlement: Support E (base of truss) undergoes a vertical settlement: ∆ = 2
|       | mm        | downward. |       |               |               |      |       |           |       |             |     |
| ----- | --------- | --------- | ----- | ------------- | ------------- | ---- | ----- | --------- | ----- | ----------- | --- |
|       |           | Figure    |       | 6: Settlement |               | Case | (Q2a) | structure | built | in SAP2000. |     |
| 5.2.2 | Solution: |           | Nodal |               | Displacements |      |       |           |       |             |     |
The solver computes nodal displacements, which are presented in Table ??:
|     |      |     | Table | 1: Nodal |     | Displacements |     | (cid:22) Settlement |       | Case  | (Q2a)   |
| --- | ---- | --- | ----- | -------- | --- | ------------- | --- | ------------------- | ----- | ----- | ------- |
|     | Node |     | u     | [m]      |     | u [m]         |     | θ                   | [rad] | Match | SAP2000 |
|     |      |     | x     |          |     | y             |     | z                   |       |       |         |
✓
|     | 1   |     | 0.000×100 |     |     | 0.000×100 |     | −6.607×10−4 |     |     |     |
| --- | --- | --- | --------- | --- | --- | --------- | --- | ----------- | --- | --- | --- |
✓
|     | 2   |     | 3.591×10−6 |     | −1.994×10−3 |     |     | −1.738×10−4 |     |     |     |
| --- | --- | --- | ---------- | --- | ----------- | --- | --- | ----------- | --- | --- | --- |
|     |     |     | 5.369×10−6 |     | −9.569×10−4 |     |     | 2.813×10−4  |     |     | ✓   |
3
|     |     |     | 5.369×10−6 |     | −1.129×10−4 |     |     | 2.813×10−4 |     |     | ✓   |
| --- | --- | --- | ---------- | --- | ----------- | --- | --- | ---------- | --- | --- | --- |
4
|     |     |     | 0.000×100 |     | −2.000×10−3 |           |     | 8.556×10−5 |     | ✓   |              |
| --- | --- | --- | --------- | --- | ----------- | --------- | --- | ---------- | --- | --- | ------------ |
|     | 5   |     |           |     |             |           |     |            |     |     | (prescribed) |
|     |     |     | 0.000×100 |     |             | 0.000×100 |     | 0.000×100  |     |     | ✓            |
6
| 5.2.3 | Solution: |          | Support |            | Reactions |           |            |                     |     |               |     |
| ----- | --------- | -------- | ------- | ---------- | --------- | --------- | ---------- | ------------------- | --- | ------------- | --- |
| Table | ??        | presents | the     | calculated |           | support   | reactions: |                     |     |               |     |
|       |           |          | Table   | 2:         | Support   | Reactions |            | (cid:22) Settlement |     | Case (Q2a)    |     |
|       |           |          |         | R          |           | R         | M          | •                   |     |               |     |
|       |           | Node     |         | x [kN]     |           | y [kN]    |            | z [kN               | m]  | Match SAP2000 |     |
✓
|     |     | 1   |     | −6.7326 |     | 9.5105   |     | Free |     |     |     |
| --- | --- | --- | --- | ------- | --- | -------- | --- | ---- | --- | --- | --- |
|     |     |     |     | 5.0658  |     | −11.7328 |     |      |     | ✓   |     |
|     |     | 5   |     |         |     |          |     | Free |     |     |     |
11

| Assignment |           | #4  |            |     |        |     |     | CE 4011 | -   | Structural | Analysis Software |
| ---------- | --------- | --- | ---------- | --- | ------ | --- | --- | ------- | --- | ---------- | ----------------- |
| 5.2.4      | Solution: |     | Member-End |     | Forces |     |     |         |     |            |                   |
Selected frame members are presented in Table ??. Forces are reported in local (member)
coordinates:
Table 3: Member-End Forces (Local Coordinates) (cid:22) Settlement Case (Q2a)
•
|     | Element |     | Node | N       | [kN] | V [kN] |     | M [kN  | m]  | Match | SAP2000 |
| --- | ------- | --- | ---- | ------- | ---- | ------ | --- | ------ | --- | ----- | ------- |
|     |         |     | 1    | −6.7326 |      | 9.5105 |     | 0.0000 |     |       | ✓       |
F1
|     |     |     | 2   | 6.7326  |     | −9.5105 |     | 38.0419  |     |     | ✓   |
| --- | --- | --- | --- | ------- | --- | ------- | --- | -------- | --- | --- | --- |
|     |     |     | 2   | −1.6667 |     | −2.2223 |     | −17.7786 |     |     | ✓   |
F2
|     |     |     | 3   | 1.6667 |     | 2.2223 |     | 0.0000 |     |     | ✓   |
| --- | --- | --- | --- | ------ | --- | ------ | --- | ------ | --- | --- | --- |
|     |     |     | 3   | 0.0000 |     | 0.0000 |     | 0.0000 |     |     | ✓   |
F3
|     |     |     | 4   | 0.0000   |     | 0.0000  |     | 0.0000   |     |     | ✓   |
| --- | --- | --- | --- | -------- | --- | ------- | --- | -------- | --- | --- | --- |
|     |     |     | 2   | −11.7328 |     | −5.0658 |     | −20.2633 |     |     | ✓   |
F4
|     |     |     | 5   | 11.7328 |     | 5.0658 |     | 0.0000 |     |     | ✓   |
| --- | --- | --- | --- | ------- | --- | ------ | --- | ------ | --- | --- | --- |
|     |     |     | 6   | 2.7779  |     | 0.0000 |     | 0.0000 |     |     | ✓   |
T1
|       |               |       | 3             | −2.7779 |     | 0.0000  |     | 0.0000    |       |     | ✓   |
| ----- | ------------- | ----- | ------------- | ------- | --- | ------- | --- | --------- | ----- | --- | --- |
| 5.2.5 | Validation    |       | Summary       |         |     |         |     |           |       |     |     |
|       | (cid:136) All | nodal | displacements | match   |     | SAP2000 |     | to within | 1.0%. |     |     |
(cid:136)
|     | All | support | reactions | match | SAP2000 |     | to  | within | 1.5%. |     |     |
| --- | --- | ------- | --------- | ----- | ------- | --- | --- | ------ | ----- | --- | --- |
(cid:136)
|     | All | member-end | forces | match |     | SAP2000 | to  | within | 2.0%. |     |     |
| --- | --- | ---------- | ------ | ----- | --- | ------- | --- | ------ | ----- | --- | --- |
(cid:136)
|     | The | prescribed | settlement |     | (∆  |     | = −2mm) |     | is correctly | enforced. |     |
| --- | --- | ---------- | ---------- | --- | --- | --- | ------- | --- | ------------ | --------- | --- |
Node5,y
12

| Assignment |        | #4      |     |                     |     |      | CE 4011 | - Structural | Analysis Software |     |
| ---------- | ------ | ------- | --- | ------------------- | --- | ---- | ------- | ------------ | ----------------- | --- |
| 5.2.6      | Solver | Results |     | (cid:22) Settlement |     | Case | (Q2a)   |              |                   |     |
Figure 7: Custom solver output for the Settlement Case (Q2a), showing nodal displace-
ments, member local end forces, and support reactions matching the SAP2000 reference.
| 5.3   | Part    | b: Thermal |           |     | Loading | Analysis |     |     |     |     |
| ----- | ------- | ---------- | --------- | --- | ------- | -------- | --- | --- | --- | --- |
| 5.3.1 | Problem |            | Statement |     |         |          |     |     |     |     |
A structure composed of a concrete primary beam and supporting steel truss elements is
| subjected |     | to a non-uniform |     | thermal | loading. |     | Speci(cid:28)cally: |     |     |     |
| --------- | --- | ---------------- | --- | ------- | -------- | --- | ------------------- | --- | --- | --- |
(cid:136) Geometry: Concrete beam (nodes A, B, C) spanning 12 m; steel trusses at sup-
ports.
(cid:136)
Materials: Concrete: E = 30 GPa, α = 12 × 10−6 /◦C; Steel: E = 200 GPa,
|     |     |           |      |     | c   |     | c   |     | s   |     |
| --- | --- | --------- | ---- | --- | --- | --- | --- | --- | --- | --- |
|     | α   | = 12×10−6 | /◦C. |     |     |     |     |     |     |     |
s
(cid:136)
|     | Sections: | Beam: |     | A = 0.5 | m2, I   | = 0.04      | m4, d = 0.8 | m (depth). |        |     |
| --- | --------- | ----- | --- | ------- | ------- | ----------- | ----------- | ---------- | ------ | --- |
|     | (cid:136) |       |     |         |         |             |             |            | +50◦C. |     |
|     | Thermal   | Load: |     | Bottom  | surface | temperature | increase:   | ∆T         | =      | Top |
bottom
0◦C.
|     | surface | remains | at  | reference | temperature: |     | ∆T = |     |     |     |
| --- | ------- | ------- | --- | --------- | ------------ | --- | ---- | --- | --- | --- |
top
13

| Assignment |     | #4  |     |     |     |     | CE  | 4011 | - Structural | Analysis Software |
| ---------- | --- | --- | --- | --- | --- | --- | --- | ---- | ------------ | ----------------- |
Figure 8: Thermal Loading Case (Q2b) structure built in SAP2000.
| 5.3.2 | Solution: |          | Nodal        | Displacements |               |                |          |         |            |         |
| ----- | --------- | -------- | ------------ | ------------- | ------------- | -------------- | -------- | ------- | ---------- | ------- |
| Table | ??        | presents | the computed |               | nodal         | displacements: |          |         |            |         |
|       |           |          | Table 4:     | Nodal         | Displacements |                | (cid:22) | Thermal | Case (Q2b) |         |
|       | Node      |          | u [m]        |               | u             | [m]            |          | θ [rad] | Match      | SAP2000 |
|       |           |          | x            |               |               | y              |          | z       |            |         |
✓
|     | 1   |     | 0.000×100 |     | 0.000×100 |     | 0.000×100 |     |     | ((cid:28)xed) |
| --- | --- | --- | --------- | --- | --------- | --- | --------- | --- | --- | ------------- |
✓
|     | 2   |     | −7.323×10−7 |     | −1.939×10−3 |     | −4.593×10−4 |     |     |     |
| --- | --- | --- | ----------- | --- | ----------- | --- | ----------- | --- | --- | --- |
|     |     |     | 0.000×100   |     | 0.000×100   |     | 1.678×10−3  |     |     | ✓   |
3
|     |     |     | 0.000×100 |     | 0.000×100 |     | 0.000×100 |     |     | ✓   |
| --- | --- | --- | --------- | --- | --------- | --- | --------- | --- | --- | --- |
4
|     |     |     | 0.000×100 |     | 0.000×100 |     | 0.000×100 |     |     | ✓   |
| --- | --- | --- | --------- | --- | --------- | --- | --------- | --- | --- | --- |
5
| 5.3.3 | Solution: |          | Member-End |     |       | Forces      |     |     |     |     |
| ----- | --------- | -------- | ---------- | --- | ----- | ----------- | --- | --- | --- | --- |
| Table | ??        | presents | the member |     | local | end forces: |     |     |     |     |
Table 5: Member-End Forces (Local Coordinates) (cid:22) Thermal Case (Q2b)
•
|     | Element |     | Node | N         | [kN] | V [kN] |     | M [kN    | m] Match | SAP2000 |
| --- | ------- | --- | ---- | --------- | ---- | ------ | --- | -------- | -------- | ------- |
|     |         |     | 1    | 1921.0043 |      | 5.9276 |     | 310.3423 |          | ✓       |
F1
|     |     |     | 2   | −1921.0043 |     | −5.9276 |     | −268.8495 |     | ✓   |
| --- | --- | --- | --- | ---------- | --- | ------- | --- | --------- | --- | --- |
|     |     |     | 2   | 1919.2189  |     | 29.8722 |     | 268.8495  |     | ✓   |
F2
|     |     |     | 3   | −1919.2189 |     | −29.8722 |     | 0.0000 |     | ✓   |
| --- | --- | --- | --- | ---------- | --- | -------- | --- | ------ | --- | --- |
|     |     |     | 2   | 14.4656    |     | 0.0000   |     | 0.0000 |     | ✓   |
T1
|     |     |     | 4   | −14.4656 |     | 0.0000 |     | 0.0000 |     | ✓   |
| --- | --- | --- | --- | -------- | --- | ------ | --- | ------ | --- | --- |
|     |     |     | 2   | 13.7577  |     | 0.0000 |     | 0.0000 |     | ✓   |
T2
|     |     |     | 5   | −13.7577 |     | 0.0000 |     | 0.0000 |     | ✓   |
| --- | --- | --- | --- | -------- | --- | ------ | --- | ------ | --- | --- |
14

| Assignment |           | #4    |             |            |           | CE               | 4011 | - Structural | Analysis Software |
| ---------- | --------- | ----- | ----------- | ---------- | --------- | ---------------- | ---- | ------------ | ----------------- |
| 5.3.4      | Solution: |       | Support     |            | Reactions |                  |      |              |                   |
| Table      | ??        | shows | the support | reactions: |           |                  |      |              |                   |
|            |           |       | Table 6:    | Support    | Reactions | (cid:22) Thermal |      | Case         | (Q2b)             |
•
|     |     | Node | R [kN] |     | R [kN] | M [kN | m]  | Match | SAP2000 |
| --- | --- | ---- | ------ | --- | ------ | ----- | --- | ----- | ------- |
|     |     |      | x      |     | y      | z     |     |       |         |
✓
|     |     | 1   | 1921.0043 |     | 5.9276 | 310.3423 |     |     |     |
| --- | --- | --- | --------- | --- | ------ | -------- | --- | --- | --- |
✓
|     |     | 3   | −1919.2189 |     | −29.8722 | Free |     |     |     |
| --- | --- | --- | ---------- | --- | -------- | ---- | --- | --- | --- |
✓
|       |            | 4   | 6.4692  |     | 12.9384 | Free |     |     |     |
| ----- | ---------- | --- | ------- | --- | ------- | ---- | --- | --- | --- |
|       |            |     | −8.2546 |     | 11.0062 |      |     |     | ✓   |
|       |            | 5   |         |     |         | Free |     |     |     |
| 5.3.5 | Validation |     | Summary |     |         |      |     |     |     |
(cid:136)
|     | All | nodal | displacements |     | match SAP2000 | to within |     | 1.0%. |     |
| --- | --- | ----- | ------------- | --- | ------------- | --------- | --- | ----- | --- |
(cid:136)
|     | All | support | reactions | match | SAP2000 | to within | 2.0%. |     |     |
| --- | --- | ------- | --------- | ----- | ------- | --------- | ----- | --- | --- |
(cid:136) Axial forces in frame elements correctly re(cid:29)ect thermal strain restraint.
(cid:136) Bending moments and shear forces from the thermal gradient are correctly com-
puted.
15

| Assignment   | #4      |                  | CE 4011    | - Structural | Analysis Software |
| ------------ | ------- | ---------------- | ---------- | ------------ | ----------------- |
| 5.3.6 Solver | Results | (cid:22) Thermal | Case (Q2b) |              |                   |
Figure 9: Custom solver output for the Thermal Loading Case (Q2b), showing nodal
displacements, member local end forces, and support reactions matching the SAP2000
reference.
| 5.3.7 Regression | Test | Conclusion |     |     |     |
| ---------------- | ---- | ---------- | --- | --- | --- |
Figure 10: Regression test output con(cid:28)rming that the Thermal Loading Case (Q2b)
and Settlement Case (Q2a) passes all automated validation checks against the SAP2000
| reference | solution. |     |     |     |     |
| --------- | --------- | --- | --- | --- | --- |
16

| Assignment |         | #4            |     |             |         |       | CE  | 4011 | - Structural | Analysis | Software |
| ---------- | ------- | ------------- | --- | ----------- | ------- | ----- | --- | ---- | ------------ | -------- | -------- |
| 6          | Testing |               | and | Reliability |         |       |     |      |              |          |          |
| 6.1        |         | Comprehensive |     |             | Testing | Suite |     |      |              |          |          |
The software reliability is ensured through a multi-layered testing strategy encompassing
| unit | tests,    | interface | tests,             | and    | regression | validation.          |     |        |       |       |              |
| ---- | --------- | --------- | ------------------ | ------ | ---------- | -------------------- | --- | ------ | ----- | ----- | ------------ |
| 6.2  |           | Thermal   | Unit               | Tests  |            |                      |     |        |       |       |              |
| New  | unit      | tests     | speci(cid:28)cally | target | the        | TemperatureL         |     | class: |       |       |              |
|      | (cid:136) |           |                    |        |            |                      |     | F =    | α · T | · E · | A            |
|      | Axial     | Force     | Magnitude          |        |            | Test: Veri(cid:28)es |     | T      |       |       | with various |
uniform
|     | material | and | thermal | pro(cid:28)les. |     |     |     |     |     |     |     |
| --- | -------- | --- | ------- | --------------- | --- | --- | --- | --- | --- | --- | --- |
(cid:136) Moment Magnitude Test: Veri(cid:28)es M = α·∆T ·E ·I for frame elements.
T
d
(cid:136) Truss-Only Axial Test: Con(cid:28)rms that truss elements compute only axial forces,
|     | ignoring | bending |     | moment | contributions. |     |     |     |     |     |     |
| --- | -------- | ------- | --- | ------ | -------------- | --- | --- | --- | --- | --- | --- |
(cid:136)
Boundary Condition Sensitivity: Tests FEF adjustment logic for (cid:28)xed, pinned,
|     | and | released  | boundary |     | conditions. |     |     |     |     |     |     |
| --- | --- | --------- | -------- | --- | ----------- | --- | --- | --- | --- | --- | --- |
| 6.3 |     | Interface | Tests    |     |             |     |     |     |     |     |     |
Interface tests verify the global assembly and load application pipeline:
(cid:136)
Settlement Load Assembly: Con(cid:28)rms that settlement-induced unbalance forces
|     | are | correctly | incorporated |     | into | the global | load | vector. |     |     |     |
| --- | --- | --------- | ------------ | --- | ---- | ---------- | ---- | ------- | --- | --- | --- |
(cid:136)
Thermal Load Assembly: Veri(cid:28)es that thermal FEF from all elements are cor-
|     | rectly | summed | into | the | global | load vector. |     |     |     |     |     |
| --- | ------ | ------ | ---- | --- | ------ | ------------ | --- | --- | --- | --- | --- |
(cid:136) Boundary Condition Incorporation: Ensures that prescribed displacements
(settlements) are correctly partitioned and applied in the solver.
| 6.4 |     | Backward | Compatibility |     |     | and | Regression |     | Suite |     |     |
| --- | --- | -------- | ------------- | --- | --- | --- | ---------- | --- | ----- | --- | --- |
The regression suite comprehensively validates 100% backward compatibility with As-
| signment |     | #3: |     |     |     |     |     |     |     |     |     |
| -------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:136)
Example 1 (Settlement Frame): Complex frame with settlement. SAP2000
validation with full coordinate transformations and tolerance management.
(cid:136)
Example 2 (Thermal Beam): Two-span beam with thermal gradient. Moment
|     | and | rotation | validated |     | analytically. |     |     |     |     |     |     |
| --- | --- | -------- | --------- | --- | ------------- | --- | --- | --- | --- | --- | --- |
17

| Assignment | #4            |         |          |         | CE      | 4011 - Structural | Analysis Software |
| ---------- | ------------- | ------- | -------- | ------- | ------- | ----------------- | ----------------- |
| 6.5 Test   | Results       | Summary |          |         |         |                   |                   |
|            |               |         | Table 7: | Testing | Summary |                   |                   |
|            | Test Category |         |          | Count   | Pass    | Rate              | Status            |
✓
|     | Unit Tests | (Thermal) |     | 8   |     | 100% | All Pass |
| --- | ---------- | --------- | --- | --- | --- | ---- | -------- |
✓
|     | Interface | Tests |     | 6   |     | 100% | All Pass |
| --- | --------- | ----- | --- | --- | --- | ---- | -------- |
✓
|     | Regression | Tests | (A#3) | 3   |     | 100% | All Pass |
| --- | ---------- | ----- | ----- | --- | --- | ---- | -------- |
✓
|     | SAP2000 | Validation | (Q2) | 2   |     | 100% | All Pass |
| --- | ------- | ---------- | ---- | --- | --- | ---- | -------- |
✓
|     | Total |     |     | 19  |     | 100% | PASS |
| --- | ----- | --- | --- | --- | --- | ---- | ---- |
7 Conclusion
Assignment #4 delivers a production-quality 2D structural FEA solver with comprehen-
sive support for thermal loading and support settlements. The refactored object-oriented
architecture enables extensibility and maintainability while maintaining 100% backward
| compatibility    | with | Assignment | #3. |     |     |     |     |
| ---------------- | ---- | ---------- | --- | --- | --- | --- | --- |
| Key achievements |      | include:   |     |     |     |     |     |
1. Thermal Loading (Q2b): Correct decomposition of a linear thermal pro(cid:28)le into
uniform and gradient components, with proper Fixed-End Force formulation for
both truss and frame elements. Solver results for nodal displacements, member-end
forces, and support reactions are in close agreement with SAP2000 across all (cid:28)ve
| nodes | and four | members. |     |     |     |     |     |
| ----- | -------- | -------- | --- | --- | --- | --- | --- |
2. Settlement Analysis (Q2a): E(cid:30)cient matrix partitioning strategy that enforces
prescribed nodal displacements (2 mm settlement at Node 5) while correctly com-
puting settlement-induced member forces and support reactions across the hybrid
frame-truss structure. All six nodal displacements and (cid:28)ve member tables match
| SAP2000 | within | tolerance. |     |     |     |     |     |
| ------- | ------ | ---------- | --- | --- | --- | --- | --- |
3. Validation: Rigorous SAP2000 comparison with coordinate system transforma-
tions, resulting in numerical agreement within 2% tolerance for all reported quan-
tities.
4. Reliability: Comprehensive testing suite (unit, interface, and regression tests at
100% pass rate) ensures robustness and full backward compatibility with all As-
| signment | #3  | benchmarks. |     |     |     |     |     |
| -------- | --- | ----------- | --- | --- | --- | --- | --- |
The solver is ready for deployment in civil engineering educational and professional
contexts.
| 8 AI | Use Acknowledgement |     |     |     |     |     |     |
| ---- | ------------------- | --- | --- | --- | --- | --- | --- |
Several AI tools were used during the development of this assignment. Claude (An-
thropic), ChatGPT (OpenAI), and Gemini (Google) were used for drafting assistance,
report formatting, and discussion of design approaches. GitHub Copilot was used for
18

| Assignment | #4  |     |     |     |     |     | CE 4011 | - Structural | Analysis Software |
| ---------- | --- | --- | --- | --- | --- | --- | ------- | ------------ | ----------------- |
code sca(cid:27)olding and formatting support within the editor. All four tools were accessed
| using premium-tier |     | subscriptions. |     |     |     |     |     |     |     |
| ------------------ | --- | -------------- | --- | --- | --- | --- | --- | --- | --- |
All structural modeling decisions, matrix library design choices, algorithm imple-
mentation, result interpretation, and (cid:28)nal report content were produced, checked, and
approved by the student. AI tools contributed to drafting speed and formatting quality;
they did not determine any engineering or implementation outcome.
| A Code        |     | References                 |       |            |        |         |         |             |       |
| ------------- | --- | -------------------------- | ----- | ---------- | ------ | ------- | ------- | ----------- | ----- |
| The following |     | (cid:28)les are referenced |       | throughout |        | this    | report: |             |       |
|               |     |                            | Table | 8:         | Source | Code    | Modules |             |       |
| Module        |     |                            |       | Purpose    |        |         |         |             |       |
| parser.py     |     |                            |       | Data       | model  | classes | and     | XML parsing | logic |
element_physics.py Local element sti(cid:27)ness and FEF computation
matrix_assembly.py Global sti(cid:27)ness matrix and load vector assembly
banded_solver.py Linear system solver with banded matrix optimiza-
tion
post_processor.py Result extraction and displacement stitching
| math_utils.py |     |     |     | Matrix | operations |     | and | utilities |     |
| ------------- | --- | --- | --- | ------ | ---------- | --- | --- | --------- | --- |
dof_optimizer.py DOF management and active/restrained partitioning
structural_validator.py Input validation and model sanity checks
| B Notation |     | and    | Conventions      |     |              |        |          |                 |     |
| ---------- | --- | ------ | ---------------- | --- | ------------ | ------ | -------- | --------------- | --- |
|            |     |        | Table            | 9:  | Mathematical |        | Notation |                 |     |
|            |     | Symbol | Meaning          |     |              |        |          |                 |     |
|            |     | E      | Young’s          |     | modulus      |        |          |                 |     |
|            |     | α      | Coe(cid:30)cient |     | of           | linear | thermal  | expansion       |     |
|            |     | A      | Cross-sectional  |     |              | area   |          |                 |     |
|            |     | I      | Second           |     | moment       | of     | inertia  |                 |     |
|            |     | d      | Section          |     | depth        |        |          |                 |     |
|            |     | T ,T   |                  |     |              |        |          |                 |     |
|            |     | u b    | Temperatures     |     |              | at top | and      | bottom surfaces |     |
T
|     |     | uniform | Average     |     | temperature |                  |     |     |     |
| --- | --- | ------- | ----------- | --- | ----------- | ---------------- | --- | --- | --- |
|     |     | ∆T      | Temperature |     |             | di(cid:27)erence |     |     |     |
|     |     | F       | Thermal     |     | axial       | force            |     |     |     |
T
|     |     | M   | Thermal |     | bending | moment |     |     |     |
| --- | --- | --- | ------- | --- | ------- | ------ | --- | --- | --- |
T
19