# MATH_SPEC.md

## Scope

This document is the final mathematical contract for the submitted Static + Modal desktop MVP. All structure types are reduced to common DOF maps, matrices, vectors, and result objects before solving.

RSA and THA are deferred future extensions and are not part of the submitted desktop analysis scope.

## Degrees Of Freedom

Each 2D node uses:

```text
[ux, uy, rz]
```

Each 2D frame element uses:

```text
[ux_i, uy_i, rz_i, ux_j, uy_j, rz_j]
```

The DOF layer provides the global DOF map, free DOFs, restrained DOFs, and active dynamic DOFs for modal analysis.

## Coordinate Transformation

For an element of length `L` with direction cosines `c = cos(theta)` and `s = sin(theta)`:

```text
q_local = T q_global
k_global = T^T k_local T
m_global = T^T m_local T
```

Element local axes run from node `i` to node `j`.

## Element Stiffness

### Truss Or Bar

```text
k = EA/L * [[1, -1],
            [-1, 1]]
```

### 2D Euler-Bernoulli Frame

Local 6 by 6 stiffness:

```text
[ EA/L       0          0       -EA/L       0          0      ]
[ 0     12EI/L^3   6EI/L^2      0    -12EI/L^3   6EI/L^2 ]
[ 0      6EI/L^2   4EI/L        0     -6EI/L^2   2EI/L   ]
[-EA/L       0          0        EA/L       0          0      ]
[ 0    -12EI/L^3  -6EI/L^2      0     12EI/L^3  -6EI/L^2 ]
[ 0      6EI/L^2   2EI/L        0     -6EI/L^2   4EI/L   ]
```

Member releases and hinged-node effects are handled through the existing element/release condensation behavior before assembly.

## Global Assembly

For each element:

```text
compute k_local
transform to k_global
scatter into K using global DOF indices
assemble equivalent nodal loads into F where applicable
```

For modal analysis, mass terms are also assembled:

```text
compute or collect element/nodal mass
transform m_local to m_global where needed
scatter into M using global DOF indices
```

The implementation preserves full and reduced matrices/vectors for educational output.

## Boundary Reduction

Partition the static system into free and restrained DOFs:

```text
[Kff Kfr] [uf] = [Ff]
[Krf Krr] [ur]   [Fr]
```

With prescribed support displacement `ur`:

```text
Kff uf = Ff - Kfr ur
```

When `ur = 0`, this reduces to:

```text
Kff uf = Ff
```

## Static Analysis

### Solve

```text
K u = F
Kff uf = Ff
```

Use a direct linear solve for `Kff uf = Ff`; do not compute an explicit global inverse for ordinary solving.

### Reactions

After recovering the full displacement vector:

```text
R = K u - F
```

Support reactions are extracted at restrained DOFs and mapped back to nodal `[Fx, Fy, Mz]`.

### Member Force Recovery

For each element:

```text
u_local = T u_global
f_local = k_local u_local + fef_local
```

`fef_local` accounts for fixed-end effects from member loads, thermal loading, settlements, and equivalent nodal actions supported by the model.

### Static Outputs

- DOF map
- `K`, `Kff`
- `F`, `Ff`
- nodal displacements
- support reactions
- member-end forces
- axial force `N`, shear force `V`, and bending moment `M` diagram data

## Mass Assembly

Modal analysis requires a compatible mass matrix. Lumped mass is the final-scope default for educational workflows.

For a member with density `rho`, area `A`, and length `L`:

```text
m_total = rho A L
m_node = m_total / 2
```

The translational nodal masses are added to the appropriate translational DOFs. Rotational inertia is ignored unless explicitly modeled by input data.

Nodal lumped masses are assembled directly into the corresponding active translational DOFs.

## Massless DOF Handling

Before modal analysis:

- disconnected zero-mass DOFs may be removed
- stiffness-coupled massless DOFs must be statically condensed

For active massive DOFs `a` and massless stiffness-coupled DOFs `m`:

```text
K_eff = Kaa - Kam Kmm^-1 Kma
M_eff = Maa
```

The modal eigenproblem uses the retained effective system.

## Modal Analysis

### Generalized Eigenproblem

```text
K phi = lambda M phi
```

where:

```text
lambda = omega^2
omega = sqrt(lambda)
```

### Frequencies And Periods

```text
f = omega / (2 pi)
T = 1 / f
```

### Mode Shape Normalization

Mass normalization:

```text
phi_n = phi_n / sqrt(phi_n^T M phi_n)
```

After normalization:

```text
phi_n^T M phi_n = 1
```

The UI may also display magnitude-normalized or reference-DOF-normalized mode shapes for readability, but stored modal properties should remain mathematically traceable.

### Participation And Effective Mass

For influence vector `r`, commonly horizontal translation:

```text
Gamma_n = (phi_n^T M r) / (phi_n^T M phi_n)
```

For mass-normalized modes:

```text
Gamma_n = phi_n^T M r
```

Effective modal mass:

```text
M_eff,n = Gamma_n^2 (phi_n^T M phi_n)
```

For mass-normalized modes:

```text
M_eff,n = Gamma_n^2
```

Total participating mass:

```text
M_total = r^T M r
```

Mass participation ratio:

```text
ratio_n = M_eff,n / M_total
```

Cumulative participation is the running sum of `ratio_n`.

### Modal Outputs

- full and reduced/condensed stiffness and mass matrices where available
- eigenvalues `lambda`
- circular frequencies `omega`
- frequencies `f`
- periods `T`
- mode shapes
- modal masses
- participation factors
- effective modal masses
- mass participation ratios
- active dynamic DOF information

## Numerical Rules

- Prefer solving linear systems over computing explicit matrix inverses.
- Keep core numerical routines transparent and standard-library oriented unless a dependency is approved.
- Preserve intermediate matrices/vectors for reports, tests, and classroom inspection.
- Detect singular or ill-conditioned systems and report clear analysis failures.

## Sign Conventions

- Global `x`: positive right.
- Global `y`: positive up.
- Global `rz`: positive counterclockwise.
- Element local axis: positive from node `i` to node `j`.
- Axial force `N`: positive in tension.
- Shear force `V`: positive according to the project/SAP2000-compatible member-end convention.
- Bending moment `M`: positive according to the project/SAP2000-compatible plotting and member-end convention.
- Downward applied load is negative global `y`.

## Deferred/Future Extensions

RSA and THA should remain future extensions unless explicitly approved for a later scope. Future work should reuse the same architecture:

```text
model -> assembly -> generalized solver -> result object -> visualization/export
```

Future RSA would build on modal properties and spectrum interpolation/combination. Future THA would build on dynamic matrices, damping, ground-motion input, and time-integration results. Neither workflow is part of the final submitted desktop UI scope.
