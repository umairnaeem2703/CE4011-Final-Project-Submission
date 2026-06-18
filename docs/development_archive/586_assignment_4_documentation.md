| CE586 | — Earthquake             | Engineering |
| ----- | ------------------------ | ----------- |
|       | Assignment #4 Submission |             |
Submitted By
|     | Mohammad Umair | Naeem |
| --- | -------------- | ----- |
Student ID: 2416055
June 6, 2026

| CE586 Assignment | 4   |     |     | Mohammad | Umair Naeem | — 2416055 |
| ---------------- | --- | --- | --- | -------- | ----------- | --------- |
Contents
| 1 Introduction  | and Given | Data    |      |               |     | 2   |
| --------------- | --------- | ------- | ---- | ------------- | --- | --- |
| 2 Q1: Equations | of Motion | for Two | Beam | Idealizations |     | 2   |
2.1 Flexurally Rigid Beams . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 2
2.2 Beams with Flexural Stiffness EI . . . . . . . . . . . . . . . . . . . . . . . 4
2.3 Comparison of the Two Beam Idealizations . . . . . . . . . . . . . . . . . . 6
| 3 Q2: Undamped | Eigenvalue | Analysis | for | Rigid-Beam | Model | 7   |
| -------------- | ---------- | -------- | --- | ---------- | ----- | --- |
3.1 Characteristic Polynomial . . . . . . . . . . . . . . . . . . . . . . . . . . . 7
3.2 Eigenvalues and Natural Frequencies . . . . . . . . . . . . . . . . . . . . . 7
3.3 Mode Shapes (Roof-Normalized) . . . . . . . . . . . . . . . . . . . . . . . . 8
| 4 Q3: Response | History | Analysis |     |     |     | 8   |
| -------------- | ------- | -------- | --- | --- | --- | --- |
4.1 Q3a: Modal Properties (L , M , Γ ) . . . . . . . . . . . . . . . . . . . . . 8
|     |     | n   | n n |     |     |     |
| --- | --- | --- | --- | --- | --- | --- |
4.2 Q3b: Equivalent SDOF Displacement Histories D (t) . . . . . . . . . . . . 9
n
4.3 Q3c: Floor Displacements and Story Drifts . . . . . . . . . . . . . . . . . . 10
4.4 Q3d: Story Shear Response Histories . . . . . . . . . . . . . . . . . . . . . 12
4.5 Q3e: Base Overturning Moment . . . . . . . . . . . . . . . . . . . . . . . . 13
4.6 Q3f: Effective Modal Parameters and Verification . . . . . . . . . . . . . . 14
| 5 Q4: Response | Spectrum | Analysis | and ESLFP |     |     | 16  |
| -------------- | -------- | -------- | --------- | --- | --- | --- |
5.1 Q4a: 5% Elastic Response Spectrum . . . . . . . . . . . . . . . . . . . . . 16
5.2 Q4b: Peak Modal Responses (RSA) . . . . . . . . . . . . . . . . . . . . . . 16
5.3 Q4c: Comparison of RHA and RSA . . . . . . . . . . . . . . . . . . . . . . 18
5.4 Q4d: Equivalent Static Lateral Force Procedure (ESLFP) . . . . . . . . . . 18
5.5 Q4e: Comparison of RHA, RSA, and ESLFP . . . . . . . . . . . . . . . . . 20
| 6 Conclusion       |     |     |     |     |     | 20  |
| ------------------ | --- | --- | --- | --- | --- | --- |
| 7 Acknowledgements |     |     |     |     |     | 21  |
1

| CE586 |              | Assignment | 4   |     |       |     |      |     | Mohammad | Umair Naeem | — 2416055 |     |
| ----- | ------------ | ---------- | --- | --- | ----- | --- | ---- | --- | -------- | ----------- | --------- | --- |
| 1     | Introduction |            |     | and | Given |     | Data |     |          |             |           |     |
This report presents the seismic dynamic analysis of a three-story idealized frame building
subjected to an assigned horizontal ground-motion record. The assignment is solved in
four stages: (1) derivation of the equations of motion for two beam idealizations, (2)
undamped eigenvalue analysis for the flexurally rigid-beam model, (3) modal response
history analysis (RHA), and (4) response spectrum analysis (RSA) combined with the
| equivalent |     | static | lateral | force | procedure |     | (ESLFP). |     |     |     |     |     |
| ---------- | --- | ------ | ------- | ----- | --------- | --- | -------- | --- | --- | --- | --- | --- |
The structure is a three-story frame with massless columns and lumped floor masses.
Axial deformations are neglected. The lateral degrees of freedom are
|     |     |     |     |     |     |     |     |    |    |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
u (t)
1
|     |     |     |     |     |     | u(t) | =   | u (t), |     |     |     | (1) |
| --- | --- | --- | --- | --- | --- | ---- | --- | -------- | --- | --- | --- | --- |
2
u (t)
3
where u (t) is the lateral displacement of floor i relative to the ground.
i
|     | The | given | structural | properties |     | are |     |     |     |     |     |     |
| --- | --- | ----- | ---------- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
kNm2,
|     |     |     |     | EI  | = 3600 |     |     | h = | 3 m, L | = 4 m. |     | (2) |
| --- | --- | --- | --- | --- | ------ | --- | --- | --- | ------ | ------ | --- | --- |
b
|        | The | floor    | masses | are         |     |       |      |         |       |       |     |     |
| ------ | --- | -------- | ------ | ----------- | --- | ----- | ---- | ------- | ----- | ----- | --- | --- |
|        |     |          |        | m           | =   | 20 t, | m    | = 15 t, | m =   | 15 t, |     | (3) |
|        |     |          |        |             | 1   |       | 2    |         | 3     |       |     |     |
| giving | the | diagonal |        | mass matrix |     |       |      |         |       |       |     |     |
|        |     |          |        |             |     |       |  20 | 0       | 0    |       |     |     |
|        |     |          |        |             |     | M =   | 0   | 15      | 0 t. |       |     | (4) |
|        |     |          |        |             |     |       | 0    | 0       | 15    |       |     |     |
1]T.
The influence vector for horizontal base excitation is ι = [1, 1, The general
| equation |     | of motion |     | is                  |     |     |     |     |         |      |     |     |
| -------- | --- | --------- | --- | ------------------- | --- | --- | --- | --- | ------- | ---- | --- | --- |
|          |     |           |     | Mu¨(t)+Cu˙(t)+Ku(t) |     |     |     |     | = −Mιu¨ | (t). |     | (5) |
g
|     | The | column | stiffness | properties |     | per | story | are: |     |     |     |     |
| --- | --- | ------ | --------- | ---------- | --- | --- | ----- | ---- | --- | --- | --- | --- |
(cid:136)
Story 1 & 2: two columns each with 2EI ⇒ ΣEI = 4EI per story.
c
(cid:136)
|     | Story | 3:  | two columns |     | each | with | EI  | ⇒ ΣEI | = 2EI. |     |     |     |
| --- | ----- | --- | ----------- | --- | ---- | ---- | --- | ----- | ------ | --- | --- | --- |
c
| 2   | Q1:        | Equations |       | of    | Motion |     | for | Two | Beam | Idealizations |     |     |
| --- | ---------- | --------- | ----- | ----- | ------ | --- | --- | --- | ---- | ------------- | --- | --- |
| 2.1 | Flexurally |           | Rigid | Beams |        |     |     |     |      |               |     |     |
When the beams are assumed to be flexurally rigid, joint rotations are fully suppressed
and the structure behaves as a pure shear frame. The lateral stiffness of each story is
| obtained |     | from | the fixed-fixed |     | column |     | formula. |     |     |     |     |     |
| -------- | --- | ---- | --------------- | --- | ------ | --- | -------- | --- | --- | --- | --- | --- |
2

CE586 Assignment 4 Mohammad Umair Naeem — 2416055
Step 1: Story Stiffness Coefficients
The lateral stiffness of one column with height h and flexural rigidity EI under double-
c
curvature bending is 12EI /h3. Summing over both columns in each story:
c
Story 1 and Story 2 (ΣEI = 4EI = 4×3600 = 14400 kNm2):
c
12(ΣEI ) 12(14400) 172800
c
k = k = = = = 6400 kN/m. (6)
1 2 h3 33 27
Story 3 (ΣEI = 2EI = 2×3600 = 7200 kNm2):
c
12(ΣEI ) 12(7200) 86400
c
k = = = = 3200 kN/m. (7)
3 h3 33 27
Step 2: Stiffness Matrix Assembly by Unit Displacement Method
Inducing u = 1 (others zero): Forces required at each floor are
1
K = k +k = 6400+6400 = 12800 kN/m, (8)
11 1 2
K = −k = −6400 kN/m, (9)
21 2
K = 0. (10)
31
Inducing u = 1 (others zero):
2
K = −k = −6400 kN/m, (11)
12 2
K = k +k = 6400+3200 = 9600 kN/m, (12)
22 2 3
K = −k = −3200 kN/m. (13)
32 3
Inducing u = 1 (others zero):
3
K = 0, (14)
13
K = −k = −3200 kN/m, (15)
23 3
K = k = 3200 kN/m. (16)
33 3
The assembled rigid-beam stiffness matrix is therefore:
   
k +k −k 0 12800 −6400 0
1 2 2
K rigid =  −k 2 k 2 +k 3 −k 3 = −6400 9600 −3200 kN/m. (17)
0 −k k 0 −3200 3200
3 3
Step 3: Rayleigh Damping Matrix
Rayleigh damping with ζ = ζ = 0.05 is enforced using the natural frequencies from the
1 2
eigenvalue analysis in Q2 (ω = 8.574 rad/s, ω = 19.537 rad/s). The coefficients satisfy
1 2
 1 ω 
1
(cid:20) (cid:21) (cid:20) (cid:21)
2ω 2 α 0.05
 1  = . (18)
 1 ω 2  β 0.05
2ω 2
2
Using the closed-form solution for equal damping in two modes:
2ω ω 2(8.574)(19.537)
α = ζ 1 2 = 0.05· = 0.5959 s−1, (19)
ω +ω 8.574+19.537
1 2
3

| CE586 | Assignment        | 4   |            |       |         |              |     | Mohammad |            | Umair | Naeem | —   | 2416055 |
| ----- | ----------------- | --- | ---------- | ----- | ------- | ------------ | --- | -------- | ---------- | ----- | ----- | --- | ------- |
|       |                   |     |            | 2     |         |              |     | 2        |            |       |       |     |         |
|       |                   | β   | = ζ        |       | = 0.05· |              |     |          | = 0.003557 |       | s.    |     | (20)    |
|       |                   |     | ω          | +ω    |         | 8.574+19.537 |     |          |            |       |       |     |         |
|       |                   |     |            | 1     | 2       |              |     |          |            |       |       |     |         |
| The   | mass-proportional |     |            | term: |         |              |     |          |            |       |       |     |         |
|       |                   |     |            |       |        |              |   |          |            |       |      |     |         |
|       |                   |     |            |       | 20      | 0 0          |     | 11.918   | 0          |       | 0     |     |         |
|       |                   | αM  | = 0.59590 |       |         | 15 0        | =   | 0        | 8.939      |       | 0 .  |     | (21)    |

|     |                        |     |       |       | 0     | 0 15 |     | 0      | 0   | 8.939   |     |     |     |
| --- | ---------------------- | --- | ----- | ----- | ----- | ---- | --- | ------ | --- | ------- | --- | --- | --- |
| The | stiffness-proportional |     |       | term: |       |      |     |        |     |         |     |     |     |
|     |                        |     |      |       |       |      |    |       |     |         |     |    |     |
|     |                        |     | 12800 |       | −6400 |      | 0   | 45.530 |     | −22.765 |     | 0   |     |
βK = 0.003557−6400 9600 −3200 = −22.765 34.147 −11.382. (22)
rigid
|        |        |          | 0       |        | −3200     | 3200     |     |         | 0          | −11.382 |        | 11.382 |      |
| ------ | ------ | -------- | ------- | ------ | --------- | -------- | --- | ------- | ---------- | ------- | ------ | ------ | ---- |
| Adding | both   | terms:   |         |        |           |          |     |         |            |         |        |        |      |
|        |        |          |         |        |           |         |     |         |            |         |       |        |      |
|        |        |          |         |        |           | 57.451   |     | −22.767 |            | 0       |        |        |      |
|        | C      | =        | αM+βK   |        | =         | −22.767 |     | 43.086  | −11.382   |         | kNs/m. |        | (23) |
|        |        | rigid    |         | rigid  |           |          |     |         |            |         |        |        |      |
|        |        |          |         |        |           |          | 0   | −11.382 | 20.321     |         |        |        |      |
| Case 1 | — Full | Equation | of      | Motion |           |          |     |         |            |         |        |        |      |
|        |        |         |         |        |          |         |     |         |            |         |       |        |      |
|        |        |          | 20 0    | 0      |           | 57.451   |     | −22.767 |            | 0       |        |        |      |
|        |        | 0       | 15      | 0u¨   | +−22.767 |          |     | 43.086  | −11.382u˙ |         |        |        |      |
|        |        |          | 0 0     | 15     |           |          | 0   | −11.382 | 20.321     |         |        |        |      |
|        |        |          |        |        |           |          |     |        |           |        |        |        |      |
|        |        |          |         | 12800  | −6400     |          | 0   |         | 20         |         |        |        |      |
|        |        |          | +−6400 |        | 9600      | −3200u  |     | =       | −15u¨    | (t).    |        |        | (24) |
g
|           |     |      |          | 0   | −3200     |     | 3200 |     | 15  |     |     |     |     |
| --------- | --- | ---- | -------- | --- | --------- | --- | ---- | --- | --- | --- | --- | --- | --- |
| 2.2 Beams |     | with | Flexural |     | Stiffness | EI  |      |     |     |     |     |     |     |
When the beams have finite flexural stiffness, joint rotations must be included. Exploiting
the symmetry of the frame under lateral loading (both joints at a given floor rotate by
]T
the same amount), we define 6 DOFs: 3 lateral translations [u ,u ,u and 3 symmetric
|                 |      |            |        |           |     |     |     |     |     | 1 2 | 3   |     |     |
| --------------- | ---- | ---------- | ------ | --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| joint rotations |      | [θ ,θ      | ,θ ]T. |           |     |     |     |     |     |     |     |     |     |
|                 |      | 1          | 2 3    |           |     |     |     |     |     |     |     |     |     |
| Step 1:         | Beam | Rotational |        | Stiffness |     |     |     |     |     |     |     |     |     |
For a beam of span L = 4 m with both ends undergoing equal rotation θ, the restoring
moment at each joint contributed by one beam is 6EI /L. With two joints per floor (both
b
rotating equally), the effective rotational stiffness added to the diagonal of K per floor
θθ
is:
|     |     |     | 6EI  |     | 12×3600 |     | 43200 |     |       |          |     |     |      |
| --- | --- | --- | ---- | --- | ------- | --- | ----- | --- | ----- | -------- | --- | --- | ---- |
|     |     | K   | = 2· | b   | =       |     | =     | =   | 10800 | kNm/rad. |     |     | (25) |
b
|          |             |              |           | L      |     | 4   |           | 4      |          |     |     |     |      |
| -------- | ----------- | ------------ | --------- | ------ | --- | --- | --------- | ------ | -------- | --- | --- | --- | ---- |
| Step 2:  | Unit        | Displacement |           | Method | —   | 6×6 | Stiffness | Matrix |          |     |     |     |      |
| The full | partitioned |              | stiffness | matrix |     | is  |           |        |          |     |     |     |      |
|          |             |              |           |        |     |     | (cid:20)  |        | (cid:21) |     |     |     |      |
|          |             |              |           |        |     |     | K         | K      |          |     |     |     |      |
|          |             |              |           |        | K   | =   | tt        | tθ     | ,        |     |     |     | (26) |
structure
|     |     |     |     |     |     |     | K   | K   |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     | θt  | θθ  |     |     |     |     |     |
4

| CE586 | Assignment |     | 4   |     |     |     |     |     | Mohammad |     | Umair | Naeem — | 2416055 |
| ----- | ---------- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | ----- | ------- | ------- |
where the translational sub-block K is identical to K (columns resist shear irrespec-
|      |         |               |     |     |     | tt  |     |     | rigid |     |     |     |     |
| ---- | ------- | ------------- | --- | --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- |
| tive | of beam | flexibility). |     |     |     |     |     |     |       |     |     |     |     |
Coupling sub-block K (column end-moment due to unit joint rotation, using
tθ
| M   | = 6EI | /h2): |     |     |     |     |     |     |     |     |     |     |     |
| --- | ----- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
c
Apply θ = 1: moment at floor 1 due to story-1 columns = 6(4EI)/h2 = 6(14400)/9 =
1
9600 kNm. Column shear above = 6(14400)/9 = 9600. Coupling entries:
|     |     |     |     |     |       |       |     |       |          |     |     |     |      |
| --- | --- | --- | --- | --- | ------ | ----- | --- | ----- | --------- | --- | --- | --- | ---- |
|     |     |     |     |     | 0      | 9600  |     | 0     |           |     |     |     |      |
|     |     |     |     | K = | −9600 | −4800 |     | 4800  | kN/m·rad. |     |     |     | (27) |
|     |     |     |     | tθ  |        |       |     |       |          |     |     |     |      |
|     |     |     |     |     | 0      | −4800 |     | −4800 |           |     |     |     |      |
Rotational sub-block K (using M = 4EI /h for near end, M = 2EI /h for far
|      |      |      |              |     | θθ   |     |     | c   |     |     |     | c   |     |
| ---- | ---- | ---- | ------------ | --- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
| end, | plus | beam | contribution |     | K ): |     |     |     |     |     |     |     |     |
b
|     | Apply | θ = | 1:  |     |     |     |     |     |     |     |     |     |     |
| --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
1
|     |     |     |     |     | 4(4EI) | 4(4EI)  |     |      |          |          |     |     |     |
| --- | --- | --- | --- | --- | ------ | ------- | --- | ---- | -------- | -------- | --- | --- | --- |
|     |     |     | K   | =   |        | +       | +K  | =    | 49200    | kNm/rad, |     |     |     |
|     |     |     |     | 44  | h      | h       |     | b    |          |          |     |     |     |
|     |     |     |     |     | 2(4EI) | 8(3600) |     |      |          |          |     |     |     |
|     |     |     | K   | =   |        | =       | =   | 9600 | kNm/rad. |          |     |     |     |
54
|     |       |     |     |     | h   |     | 3   |     |     |     |     |     |     |
| --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|     | Apply | θ = | 1:  |     |     |     |     |     |     |     |     |     |     |
2
|     |       | 4(4EI) |     | 4(2EI)  |     |      |                  |     |     |     |       |          |     |
| --- | ----- | ------ | --- | ------- | --- | ---- | ---------------- | --- | --- | --- | ----- | -------- | --- |
|     | K     | =      |     | +       | +K  | =    | 19200+9600+10800 |     |     | =   | 39600 | kNm/rad, |     |
|     |       | 55     | h   |         | h   | b    |                  |     |     |     |       |          |     |
|     |       | 2(2EI) |     | 4(3600) |     |      |                  |     |     |     |       |          |     |
|     | K     | =      |     | =       | =   | 4800 | kNm/rad.         |     |     |     |       |          |     |
|     |       | 65     | h   |         | 3   |      |                  |     |     |     |       |          |     |
|     | Apply | θ =    | 1:  |         |     |      |                  |     |     |     |       |          |     |
3
4(2EI)
|     |     |     | K = |     | +K  | = 9600+10800 |     |     | = 20400 | kNm/rad. |     |     | (28) |
| --- | --- | --- | --- | --- | --- | ------------ | --- | --- | ------- | -------- | --- | --- | ---- |
|     |     |     | 66  |     |     | b            |     |     |         |          |     |     |      |
h
|     |     |     |     |     |  49200 | 9600  |     | 0     |         |     |     |     |      |
| --- | --- | --- | --- | --- | ------- | ----- | --- | ----- | -------- | --- | --- | --- | ---- |
|     |     |     |     | K   | = 9600 | 39600 |     | 4800 | kNm/rad. |     |     |     | (29) |
θθ
|     |     |     |     |     |     | 0 4800 |     | 20400 |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------ | --- | ----- | --- | --- | --- | --- | --- |
The complete 6×6 stiffness matrix (units: kN/m and kN·m/rad) is:
|     |     |     |     |       |         |      |       |     |       |       |        |    |     |
| --- | --- | --- | --- | ------ | ------- | ---- | ----- | --- | ----- | ----- | ------ | --- | --- |
|     |     |     |     | 12800  | −6400   |      | 0     |     | 0     | 9600  |        | 0   |     |
|     |     |     |     | −6400 |         | 9600 | −3200 |     | −9600 | −4800 | 4800   |    |     |
|     |     |     |     |       |         |      |       |     |       |       |        |    |     |
|     |     |     |     |        | 0 −3200 |      | 3200  |     | 0     | −4800 | −4800 |     |     |

|             |           | K         | =            |     |         |            |               |      |       |       |       | .  | (30) |
| ----------- | --------- | --------- | ------------ | ---- | ------- | ---------- | ------------- | ---- | ----- | ----- | ----- | --- | ---- |
|             |           | structure |              |      | 0 −9600 |            | 0             |      | 49200 | 9600  |       | 0   |      |
|             |           |           |              |     |         |            |               |      |       |       |       |    |      |
|             |           |           |              |     |         |            |               |      |       |       |       |    |      |
|             |           |           |              | 9600 | −4800   |            | −4800         |      | 9600  | 39600 | 4800  |     |      |
|             |           |           |              |     |         |            |               |      |       |       |       |    |      |
|             |           |           |              |      | 0       | 4800       | −4800         |      | 0     | 4800  | 20400 |     |      |
| Step        | 3: Static |           | Condensation |      |         |            |               |      |       |       |       |     |      |
| Eliminating |           | the       | rotational   |      | DOFs    | via static | condensation: |      |       |       |       |     |      |
|             |           |           |              |      | K∗      | = K        | −K            | K−1K | .     |       |       |     | (31) |
|             |           |           |              |      |         | tt         | tθ            |      | θt    |       |       |     |      |
θθ
5

CE586 Assignment 4 Mohammad Umair Naeem — 2416055
The intermediate product computed in MATLAB is:
 
2518.23 −1064.01 −962.84
∆K = K
tθ
K−
θθ
1K
θt
= −1064.01 3452.15 −722.59 kN/m. (32)
−962.84 −722.59 1497.56
Subtracting from K :
tt
 
10281.77 −5335.99 962.84
K
flex
= −5335.99 6147.85 −2477.41 kN/m. (33)
962.84 −2477.41 1702.44
The eigenvalue analysis and Rayleigh damping for Case 2 were carried out entirely
in MATLAB, yielding the natural frequencies ω = 4.554 rad/s, ω = 14.480 rad/s,
1 2
ω = 28.409 rad/s and the damping coefficients α = 0.34644 s−1, β = 0.0052539 s.
3
 
60.948 −28.035 5.059
C
flex
= −28.035 37.497 −13.016 kNs/m. (34)
5.059 −13.016 14.141
Case 2 — Full Equation of Motion
   
20 0 0 60.948 −28.035 5.059
0 15 0u¨ +−28.035 37.497 −13.016u˙
0 0 15 5.059 −13.016 14.141
   
10281.77 −5335.99 962.84 20
+−5335.99 6147.85 −2477.41u = −15u¨
g
(t). (35)
962.84 −2477.41 1702.44 15
2.3 Comparison of the Two Beam Idealizations
Table 1: Comparison of natural periods for the two beam idealizations.
Mode T Rigid Beams (s) T Flexible Beams (s) Observation
n n
1 0.733 1.380 Large flexibility increase
2 0.322 0.434 Notable period increase
3 0.195 0.221 Smaller but visible increase
The flexible-beam model is considerably softer because joint rotations are no longer sup-
pressed. Static condensation of the rotational DOFs produces a fully-populated 3 × 3
lateral stiffness matrix (note K ̸= 0), in contrast to the tridiagonal form of the rigid-
13
beam case. This reflects physical reality: beam bending distributes local moments to
non-adjacent floors.
6

| CE586 Assignment |          | 4   |     |            |     |          |     | Mohammad |     | Umair Naeem | —     | 2416055 |
| ---------------- | -------- | --- | --- | ---------- | --- | -------- | --- | -------- | --- | ----------- | ----- | ------- |
| 3 Q2:            | Undamped |     |     | Eigenvalue |     | Analysis |     |          | for | Rigid-Beam  | Model |         |
The undamped free-vibration equation for the rigid-beam model is
|     |     |     |     |     |     | Mu¨ +K | u   | = 0. |     |     |     | (36) |
| --- | --- | --- | --- | --- | --- | ------ | --- | ---- | --- | --- | --- | ---- |
rigid
ϕeiωt
Assuming harmonic motion u(t) = leads to the eigenvalue problem
|     |     |     |     | (cid:0) |     | (cid:1) |      |     |       |     |     |      |
| --- | --- | --- | --- | ------- | --- | ------- | ---- | --- | ----- | --- | --- | ---- |
|     |     |     |     | K       | −λM | ϕ       | = 0, | λ   | = ω2. |     |     | (37) |
rigid
| 3.1 Characteristic |       |      | Polynomial |      |     |     |     |     |     |     |     |     |
| ------------------ | ----- | ---- | ---------- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
| Setting            | det(K | −λM) |            | = 0: |     |     |     |     |     |     |     |     |
rigid
|           |                      |             |        |                                     |     |                                 |     |          |       |        |     |      |
| --------- | -------------------- | ----------- | ------- | ----------------------------------- | --- | ------------------------------- | --- | -------- | ----- | ------- | --- | ---- |
|           |                      |             |         | 12800−20λ                           |     | −6400                           |     |          | 0     |         |     |      |
|           |                      |             | det    | −6400                               |     | 9600−15λ                        |     |          | −3200 |  = 0.  |     | (38) |
|           |                      |             |         |                                     | 0   | −3200                           |     | 3200−15λ |       |         |     |      |
| Expanding |                      | along       | the     | first row:                          |     |                                 |     |          |       |         |     |      |
|           |                      |             |         | (cid:2)                             |     |                                 |     |          |       | (cid:3) |     |      |
|           |                      | (12800−20λ) |         | (9600−15λ)(3200−15λ)−(−3200)(−3200) |     |                                 |     |          |       |         |     |      |
|           |                      |             |         | (cid:2)                             |     |                                 |     | (cid:3)  |       |         |     |      |
|           |                      | −(−6400)    |         | (−6400)(3200−15λ)−0                 |     |                                 |     |          | = 0.  |         |     | (39) |
| First,    | evaluate             |             | the 2×2 | minor:                              |     |                                 |     |          |       |         |     |      |
|           | (9600−15λ)(3200−15λ) |             |         |                                     |     | = 30720000−144000λ−48000λ+225λ2 |     |          |       |         |     |      |
225λ2
|             |           |       |                   |       |         | =                  | −192000λ+30720000.          |     |     |     |     | (40) |
| ----------- | --------- | ----- | ----------------- | ----- | ------- | ------------------ | --------------------------- | --- | --- | --- | --- | ---- |
| Subtracting |           | 32002 | = 10240000:       |       |         |                    |                             |     |     |     |     |      |
|             |           |       |                   | minor | = 225λ2 | −192000λ+20480000. |                             |     |     |     |     | (41) |
| Second      | cofactor: |       |                   |       |         |                    |                             |     |     |     |     |      |
|             |           |       | (cid:2)           |       |         | (cid:3)            |                             |     |     |     |     |      |
|             | (−6400)   |       | (−6400)(3200−15λ) |       |         |                    | = (−6400)(−20480000+96000λ) |     |     |     |     |      |
|             |           |       |                   |       |         |                    | = 6400(20480000−96000λ).    |     |     |     |     | (42) |
Combining:
(12800−20λ)(225λ2
|                 |         |                      |     | −192000λ+20480000)+6400(20480000−96000λ) |                           |             |     |     |     |      |     | = 0  |
| --------------- | ------- | -------------------- | --- | ---------------------------------------- | ------------------------- | ----------- | --- | --- | --- | ---- | --- | ---- |
| ⇒               | −4500λ3 | +6720000λ2           |     |                                          | −2252800000λ+131072000000 |             |     |     |     | = 0. |     | (43) |
| 3.2 Eigenvalues |         |                      | and | Natural                                  |                           | Frequencies |     |     |     |      |     |      |
| Solving         | the     | cubic characteristic |     |                                          | equation                  | yields:     |     |     |     |      |     |      |
λ = 73.506 rad2/s2, λ = 381.705 rad2/s2, λ = 1038.122 rad2/s2. (44)
|     | 1   |     |     |     | 2   |     |     |     | 3   |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
√
| Natural | circular |     | frequencies: |         | ω   | = λ       |        |      |         |               |     |      |
| ------- | -------- | --- | ------------ | ------- | --- | --------- | ------ | ---- | ------- | ------------- | --- | ---- |
|         |          |     |              |         | n   | n         |        |      |         |               |     |      |
|         |          | ω = | 8.574        | rad/s,  | ω   | = 19.537  | rad/s, |      | ω =     | 32.220 rad/s. |     | (45) |
|         |          | 1   |              |         |     | 2         |        |      | 3       |               |     |      |
| Natural | periods: |     | T =          | 2π/ω    |     |           |        |      |         |               |     |      |
|         |          |     | n            |         | n   |           |        |      |         |               |     |      |
|         |          |     | T            | = 0.733 | s,  | T = 0.322 |        | s, T | = 0.195 | s.            |     | (46) |
|         |          |     | 1            |         |     | 2         |        |      | 3       |               |     |      |
7

| CE586 | Assignment |        | 4   |                   |     |     |     |     | Mohammad | Umair | Naeem — | 2416055 |
| ----- | ---------- | ------ | --- | ----------------- | --- | --- | --- | --- | -------- | ----- | ------- | ------- |
| 3.3   | Mode       | Shapes |     | (Roof-Normalized) |     |     |     |     |          |       |         |         |
The mode shapes are obtained by solving (K − λ M)ϕ = 0 with normalization
|     |     |     |     |     |     |     |     | rigid | n   | n   |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- |
ϕ = 1.0.
3n
Mode 1 (λ = 73.506): From row 1: (12800−20×73.506)ϕ −6400ϕ = 0, giving
|     |     | 1   |     |     |     |     |     |     |     | 11  | 21  |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(12800−1470.12)ϕ = 6400ϕ ⇒ ϕ /ϕ = 11329.88/6400 = 1.770. (47)
|     |     |     |     | 11  |     | 21  |     | 21  | 11  |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Setting ϕ = 1, from row 2: −6400ϕ +(9600−15×73.506)ϕ −3200(1) = 0, solving
|       | 31  |        |     |     |           | 11  |     |     |     | 21  |     |     |
| ----- | --- | ------ | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
| gives | ϕ = | 0.3702 | and | ϕ   | = 0.6554. |     |     |     |     |     |     |     |
|       | 11  |        |     | 21  |           |     |     |     |     |     |     |     |
The MATLAB-computed roof-normalized mode shape matrix (each column is one
mode) is:
|     |     |     |     |     |            |        |         |     |           |    |     |      |
| --- | --- | --- | --- | --- | ----------- | ------ | ------- | --- | --------- | --- | --- | ---- |
|     |     |     |     |     |             | 0.3702 | −0.9778 |     | 3.1075    |     |     |      |
|     |     |     |     |     | Φ = 0.6554 |        | −0.7892 |     | −3.8662. |     |     | (48) |
|     |     |     |     |     |             | 1.0000 | 1.0000  |     | 1.0000    |     |     |      |
Table 2: Undamped eigenvalue analysis results for the flexurally rigid-beam model.
ω2 (rad2/s2)
|     |     |     | Mode |     | λ   | =        |     |     | ω (rad/s) | T (s) |     |     |
| --- | --- | --- | ---- | --- | --- | -------- | --- | --- | --------- | ----- | --- | --- |
|     |     |     |      |     | n   | n        |     |     | n         | n     |     |     |
|     |     |     |      | 1   |     | 73.506   |     |     | 8.574     | 0.733 |     |     |
|     |     |     |      | 2   |     | 381.705  |     |     | 19.537    | 0.322 |     |     |
|     |     |     |      | 3   |     | 1038.122 |     |     | 32.220    | 0.195 |     |     |
Mode 1 is the dominant lateral deformation mode because it has the longest period
and the smoothest floor displacement pattern. The higher modes introduce sign changes
in the mode shapes, so they are more important for force variation than for overall roof
displacement.
| 4 Q3: | Response |     |     | History |     | Analysis |     |     |     |     |     |     |
| ----- | -------- | --- | --- | ------- | --- | -------- | --- | --- | --- | --- | --- | --- |
All dynamic analyses proceed using the Case 1 (rigid-beam) model. The assigned ground
motion record (PZR23Y08) contains 12500 data points at ∆t = 0.01 s and was converted
| from      | cm/s2 | to m/s2       | before     |            | use. |      |         |     |     |     |     |     |
| --------- | ----- | ------------- | ---------- | ---------- | ---- | ---- | ------- | --- | --- | --- | --- | --- |
| 4.1       | Q3a:  | Modal         | Properties |            |      | (L , | M ,     | Γ ) |     |     |     |     |
|           |       |               |            |            |      | n    | n       | n   |     |     |     |     |
| The modal |       | participation |            | quantities |      | are  | defined | as: |     |     |     |     |
L
|     |     |     | L   | = ϕTMι, |     |     | M = | ϕTMϕ | ,   | Γ = n . |     | (49) |
| --- | --- | --- | --- | ------- | --- | --- | --- | ---- | --- | ------- | --- | ---- |
|     |     |     |     | n       |     |     | n   |      | n   | n       |     |      |
|     |     |     |     |         | n   |     |     | n    |     | M       |     |      |
n
| Mode | 1:  |     |     |     |     |     |     |     |     |     |     |     |
| ---- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
L = (0.3702)(20)(1)+(0.6554)(15)(1)+(1.0000)(15)(1) = 32.235 t, (50)
1
M = (0.3702)2(20)+(0.6554)2(15)+(1.0000)2(15) = 24.188 t, (51)
1
|     | Γ   | = 32.235/24.188 |     |     | =   | 1.3328. |     |     |     |     |     | (52) |
| --- | --- | --------------- | --- | --- | --- | ------- | --- | --- | --- | --- | --- | ---- |
1
8

| CE586 Assignment |     | 4   |     |     |     |     |     | Mohammad |     | Umair | Naeem | —   | 2416055 |
| ---------------- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | ----- | ----- | --- | ------- |
| Mode             | 2:  |     |     |     |     |     |     |          |     |       |       |     |         |
L = (−0.9778)(20)+(−0.7892)(15)+(1.0000)(15) = −16.394 t, (53)
2
M = (−0.9778)2(20)+(−0.7892)2(15)+(1.0000)2(15) = 43.470 t, (54)
2
|     | Γ   | = −16.394/43.470 |     |     | = −0.3771. |     |     |     |     |     |     |     | (55) |
| --- | --- | ---------------- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | ---- |
2
| Mode | 3:  |                                           |     |     |     |     |     |     |     |          |     |     |      |
| ---- | --- | ----------------------------------------- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | --- | ---- |
|      | L   | = (3.1075)(20)+(−3.8662)(15)+(1.0000)(15) |     |     |     |     |     |     |     | = 19.157 | t,  |     | (56) |
3
M = (3.1075)2(20)+(−3.8662)2(15)+(1.0000)2(15) = 432.810 t, (57)
3
|     | Γ   | = 19.157/432.810 |     |     | = 0.0443. |     |     |     |     |     |     |     | (58) |
| --- | --- | ---------------- | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | ---- |
3
|     |     |     | Table | 3:  | Modal   | participation |         | quantities. |        |     |     |     |     |
| --- | --- | --- | ----- | --- | ------- | ------------- | ------- | ----------- | ------ | --- | --- | --- | --- |
|     |     |     | Mode  |     | L       | (t)           | M (t)   |             | Γ      |     |     |     |     |
|     |     |     |       |     |         | n             | n       |             | n      |     |     |     |     |
|     |     |     |       | 1   | 32.237  |               | 24.186  |             | 1.3329 |     |     |     |     |
|     |     |     |       | 2   | −16.394 |               | 43.465  | −0.3772     |        |     |     |     |     |
|     |     |     |       | 3   | 19.158  |               | 432.349 |             | 0.0443 |     |     |     |     |
Mode 1 carries most of the effective modal mass, so it controls the main displacement
response. Modes 2 and 3 still need to be retained because their force patterns affect story
| shears and | drift      | distribution. |      |     |              |     |     |           |     |       |     |     |     |
| ---------- | ---------- | ------------- | ---- | --- | ------------ | --- | --- | --------- | --- | ----- | --- | --- | --- |
| 4.2 Q3b:   | Equivalent |               | SDOF |     | Displacement |     |     | Histories |     | D (t) |     |     |     |
n
| For each | mode | n, the | governing |        | uncoupled |             | SDOF | equation | is:   |      |     |     |      |
| -------- | ---- | ------ | --------- | ------ | --------- | ----------- | ---- | -------- | ----- | ---- | --- | --- | ---- |
|          |      |        | D ¨       | (t)+2ζ | ω         | D ˙ (t)+ω2D |      | (t)      | = −u¨ | (t). |     |     | (59) |
|          |      |        | n         |        | n         | n n         | n    | n        | g     |      |     |     |      |
The Newmark constant-average-acceleration method was used for numerical integra-
tion with:
| (cid:136) k ˆ  | = ω2 +(2/∆t)c |     | +(4/∆t2), |       |     | where | c = 2ζ | ω   |     |     |     |     |     |
| -------------- | ------------- | --- | --------- | ----- | --- | ----- | ------ | --- | --- | --- | --- | --- | --- |
|                | n             |     | n         |       |     |       | n      | n n |     |     |     |     |     |
| (cid:136) ∆pˆ= | ∆p+[(4/∆t)+2c |     |           | ]D+2D | ˙   | ¨     |        |     |     |     |     |     |     |
n
| (cid:136) |     | ˆ   |     |     |     |     |     |     |     |     |     |     |     |
| --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
∆D = ∆pˆ/k, then increments in velocity and acceleration follow.
Table 4: Maximum equivalent SDOF displacement responses D (t).
n
|     |     | SDOF | System | T     | (s) | ζ    | Peak | |D |    | (cm) | Time   | (s) |     |     |
| --- | --- | ---- | ------ | ----- | --- | ---- | ---- | ------- | ---- | ------ | --- | --- | --- |
|     |     |      |        |       | n   | n    |      | n       | max  |        |     |     |     |
|     |     | Mode | 1      | 0.733 |     | 0.05 |      | 17.5239 |      | 85.540 |     |     |     |
|     |     | Mode | 2      | 0.322 |     | 0.05 |      | 7.7035  |      | 85.640 |     |     |     |
|     |     | Mode | 3      | 0.195 |     | 0.05 |      | 1.6899  |      | 85.580 |     |     |     |
9

| CE586 Assignment |     | 4   |     |     |     |     | Mohammad | Umair Naeem | —   | 2416055 |
| ---------------- | --- | --- | --- | --- | --- | --- | -------- | ----------- | --- | ------- |
Figure 1: Q3b equivalent SDOF displacement histories for the first three modes.
| 4.3 Q3c:      | Floor | Displacements |     |     | and | Story | Drifts |     |     |     |
| ------------- | ----- | ------------- | --- | --- | --- | ----- | ------ | --- | --- | --- |
| Step 1: Modal |       | Superposition |     |     |     |       |        |     |     |     |
The physical floor displacements are reconstructed by summing modal contributions:
3
(cid:88)
|     |     |     |     | u(t) | =   | Γ   | ϕ D (t). |     |     | (60) |
| --- | --- | --- | --- | ---- | --- | --- | -------- | --- | --- | ---- |
|     |     |     |     |      |     |     | n n n    |     |     |      |
n=1
| Computing |     | the scaled | mode | shape | vectors |     | Γ ϕ : |     |     |     |
| --------- | --- | ---------- | ---- | ----- | ------- | --- | ----- | --- | --- | --- |
n n
|           |              |       |           |                  |            |         |           |      |     |      |
| --------- | ------------ | ----- | --------- | ---------------- | ----------- | ------- | ------------ | ---- | --- | ---- |
|           |              |       |           |                  | 0.3702      |         | 0.4934       |      |     |      |
|           |              |       | Γ ϕ =     | 1.33290.6554   |             |         | = 0.8739,  |      |     | (61) |
|           |              |       | 1 1       |                  |             |         |              |      |     |      |
|           |              |       |           |                  | 1.0000      |         | 1.3329       |      |     |      |
|           |              |       |           |                  |            |         |            |     |     |      |
|           |              |       |           |                  |             | −0.9778 | 0.3688       |      |     |      |
|           |              |       | Γ ϕ =     | −0.3772−0.7892 |             |         | =  0.2977   | ,   |     | (62) |
|           |              |       | 2 2       |                  |             |         |              |      |     |      |
|           |              |       |           |                  |             | 1.0000  | −0.3772      |      |     |      |
|           |              |       |           |                  |            |         |            |     |     |      |
|           |              |       |           |                  |             | 3.1075  | 0.1377       |      |     |      |
|           |              |       | Γ ϕ =     | 0.0443−3.8662  |             |         | = −0.1713. |      |     | (63) |
|           |              |       | 3 3       |                  |             |         |              |      |     |      |
|           |              |       |           |                  |             | 1.0000  | 0.0443       |      |     |      |
| The floor | displacement |       | histories |                  | are:        |         |              |      |     |      |
|           |              | u (t) | = 0.4934D |                  | (t)+0.3688D |         | (t)+0.1377D  | (t), |     | (64) |
|           |              | 1     |           |                  | 1           |         | 2            | 3    |     |      |
|           |              | u (t) | = 0.8739D |                  | (t)+0.2977D |         | (t)−0.1713D  | (t), |     | (65) |
|           |              | 2     |           |                  | 1           |         | 2            | 3    |     |      |
|           |              | u (t) | = 1.3329D |                  | (t)−0.3772D |         | (t)+0.0443D  | (t). |     | (66) |
|           |              | 3     |           |                  | 1           |         | 2            | 3    |     |      |
10

| CE586 Assignment |     | 4   |     |     |     | Mohammad |     | Umair | Naeem — 2416055 |
| ---------------- | --- | --- | --- | --- | --- | -------- | --- | ----- | --------------- |
Figure 2: Q3c floor displacement histories from modal superposition.
| Step 2: Story | Drift | Histories |     |     |     |     |     |     |     |
| ------------- | ----- | --------- | --- | --- | --- | --- | --- | --- | --- |
∆ (t) = u (t), ∆ (t) = u (t)−u (t), ∆ (t) = u (t)−u (t). (67)
|     | 1   | 1     | 2                | 2     | 1        |       | 3        | 3        | 2   |
| --- | --- | ----- | ---------------- | ----- | -------- | ----- | -------- | -------- | --- |
|     |     | Table | 5: Peak          | story | relative | drift | summary. |          |     |
|     |     | Story | Drift Expression |       | Peak     | |∆    | | (cm)   | Time (s) |     |
i
|     |     | 1st | max|u | (t)| |     | 9.6546 |     | 85.520 |     |
| --- | --- | --- | ----- | ---- | --- | ------ | --- | ------ | --- |
1
|     |     | 2nd | max|u (t)−u | (t)| |     | 7.0737  |     | 85.560 |     |
| --- | --- | --- | ----------- | ---- | --- | ------- | --- | ------ | --- |
|     |     |     | 2           | 1    |     |         |     |        |     |
|     |     | 3rd | max|u (t)−u | (t)| |     | 11.4220 |     | 85.820 |     |
|     |     |     | 3           | 2    |     |         |     |        |     |
The largest drift occurs in the third story, even though the roof displacement is mainly
first-mode dominated. This indicates that higher-mode curvature changes the relative
| floor movement |     | near the | top of the | frame. |     |     |     |     |     |
| -------------- | --- | -------- | ---------- | ------ | --- | --- | --- | --- | --- |
11

| CE586 | Assignment |     | 4   |     |     | Mohammad | Umair |     | Naeem — | 2416055 |
| ----- | ---------- | --- | --- | --- | --- | -------- | ----- | --- | ------- | ------- |
Figure 3: Q3c story drift histories from response history analysis.
| 4.4 Q3d:       |       | Story  | Shear    | Response     | Histories |          |     |     |     |      |
| -------------- | ----- | ------ | -------- | ------------ | --------- | -------- | --- | --- | --- | ---- |
| Step 1:        | Modal | Floor  | Force    | Vectors      |           |          |     |     |     |      |
| The equivalent |       | static | lateral  | force vector | for mode  | n is:    |     |     |     |      |
|                |       |        |          | f (t)        | = Γ Mϕ    | ω2D (t). |     |     |     | (68) |
|                |       |        |          | n            | n n       | n n      |     |     |     |      |
| Mode           | 1     | (ω2 =  | 73.506): |              |           |          |     |     |     |      |
1
|     |     |     |       |  20×0.3702                |    |     |     |     |     |     |
| --- | --- | --- | ----- | -------------------------- | --- | --- | --- | --- | --- | --- |
|     |     | f   | (t) = | 1.332915×0.6554(73.506)D |     | (t) |     |     |     |     |
|     |     | 1   |       |                            |     | 1   |     |     |     |     |
15×1.0000
|      |     |       |           |                       |    |               |       |      |     |      |
| ---- | --- | ----- | --------- | ---------------------- | --- | -------------- | ------ | ---- | --- | ---- |
|      |     |       |           | 7.404                  |     |                | 725.5  |      |     |      |
|      |     |       | =         | 1.33299.831(73.506)D |     | (t) = 961.8D |        | (t). |     | (69) |
|      |     |       |           |                        |     | 1              |        | 1    |     |      |
|      |     |       |           | 15.000                 |     |                | 1471.4 |      |     |      |
| Mode | 2   | (ω2 = | 381.705): |                        |     |                |        |      |     |      |
2
|     |     |     |     |             |    |     |      |     |    |     |
| --- | --- | --- | --- | ------------ | --- | --- | ----- | --- | --- | --- |
|     |     |     |     | 20×(−0.9778) |     |     | 281.5 |     |     |     |
f (t) = −0.377215×(−0.7892)(381.705)D (t) = 169.9 D (t). (70)
|      | 2   |       |            |           |     | 2   |       |     | 2   |     |
| ---- | --- | ----- | ---------- | --------- | --- | --- | ------ | --- | --- | --- |
|      |     |       |            | 15×1.0000 |     |     | −216.1 |     |     |     |
| Mode | 3   | (ω2 = | 1038.122): |           |     |     |        |     |     |     |
3
|     |     |     |     |          |    |     |      |     |    |     |
| --- | --- | --- | --- | --------- | --- | --- | ----- | --- | --- | --- |
|     |     |     |     | 20×3.1075 |     |     | 285.8 |     |     |     |
f (t) = 0.044315×(−3.8662)(1038.122)D (t) = −266.6D (t). (71)
|     | 3   |     |     |           |     | 3   |      |     | 3   |     |
| --- | --- | --- | --- | --------- | --- | --- | ---- | --- | --- | --- |
|     |     |     |     | 15×1.0000 |     |     | 68.5 |     |     |     |
12

| CE586 Assignment |              | 4    |             |         |           |         |       | Mohammad |        | Umair Naeem | —   | 2416055 |
| ---------------- | ------------ | ---- | ----------- | ------- | --------- | ------- | ----- | -------- | ------ | ----------- | --- | ------- |
| Step 2:          | Story Shears |      | by Top-Down |         | Summation |         |       |          |        |             |     |         |
| Total floor      | forces:      | f(t) | = f         | (t)+f   | (t)+f     | (t).    |       |          |        |             |     |         |
|                  |              |      | 1           |         | 2         | 3       |       |          |        |             |     |         |
|                  |              |      |             | V       | (t) =     | f (t),  |       |          |        |             |     | (72)    |
|                  |              |      |             | 3       |           | 3       |       |          |        |             |     |         |
|                  |              |      |             | V       | (t) =     | f (t)+f | (t),  |          |        |             |     | (73)    |
|                  |              |      |             | 2       |           | 3       | 2     |          |        |             |     |         |
|                  |              |      |             | V       | (t) =     | f (t)+f | (t)+f |          | (t).   |             |     | (74)    |
|                  |              |      |             | 1       |           | 3       | 2     |          | 1      |             |     |         |
|                  |              |      | Table       | 6: Peak | story     |         | shear | summary  | (RHA). |             |     |         |
|                  |              |      | Story       |         | Shear     | Peak    | |V    | | (kN)   | Time   | (s)         |     |         |
i
|     |     |     | 1st (Base) |     | V   |     | 617.90 |     |     | 85.520 |     |     |
| --- | --- | --- | ---------- | --- | --- | --- | ------ | --- | --- | ------ | --- | --- |
1
|     |     |     | 2nd |     | V   |     | 452.72 |     |     | 85.560 |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------ | --- | --- | ------ | --- | --- |
2
|     |     |     | 3rd (Roof) |     | V   |     | 365.50 |     |     | 85.820 |     |     |
| --- | --- | --- | ---------- | --- | --- | --- | ------ | --- | --- | ------ | --- | --- |
3
Story shears are less purely first-mode controlled than displacements. The higher
modesaddfloor-forcereversals, whichchangesthepeaksheardistributionbetweenstories.
|          |      |             | Figure | 4:  | Q3d story |     | shear | response | histories. |     |     |     |
| -------- | ---- | ----------- | ------ | --- | --------- | --- | ----- | -------- | ---------- | --- | --- | --- |
| 4.5 Q3e: | Base | Overturning |        |     | Moment    |     |       |          |            |     |     |     |
3
(cid:88)
|     |     | M   | (t) = | f   | (t)h | = f | (t)(3)+f | (t)(6)+f |     | (t)(9). |     | (75) |
| --- | --- | --- | ----- | --- | ---- | --- | -------- | -------- | --- | ------- | --- | ---- |
|     |     |     | b     |     | i    | i 1 |          | 2        |     | 3       |     |      |
i=1
13

| CE586 Assignment |     | 4   |           |         |      |             |             | Mohammad |      | Umair Naeem | —   | 2416055 |
| ---------------- | --- | --- | --------- | ------- | ---- | ----------- | ----------- | -------- | ---- | ----------- | --- | ------- |
|                  |     |     | Table     | 7: Peak | base | overturning |             | moment   |      | (RHA).      |     |         |
|                  |     |     | Parameter |         |      | Peak        | |M | (kN·m) |          | Time | (s)         |     |         |
b
|     |     |     | Base | M   |     |     | 3719.35 |     | 85.550 |     |     |     |
| --- | --- | --- | ---- | --- | --- | --- | ------- | --- | ------ | --- | --- | --- |
b
The base overturning moment is dominated by forces acting at larger heights. There-
fore, the roof and upper-story force contributions have a stronger influence than their
| story shear | values    | alone  | suggest. |        |            |             |     |              |     |          |     |     |
| ----------- | --------- | ------ | -------- | ------ | ---------- | ----------- | --- | ------------ | --- | -------- | --- | --- |
|             |           |        | Figure   | 5: Q3e | base       | overturning |     | moment       |     | history. |     |     |
| 4.6 Q3f:    | Effective |        | Modal    |        | Parameters |             | and | Verification |     |          |     |     |
| Effective   | Modal     | Masses |          |        |            |             |     |              |     |          |     |     |
L2
|     |     |     |     |     |     | M∗  | n   |     |     |     |     |      |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---- |
|     |     |     |     |     |     |     | =   | .   |     |     |     | (76) |
|     |     |     |     |     |     |     | n M |     |     |     |     |      |
n
|     |     |     |     |     | (32.237)2 |     | 1039.22 |     |        |     |     |      |
| --- | --- | --- | --- | --- | --------- | --- | ------- | --- | ------ | --- | --- | ---- |
|     |     |     | M∗  | =   |           |     | =       | =   | 42.967 | t,  |     | (77) |
1
|     |     |     |     |     | 24.186     |     | 24.186  |     |         |     |     |      |
| --- | --- | --- | --- | --- | ---------- | --- | ------- | --- | ------- | --- | --- | ---- |
|     |     |     |     |     | (−16.394)2 |     | 268.762 |     |         |     |     |      |
|     |     |     | M∗  | =   |            |     | =       |     | = 6.184 | t,  |     | (78) |
2
|     |     |     |     |     | 43.465    |     | 43.465  |     |     |     |     |     |
| --- | --- | --- | --- | --- | --------- | --- | ------- | --- | --- | --- | --- | --- |
|     |     |     |     |     | (19.158)2 |     | 367.029 |     |     |     |     |     |
M∗
|        |          |     |                    | =   |         |     | =        | =   | 0.849 t. |     |     | (79) |
| ------ | -------- | --- | ------------------ | --- | ------- | --- | -------- | --- | -------- | --- | --- | ---- |
|        |          |     |                    | 3   | 432.349 |     | 432.349  |     |          |     |     |      |
|        | (cid:80) |     |                    |     |         |     |          |     |          | ✓   |     |      |
| Check: | M∗       | =   | 42.967+6.184+0.849 |     |         |     | = 50.000 | t   | = m      | .   |     |      |
|        |          | n   |                    |     |         |     |          |     | total    |     |     |      |
14

| CE586 Assignment |         | 4   |     |     |     |     | Mohammad |     | Umair Naeem | —   | 2416055 |
| ---------------- | ------- | --- | --- | --- | --- | --- | -------- | --- | ----------- | --- | ------- |
| Effective Modal  | Heights |     |     |     |     |     |          |     |             |     |         |
ϕTMh
|     |     |     | h∗  | n   |     |     |          | 9]T |     |     |      |
| --- | --- | --- | --- | --- | --- | --- | -------- | --- | --- | --- | ---- |
|     |     |     |     | =   | ,   | h   | = [3, 6, | m.  |     |     | (80) |
|     |     |     | n   | L   |     |     |          |     |     |     |      |
n
| Mode 1: |      |     |                                                 |     |     |     |     |     |     |     |     |
| ------- | ---- | --- | ----------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
|         | ϕTMh | =   | (0.3702)(20)(3)+(0.6554)(15)(6)+(1.0000)(15)(9) |     |     |     |     |     |     |     |     |
1
|     |     | =    | 22.212+58.986+135.000 |     |     |       | = 216.198 |     | tm, |     | (81) |
| --- | --- | ---- | --------------------- | --- | --- | ----- | --------- | --- | --- | --- | ---- |
|     |     | h∗ = | 216.198/32.237        |     | =   | 6.707 | m.        |     |     |     | (82) |
1
| Mode 2: |     |     |     |     |     |     |     |     |     |     |     |
| ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ϕTMh
= (−0.9778)(20)(3)+(−0.7892)(15)(6)+(1.0000)(15)(9)
2
|     |     | = −58.668−71.028+135.000 |     |     |     |     | = 5.304 | tm, |     |     | (83) |
| --- | --- | ------------------------ | --- | --- | --- | --- | ------- | --- | --- | --- | ---- |
h∗
|     |     | = 5.304/(−16.394) |     |     | = −0.323 |     | m.  |     |     |     | (84) |
| --- | --- | ----------------- | --- | --- | -------- | --- | --- | --- | --- | --- | ---- |
2
| Mode 3: |     |     |     |     |     |     |     |     |     |     |     |
| ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ϕTMh
= (3.1075)(20)(3)+(−3.8662)(15)(6)+(1.0000)(15)(9)
3
|     |     | = 186.450−347.958+135.000 |     |     |     |     | = −26.508 |     | tm, |     | (85) |
| --- | --- | ------------------------- | --- | --- | --- | --- | --------- | --- | --- | --- | ---- |
h∗
|     |     | = −26.508/19.158 |     |     | = −1.384 |     | m.  |     |     |     | (86) |
| --- | --- | ---------------- | --- | --- | -------- | --- | --- | --- | --- | --- | ---- |
3
|     |     |      | Table | 8:     | Effective | modal         | parameters. |     |        |     |     |
| --- | --- | ---- | ----- | ------ | --------- | ------------- | ----------- | --- | ------ | --- | --- |
|     |     |      | M∗    |        |           |               |             |     | h∗     |     |     |
|     |     | Mode |       | (t)    | Mass      | Participation |             | (%) | (m)    |     |     |
|     |     |      |       | n      |           |               |             |     | n      |     |     |
|     |     | 1    |       | 42.967 |           | 85.93         |             |     | 6.707  |     |     |
|     |     | 2    |       | 6.184  |           | 12.37         |             |     | −0.323 |     |     |
|     |     | 3    |       | 0.849  |           | 1.70          |             |     | −1.384 |     |     |
The effective modal masses sum to the total structural mass, which confirms that
the three retained modes fully represent the translational DOFs. The negative effective
heights in higher modes reflect modal sign changes, not negative physical floor elevations.
| Invariant SDOF |     | Verification |     |     |     |     |     |     |     |     |     |
| -------------- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
The base shear and overturning moment can be computed alternatively as:
|     |     |       | 3        |     |      |     |          | 3        |       |     |      |
| --- | --- | ----- | -------- | --- | ---- | --- | -------- | -------- | ----- | --- | ---- |
|     |     |       | (cid:88) |     |      |     | (cid:88) |          |       |     |      |
|     |     |       | M∗ω2D    |     |      |     |          | h∗ M∗ω2D |       |     |      |
|     | V   | (t) = |          |     | (t), | M   | (t) =    |          | (t).  |     | (87) |
|     |     | b     |          | n n | n    | b   |          | n        | n n n |     |      |
|     |     |       | n=1      |     |      |     | n=1      |          |       |     |      |
Table 9: Verification: story force summation vs. invariant SDOF formula.
| Parameter        |      |        | Story | Force | Summation |     | Invariant | SDOF    | Formula | |∆|        |     |
| ---------------- | ---- | ------ | ----- | ----- | --------- | --- | --------- | ------- | ------- | ---------- | --- |
| Peak base shear  | (kN) |        |       |       | 617.90    |     |           | 617.90  |         | 3.41×10−13 |     |
| Peak base moment |      | (kN·m) |       |       | 3719.35   |     |           | 3719.35 |         | 2.27×10−12 |     |
The two formulations are algebraically identical; the machine-precision differences
| confirm modal | completeness. |     |     |     |     |     |     |     |     |     |     |
| ------------- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
15

| CE586 Assignment |          | 4       |          |          |     | Mohammad |       | Umair Naeem | —   | 2416055 |
| ---------------- | -------- | ------- | -------- | -------- | --- | -------- | ----- | ----------- | --- | ------- |
| 5 Q4:            | Response |         | Spectrum | Analysis |     | and      | ESLFP |             |     |         |
| 5.1 Q4a:         | 5%       | Elastic | Response | Spectrum |     |          |       |             |     |         |
The 5% damped elastic response spectrum was generated by solving the SDOF equation
for T ∈ [0.02, 3.00] s at ∆T = 0.02 s steps using the same Newmark integration. The
| spectral | quantities | are: |         |            |     |       |          |     |     |      |
| -------- | ---------- | ---- | ------- | ---------- | --- | ----- | -------- | --- | --- | ---- |
|          |            |      | S (T) = | max|D(t)|, | S   | (T) = | ω2S (T). |     |     | (88) |
|          |            |      | d       |            |     | a     | d        |     |     |      |
t
Spectral values interpolated at the structural modal periods are:
Table 10: Response spectrum ordinates at the structural modal periods (ζ = 5%).
|     |     |     | Mode | T (s)   | S (m)  | S      | (g) |     |     |     |
| --- | --- | --- | ---- | ------- | ------ | ------ | --- | --- | --- | --- |
|     |     |     |      | n       | d      | a      |     |     |     |     |
|     |     |     |      | 1 0.733 | 0.1757 | 1.3168 |     |     |     |     |
|     |     |     |      | 2 0.322 | 0.0766 | 2.9812 |     |     |     |     |
|     |     |     |      | 3 0.195 | 0.0162 | 1.7176 |     |     |     |     |
Figure 6: Q4a 5% damped elastic response spectrum for the assigned ground motion.
| 5.2 Q4b: | Peak       | Modal         | Responses | (RSA) |     |     |     |     |     |      |
| -------- | ---------- | ------------- | --------- | ----- | --- | --- | --- | --- | --- | ---- |
| Step 1:  | Peak Modal | Displacements |           |       |     |     |     |     |     |      |
|          |            |               |           | u =   | Γ ϕ | S . |     |     |     | (89) |
|          |            |               |           | n,max | n n | d,n |     |     |     |      |
| Mode     | 1 (S       | = 0.1757      | m):       |       |     |     |     |     |     |      |
d1
|     |     |     |                          |      |     |            |         |    |     |      |
| --- | --- | --- | ------------------------ | ------ | --- | ----------- | ------- | --- | --- | ---- |
|     |     |     |                          | 0.3702 |     |             | 0.08671 |     |     |      |
|     |     | u   | = 1.33290.6554(0.1757) |        |     | = 0.15361 |         | m.  |     | (90) |
1,max
|     |     |     |     | 1.0000 |     |     | 0.23424 |     |     |     |
| --- | --- | --- | --- | ------ | --- | --- | ------- | --- | --- | --- |
16

| CE586 | Assignment |      | 4        |     |     |     |     | Mohammad |     | Umair | Naeem | —   | 2416055 |
| ----- | ---------- | ---- | -------- | --- | --- | --- | --- | -------- | --- | ----- | ----- | --- | ------- |
| Mode  |            | 2 (S | = 0.0766 | m): |     |     |     |          |     |       |       |     |         |
d2
|      |     |      |          |                            |     |  −0.9778 |    |     |  0.02824 |     |    |     |      |
| ---- | --- | ---- | -------- | -------------------------- | --- | --------- | --- | --- | --------- | --- | --- | --- | ---- |
|      |     |      | u        | = −0.3772−0.7892(0.0766) |     |           |     | =   | 0.02281   |     | m.  |     | (91) |
|      |     |      | 2,max    |                            |     |           |     |     |          |     |    |     |      |
|      |     |      |          |                            |     | 1.0000    |     |     | −0.02889  |     |     |     |      |
| Mode |     | 3 (S | = 0.0162 | m):                        |     |           |     |     |           |     |     |     |      |
d3
|     |     |     |     |                           |    |        |    |     |           |     |    |     |      |
| --- | --- | --- | --- | ------------------------- | --- | ------ | --- | --- | ---------- | --- | --- | --- | ---- |
|     |     |     |     |                           |     | 3.1075 |     |     | 0.00223    |     |     |     |      |
|     |     |     | u   | = 0.0443−3.8662(0.0162) |     |        |     | =   | −0.00278 |     | m.  |     | (92) |
3,max
|       |         |         |                 |     |       | 1.0000 |               |     | 0.000717 |     |     |     |     |
| ----- | ------- | ------- | --------------- | --- | ----- | ------ | ------------- | --- | -------- | --- | --- | --- | --- |
| Step  | 2: Peak | Modal   | Forces          | and | Story | Shears |               |     |          |     |     |     |     |
| Modal | floor   | forces: | f               | =   | Γ Mϕ  | S      | .             |     |          |     |     |     |     |
|       |         |         | n,max           |     | n     | n a,n  |               |     |          |     |     |     |     |
| Mode  |         | 1 (S    | = 0.1757×73.506 |     |       | =      | 12.920 m/s2): |     |          |     |     |     |     |
a1
|     |     |     |     |                         |     |      |    |     |         |    |     |     |      |
| --- | --- | --- | --- | ----------------------- | --- | ----- | --- | --- | -------- | --- | --- | --- | ---- |
|     |     |     |     |                         |     | 7.404 |     |     | 127.49   |     |     |     |      |
|     |     |     | f   | = 1.33299.831(12.920) |     |       |     | =   | 169.42 |     | kN. |     | (93) |
1,max
|     |     |     |     |     |     | 15.000 |     |     | 258.35 |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------ | --- | --- | ------ | --- | --- | --- | --- |
Story shears (Mode 1): V = 258.35, V = 427.77, V = 555.26 kN.
|     |     |     |     |     | 31  |     | 21  |     | 11  |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
m/s2):
| Mode |     | 2 (S | = 0.0766×381.705 |     |     | =   | 29.239 |     |     |     |     |     |     |
| ---- | --- | ---- | ---------------- | --- | --- | --- | ------ | --- | --- | --- | --- | --- | --- |
a2
|     |     |     |     |                            |     |        |    |     |         |     |      |     |      |
| --- | --- | --- | --- | -------------------------- | --- | ------- | --- | --- | -------- | --- | ----- | --- | ---- |
|     |     |     |     |                            |     | −19.556 |     |     | 215.53   |     |       |     |      |
|     |     |     | f   | = −0.3772−11.838(29.239) |     |         |     | =   |  130.40 |     |  kN. |     | (94) |
2,max
|     |     |     |     |     |     | 15.000 |     |     | −165.11 |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------ | --- | --- | ------- | --- | --- | --- | --- |
Story shears (Mode 2): V = −165.11, V = −34.71, V = 180.82 kN.
|      |     |      |                   |     | 32  |     | 22              |     | 12  |     |     |     |     |
| ---- | --- | ---- | ----------------- | --- | --- | --- | --------------- | --- | --- | --- | --- | --- | --- |
| Mode |     | 3 (S | = 0.0162×1038.122 |     |     |     | = 16.817 m/s2): |     |     |     |     |     |     |
a3
|     |     |     |     |                           |    |        |    |     |         |    |     |     |      |
| --- | --- | --- | --- | ------------------------- | --- | ------ | --- | --- | -------- | --- | --- | --- | ---- |
|     |     |     |     |                           |     | 62.150 |     |     | 46.30    |     |     |     |      |
|     |     |     | f   | = 0.0443−57.993(16.817) |     |        |     | =   | −43.19 |     | kN. |     | (95) |
3,max
|       |                |                   |       |           |              | 15.000   |             |     | 11.18 |       |     |     |      |
| ----- | -------------- | ----------------- | ----- | --------- | ------------ | -------- | ----------- | --- | ----- | ----- | --- | --- | ---- |
| Story | shears         |                   | (Mode | 3): V     | =            | 11.18,   | V = −31.99, | V   | =     | 14.31 | kN. |     |      |
|       |                |                   |       |           | 33           |          | 23          |     | 13    |       |     |     |      |
| Step  | 3: CQC         | Cross-Correlation |       |           | Coefficients |          |             |     |       |       |     |     |      |
|       |                |                   |       |           | 8ζ2(1+β      |          | )β1.5       |     |       |       | ω   |     |      |
|       |                |                   |       |           |              |          | in          |     |       |       | i   |     |      |
|       |                |                   | ρ     | =         |              |          | in          | ,   | β     | =     | .   |     | (96) |
|       |                |                   | in    | (1−β2     |              |          |             |     |       | in    |     |     |      |
|       |                |                   |       |           |              | )2 +4ζ2β | (1+β        | )2  |       |       | ω   |     |      |
|       |                |                   |       |           | in           |          | in          | in  |       |       | n   |     |      |
| Key   | off-diagonal   |                   | terms | with      | ζ            | = 0.05:  |             |     |       |       |     |     |      |
| β     | = 8.574/19.537 |                   |       | = 0.4389: |              |          |             |     |       |       |     |     |      |
12
|     |     |     |     | 8(0.0025)(1.4389)(0.4389)1.5 |     |     |     |     |     | 0.01183 |            |     |      |
| --- | --- | --- | --- | ---------------------------- | --- | --- | --- | --- | --- | ------- | ---------- | --- | ---- |
|     | ρ   | =   |     |                              |     |     |     |     | =   |         | = 0.02004. |     | (97) |
12
|     |                |     | (1−0.43892)2 |           | +4(0.0025)(0.4389)(1.4389)2 |     |     |     |     | 0.59052 |     |     |     |
| --- | -------------- | --- | ------------ | --------- | --------------------------- | --- | --- | --- | --- | ------- | --- | --- | --- |
| β   | = 8.574/32.220 |     |              | = 0.2662: |                             |     |     |     |     |         |     |     |     |
13
8(0.0025)(1.2662)(0.2662)1.5
|     |                 | ρ   | =               |           |     |                             |     |     |     | ≈   | 0.00440. |     | (98) |
| --- | --------------- | --- | --------------- | --------- | --- | --------------------------- | --- | --- | --- | --- | -------- | --- | ---- |
|     |                 |     | 13 (1−0.26622)2 |           |     | +4(0.0025)(0.2662)(1.2662)2 |     |     |     |     |          |     |      |
| β   | = 19.537/32.220 |     |                 | = 0.6063: |     |                             |     |     |     |     |          |     |      |
23
8(0.0025)(1.6063)(0.6063)1.5
|     |     | ρ   | =   |     |     |     |     |     |     | ≈   | 0.05782. |     | (99) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | --- | ---- |
23
|     |     |     | (1−0.60632)2 |     |     | +4(0.0025)(0.6063)(1.6063)2 |     |     |     |     |     |     |     |
| --- | --- | --- | ------------ | --- | --- | --------------------------- | --- | --- | --- | --- | --- | --- | --- |
All diagonal terms ρ = 1. The small off-diagonal values confirm that modal combi-
nn
| nation | rules | will | yield | similar | SRSS | and | CQC results. |     |     |     |     |     |     |
| ------ | ----- | ---- | ----- | ------- | ---- | --- | ------------ | --- | --- | --- | --- | --- | --- |
17

| CE586 | Assignment |             | 4   |     |     |     |     | Mohammad |     | Umair | Naeem — | 2416055 |
| ----- | ---------- | ----------- | --- | --- | --- | --- | --- | -------- | --- | ----- | ------- | ------- |
| Step  | 4: Modal   | Combination |     |     |     |     |     |          |     |       |         |         |
ABSSUM:
|     |     |     |     |     | r      | = |r | |+|r | |+|r | |.  |     |     | (100) |
| --- | --- | --- | --- | --- | ------ | ---- | ---- | ---- | --- | --- | --- | ----- |
|     |     |     |     |     | ABSSUM |      | 1    | 2    | 3   |     |     |       |
SRSS:
(cid:113)
|     |     |     |     |     | r   | =   | r2 +r2 | +r2. |     |     |     | (101) |
| --- | --- | --- | --- | --- | --- | --- | ------ | ---- | --- | --- | --- | ----- |
SRSS
|     |     |     |     |     |     |     | 1   | 2 3 |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
CQC:
(cid:118)
|     |     |     |     |     |     | (cid:117) 3 | 3   |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ----------- | --- | --- | --- | --- | --- | --- |
(cid:117)(cid:88)(cid:88)
|     |     |     |     |     | r = | (cid:116) |     | ρ r  | r . |     |     | (102) |
| --- | --- | --- | --- | --- | --- | --------- | --- | ---- | --- | --- | --- | ----- |
|     |     |     |     |     | CQC |           |     | in i | n   |     |     |       |
i=1 n=1
| 5.3 | Q4c: | Comparison |     | of  | RHA and | RSA |     |     |     |     |     |     |
| --- | ---- | ---------- | --- | --- | ------- | --- | --- | --- | --- | --- | --- | --- |
Table 11: Comparison of RHA and RSA response quantities (absolute percentage differ-
ences).
|     | Response  |      | RHA     |     | RSA (ABSSUM) |       |     | RSA     | (SRSS) | RSA     | (CQC) |     |
| --- | --------- | ---- | ------- | --- | ------------ | ----- | --- | ------- | ------ | ------- | ----- | --- |
|     | Parameter |      | (Q3)    |     | Value        | |∆|%  |     | Value   | |∆|%   | Value   | |∆|%  |     |
|     | u 1       | (cm) | 9.6546  |     | 11.7217      | 21.41 |     | 9.1240  | 5.50   | 9.1613  | 5.11  |     |
|     | u         | (cm) | 16.0862 |     | 17.9118      | 11.35 |     | 15.5239 | 3.50   | 15.5498 | 3.33  |     |
2
|     | u   | (cm) | 23.2594 |     | 26.3855 | 13.44 |     | 23.6014 | 1.47 | 23.5651 | 1.31 |     |
| --- | --- | ---- | ------- | --- | ------- | ----- | --- | ------- | ---- | ------- | ---- | --- |
3
|     | V   | (kN) | 617.90 |     | 750.19 | 21.41 |     | 583.93 | 5.50 | 586.32 | 5.11 |     |
| --- | --- | ---- | ------ | --- | ------ | ----- | --- | ------ | ---- | ------ | ---- | --- |
1
|     | V   | (kN) | 452.72 |     | 494.52 | 9.23 |     | 430.16 | 4.98 | 429.69 | 5.09 |     |
| --- | --- | ---- | ------ | --- | ------ | ---- | --- | ------ | ---- | ------ | ---- | --- |
2
|     | V   | (kN) | 365.50 |     | 434.93 | 18.99 |     | 306.93 | 16.03 | 304.98 | 16.56 |     |
| --- | --- | ---- | ------ | --- | ------ | ----- | --- | ------ | ----- | ------ | ----- | --- |
3
|     | M   | (kN·m) | 3719.35 |     | 3800.81 | 2.19 |     | 3723.07 | 0.10 | 3722.26 | 0.08 |     |
| --- | --- | ------ | ------- | --- | ------- | ---- | --- | ------- | ---- | ------- | ---- | --- |
b
SRSS and CQC yield very similar results because the modal periods are well-separated
(T /T ≈ 2.28), making cross-modal correlation negligible. ABSSUM is uniformly conser-
1 2
vative. The largest deviations occur in story shears (V : SRSS gives −16%), which are
3
| more       | sensitive | to         | higher-mode |        | contributions. |            |     |           |     |         |     |     |
| ---------- | --------- | ---------- | ----------- | ------ | -------------- | ---------- | --- | --------- | --- | ------- | --- | --- |
| 5.4        | Q4d:      | Equivalent |             | Static | Lateral        | Force      |     | Procedure |     | (ESLFP) |     |     |
| The design |           | spectrum   | prescribed  |        | in the         | assignment |     | is:       |     |         |     |     |

0.6T
|     |     |     |     |     | 0.4+ |     | , 0 | ≤ T ≤ | 0.15 | s,  |     |     |
| --- | --- | --- | --- | --- | ----- | --- | --- | ----- | ---- | --- | --- | --- |

|     |     |     |     |     |    | 0.15 |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- |
 

|     |     |     |      |     | 1.0, |     | 0.15 | < T | ≤ 0.60 | s,  |     |       |
| --- | --- | --- | ---- | --- | ---- | --- | ---- | --- | ------ | --- | --- | ----- |
|     |     |     | A(T) | =   |      |     |      |     |        |     |     | (103) |

|     |     |     |     |     |  (cid:18) | (cid:19)0.8 |     |        |     |     |     |     |
| --- | --- | --- | --- | --- | ---------- | ----------- | --- | ------ | --- | --- | --- | --- |
|     |     |     |     |     |  0.6      |             |     |        |     |     |     |     |
|     |     |     |     |     |          | ,           | T   | > 0.60 | s.  |     |     |     |

T
| Step | 1: Design | Spectral |     | Acceleration | at  | T   |     |     |     |     |     |     |
| ---- | --------- | -------- | --- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- |
1
| Since | T = | 0.733 s | > 0.60 | s:  |     |     |     |     |     |     |     |     |
| ----- | --- | ------- | ------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
1
|     |     |     |     |     | (cid:18) |     | (cid:19)0.8 |     |     |     |     |     |
| --- | --- | --- | --- | --- | -------- | --- | ----------- | --- | --- | --- | --- | --- |
0.6
|     |     |     |     | A(T | ) = |     | =   | (0.8185)0.8. |     |     |     | (104) |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------ | --- | --- | --- | ----- |
1
0.733
18

| CE586 Assignment |     | 4   |     |     |     |     | Mohammad |     | Umair Naeem | —   | 2416055 |
| ---------------- | --- | --- | --- | --- | --- | --- | -------- | --- | ----------- | --- | ------- |
e−0.1602
Computing: ln(0.8185) = −0.2003; 0.8×(−0.2003) = −0.1602; = 0.852.
|     |     |     |     |     | A(T ) = | 0.852g. |     |     |     |     | (105) |
| --- | --- | --- | --- | --- | ------- | ------- | --- | --- | --- | --- | ----- |
1
| Step 2: Base | Shear |     |     |     |     |     |     |     |     |     |     |
| ------------ | ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Total structural weight: W = (20+15+15)×9.81 = 50×9.81 = 490.5 kN.
tot
|                    |          | V         | = A(T )·W |     | = 0.852×490.5     |     | =   | 417.97 | kN.        |     | (106) |
| ------------------ | -------- | --------- | --------- | --- | ----------------- | --- | --- | ------ | ---------- | --- | ----- |
|                    |          | b         | 1         | tot |                   |     |     |        |            |     |       |
| Step 3: Additional |          | Top-Floor | Force     |     |                   |     |     |        |            |     |       |
| For N = 3          | stories: |           |           |     |                   |     |     |        |            |     |       |
|                    | ∆F       | =         | 0.0075×N  | ×V  | = 0.0075×3×417.97 |     |     |        | = 9.40 kN. |     | (107) |
|                    |          | N         |           |     | b                 |     |     |        |            |     |       |
Remaining shear to distribute: V −∆F = 417.97−9.40 = 408.57 kN.
|                     |     |          |     |       | b N    |     |     |     |     |     |     |
| ------------------- | --- | -------- | --- | ----- | ------ | --- | --- | --- | --- | --- | --- |
| Step 4: Height-Mass |     | Products | and | Floor | Forces |     |     |     |     |     |     |
(cid:88)
|     |     | m h | = 20(3)+15(6)+15(9) |     |     | =   | 60+90+135 |     | = 285 tm. |     | (108) |
| --- | --- | --- | ------------------- | --- | --- | --- | --------- | --- | --------- | --- | ----- |
|     |     | j j |                     |     |     |     |           |     |           |     |       |
j
|             |     | 20×3 |           |     | 60              |     |     |     |           |     |       |
| ----------- | --- | ---- | --------- | --- | --------------- | --- | --- | --- | --------- | --- | ----- |
| f = 408.57× |     |      | = 408.57× |     | = 408.57×0.2105 |     |     | =   | 86.00 kN, |     | (109) |
1
|             |     | 285  |           | 285 |                 |     |     |     |            |     |       |
| ----------- | --- | ---- | --------- | --- | --------------- | --- | --- | --- | ---------- | --- | ----- |
|             |     | 15×6 |           |     | 90              |     |     |     |            |     |       |
| f = 408.57× |     |      | = 408.57× |     | = 408.57×0.3158 |     |     | =   | 129.02 kN, |     | (110) |
| 2           |     | 285  |           | 285 |                 |     |     |     |            |     |       |
15×9
f = 408.57× +∆F = 408.57×0.4737+9.40 = 193.55+9.40 = 202.95 kN.
| 3   |     |     | N   |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
285
(111)
| Check: | 86.00+129.02+202.95 |     |     | =   | 417.97 | kN = | V . ✓ |     |     |     |     |
| ------ | ------------------- | --- | --- | --- | ------ | ---- | ----- | --- | --- | --- | --- |
b
| Step 5: Story | Shears      |     |            |               |      |     |        |     |            |     |       |
| ------------- | ----------- | --- | ---------- | ------------- | ---- | --- | ------ | --- | ---------- | --- | ----- |
|               |             | V = | f = 202.94 | kN,           |      |     |        |     |            |     | (112) |
|               |             | 3   | 3          |               |      |     |        |     |            |     |       |
|               |             | V = | f +f =     | 202.94+129.04 |      | =   | 331.96 | ≈   | 331.96 kN, |     | (113) |
|               |             | 2   | 3 2        |               |      |     |        |     |            |     |       |
|               |             | V = | V = 417.97 | kN.           |      |     |        |     |            |     | (114) |
|               |             | 1   | b          |               |      |     |        |     |            |     |       |
| Step 6: Base  | Overturning |     | Moment     |               |      |     |        |     |            |     |       |
|               |             | M   | = f h +f   | h             | +f h |     |        |     |            |     |       |
|               |             | b   | 1 1        | 2 2           | 3 3  |     |        |     |            |     |       |
= 86.00(3)+129.02(6)+202.95(9)
|     |     |     | = 258.00+774.12+1826.55 |     |     |     | = 2858.67 |     | kNm. |     | (115) |
| --- | --- | --- | ----------------------- | --- | --- | --- | --------- | --- | ---- | --- | ----- |
19

CE586 Assignment 4 Mohammad Umair Naeem — 2416055
5.5 Q4e: Comparison of RHA, RSA, and ESLFP
Table 12: Comprehensive comparison of RHA, RSA, and ESLFP with signed percentage
differences.
Response RHA RSA (ABSSUM) RSA (SRSS) RSA (CQC) ESLFP
Parameter (Q3) Value % Value % Value % Value %
u (cm) 9.6546 11.7217 21.41 9.1240 5.50 9.1613 5.11 N/A N/A
1
u (cm) 16.0862 17.9118 11.35 15.5239 3.50 15.5498 3.33 N/A N/A
2
u (cm) 23.2594 26.3855 13.44 23.6014 1.47 23.5651 1.31 N/A N/A
3
V (kN) 617.90 750.19 21.41 583.93 5.50 586.32 5.11 417.97 32.36
1
V (kN) 452.72 494.52 9.23 430.16 4.98 429.69 5.09 331.96 26.68
2
V (kN) 365.50 434.93 18.99 306.93 16.03 304.98 16.56 202.94 44.48
3
M (kN·m) 3719.35 3800.81 2.19 3723.07 0.10 3722.26 0.08 2858.58 23.14
b
Discussion: The ESLFP yields considerably lower base shear and overturning moment
values compared to the RHA and RSA results. This apparent anomaly arises because
the ESLFP uses the code-prescribed design spectrum, while the assigned ground motion
record is significantly more intense at the structural fundamental period (S (T ) = 1.317g
a 1
from the actual record vs. A(T ) = 0.852g from the code). When both methods use the
1
same spectrum, the ESLFP is expected to be conservative relative to SRSS/CQC. The
SRSS and CQC combination rules agree closely with RHA (within 5% for displacements
and base shear), demonstrating their accuracy for this well-separated modal structure.
6 Conclusion
The flexurally rigid-beam model yields a fundamental period of T = 0.733 s, while
1
the condensed flexible-beam model yields T = 1.380 s, demonstrating the significant
1
influence of beam flexibility on lateral stiffness. The eigenvalue analysis confirmed three
well-separated modes with Mode 1 capturing 85.93% of the total structural mass.
Modal RHA showed that the first mode dominates the displacement response. The
effective modal parameter formulation produced base shear and overturning moment his-
tories algebraically identical to those from direct modal superposition, confirming modal
completeness with a machine-precision difference of order 10−12.
The record-specific RSA using SRSS and CQC combination rules agreed with RHA
to within 5% for displacements and base shear. ABSSUM was uniformly conservative by
9–21%. The ESLFP produced lower forces than the dynamic methods because the code
design spectrum is much smoother and less intense than the actual assigned record at the
structural fundamental period.
All computations were performed in MATLAB using the Newmark constant-average-
accelerationmethodfortimeintegration. TheMATLABscriptperformseigenvalueanaly-
sis, response spectrum construction, modal superposition, RSA combination, and ESLFP
calculation in a single parametric workflow.
20

CE586 Assignment 4 Mohammad Umair Naeem — 2416055
7 Acknowledgements
Several AI tools were used during the development of this assignment. Generative AI
tools were used for drafting assistance and report formatting. All structural modeling
decisions, algorithm implementation, result interpretation, and final report content were
produced, checked, and approved by the student. AI tools contributed to drafting speed
and formatting quality; they did not determine any engineering or implementation out-
come.
21