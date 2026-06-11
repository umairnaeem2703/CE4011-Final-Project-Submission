# MATH_SPEC.md

## Scope
Mathematical contract for static, modal, RSA, and THA solvers. Keep solvers generalized: every model becomes matrices/vectors before analysis.

---

## DOFs
2D frame node DOFs:
```text
[ux, uy, rz]
```
Two-node frame element DOFs:
```text
[ux_i, uy_i, rz_i, ux_j, uy_j, rz_j]
```
`DOFManager` returns `global_dof_map`, `free_dofs`, `restrained_dofs`, `active_dynamic_dofs`.

---

## Transformation
For element length `L`, direction cosines `c = cos(θ)`, `s = sin(θ)`:
```text
q_local = T q_global
k_global = T^T k_local T
m_global = T^T m_local T
```

---

## Stiffness (Phase 2)

### Truss/Bar
```text
k = EA/L * [[1,-1],[-1,1]]
```

### Frame2D (Euler-Bernoulli)
Local 6×6 stiffness:
```text
[k_axial       0          0       -k_axial      0          0      ]
[0        12EI/L^3   6EI/L^2      0      -12EI/L^3  6EI/L^2   ]
[0        6EI/L^2    4EI/L       0      -6EI/L^2   2EI/L    ]
[-k_axial     0          0       k_axial       0          0      ]
[0       -12EI/L^3  -6EI/L^2      0       12EI/L^3  -6EI/L^2  ]
[0        6EI/L^2    2EI/L       0      -6EI/L^2   4EI/L    ]
```
where `k_axial = EA/L`.

---

## Assembly (Phase 2–3)

For each element, compute local stiffness and mass, transform to global, then scatter into global matrix:
```text
For each element's global DOF index pairs (Ia, Ib):
  K[Ia,Ib] += k_element_global[a,b]
  M[Ia,Ib] += m_element_global[a,b]  (Phase 3)
```

### Boundary Reduction
For fixed (restrained) DOFs, partition and solve reduced free system:
```text
[Kff  Kfr ] [uf ]   [Ff]
[Krf  Krr ] [ur ] = [Fr]

Kff uf = Ff - Kfr ur_prescribed
```

Preserve both full and reduced matrices in results for educational transparency.

---

## Static (Phase 2)

### Solve
```text
K u = F
u = K^{-1} F  (or solve Kx=b via direct elimination)
```

### Recovery
Support reactions:
```text
R = K u - F  (residual force)
```
(Or equivalently: extract forces at restrained DOFs)

Element local forces:
```text
u_local = T u_global
f_local = k_local u_local + fef_local
```
where `fef_local` accounts for distributed loads, thermal effects, settlements.

### Outputs
- Nodal displacements u
- Support reactions R
- Element forces: [N_i, V_i, M_i, N_j, V_j, M_j] per element
- Diagrams: N/V/M along each element

---

## Mass Assembly (Phase 3)

### Lumped Mass
Place 1/2 of element mass at each node:
```text
For frame: m_node = (rho * A * L) / 2
M[dof_i, dof_i] += m_node
M[dof_j, dof_j] += m_node
```
Rotational inertia: typically ignored (set to 0) unless explicitly modeled.

### Consistent Mass (Optional)
Standard Euler-Bernoulli consistent mass matrix for frame elements (use if specified by problem).

---

## Damping (Phase 3–4)

### Rayleigh Damping
```text
C = alpha * M + beta * K
```

Given two target damping ratios `zeta_i` and `zeta_j` at frequencies `omega_i` and `omega_j`:
```text
alpha = 2 * zeta * omega_i * omega_j / (omega_i + omega_j)
beta  = 2 * zeta / (omega_i + omega_j)
```
where `zeta = (zeta_i + zeta_j) / 2` or problem-specified value.

### Modal Damping (Simplified, Phase 5+)
For each mode n:
```text
C_n = 2 * zeta_n * omega_n * M_n
```
Used in modal superposition for THA/RSA.

---

## Modal Analysis (Phase 4)

### Generalized Eigenvalue Problem
```text
K phi = lambda M phi
```
where `lambda = omega^2`.

### Solution Strategy (Pure Python)
1. Cholesky decomposition: `M = L L^T`
2. Transform: `A = L^{-1} K L^{-T}`
3. Jacobi eigen solver: `A y = lambda y`
4. Back-transform: `phi = L^{-T} y`

### Normalization (Mass Orthonormalization)
```text
phi_n := phi_n / sqrt(phi_n^T M phi_n)
```
Result: `phi_n^T M phi_n = 1.0` for all modes.

### Frequencies and Periods
```text
omega_n = sqrt(lambda_n)  [rad/s]
f_n = omega_n / (2*pi)     [Hz]
T_n = 1 / f_n              [seconds]
```

### Participation Factors and Effective Mass
For influence vector `r` (e.g., `r = [1, 0, 0, 1, 0, 0, ...]` for horizontal excitation):
```text
Gamma_n = phi_n^T M r  (since phi^T M phi = 1)
M_eff,n = Gamma_n^2
mass_ratio_n = M_eff,n / (r^T M r)  [fraction of total participating mass]
```

### Outputs
- Eigenvalues (lambda, omega^2)
- Frequencies (Hz)
- Periods (seconds)
- Mode shapes (mass-normalized)
- Modal masses (≈ 1.0)
- Participation factors
- Effective masses
- Mass participation ratios (%)

---

## Damped Modal Superposition (Phase 5–6)

For each mode n with modal properties:
```text
omega_n, zeta_n, Gamma_n, phi_n
```

In modal coordinates `q_n(t)`:
```text
q_n_ddot + 2*zeta_n*omega_n * q_n_dot + omega_n^2 * q_n = Gamma_n * ag(t)
```
where `ag(t)` is the ground acceleration.

Solve using Newmark step-by-step (Phase 5) or spectral acceleration (Phase 6).

Transform back to physical coordinates:
```text
u(t) = sum_n phi_n * q_n(t)
```

---

## Response Spectrum Analysis (Phase 6)

### Spectrum Lookup
For each mode n:
- Period: `T_n`
- Damping ratio: `zeta_n`
- Lookup `Sa(T_n, zeta_n)` from design spectrum

### Modal Response
```text
q_n,max = Gamma_n * Sa(T_n, zeta_n) / omega_n^2
u_n,max = phi_n * q_n,max  [peak displacement due to mode n]
F_n,max = K * u_n,max       [peak forces due to mode n]
```

### Combination: SRSS
```text
R_total = sqrt(sum_n (R_n,max)^2)
```
for any response quantity R (displacement, force, etc.).

### Combination: CQC (Complete Quadratic Combination)
```text
R_total = sqrt(sum_i sum_j rho_ij * R_i,max * R_j,max)
```

#### CQC Coupling Coefficient (Chopra formula)
```text
rho_ij = (8 * zeta^2 * sqrt(1-zeta^2) * (r_ij + 4*zeta^2*r_ij^3)) / 
         ((1 - r_ij^2)^2 + 4*zeta^2*r_ij^2*(1 + r_ij^2))

where r_ij = omega_i / omega_j  (typically omega_i <= omega_j)
and zeta is average damping ratio (e.g., (zeta_i + zeta_j)/2 or global zeta)
```

**Note:** Implementation detail — if `omega_i == omega_j`, set `rho_ij = 1.0`.

### Outputs
- Interpolated spectrum values Sa(T_n, zeta_n)
- Modal response vectors (before combination)
- Modal base shears / OTMs (if applicable)
- Combined response via SRSS or CQC
- Peak displacement, base shear, OTM

---

## Time-History Analysis (Phase 5)

### Newmark Average Acceleration Method

Default constants:
```text
gamma = 1/2  (average acceleration assumed)
beta = 1/4
```

#### Effective Stiffness and Load at Each Step
```text
Keff = K + a0*M + a1*C
where a0 = 1/(beta*dt^2)
      a1 = gamma/(beta*dt)

Peff(t+dt) = P(t+dt) + M*(a0*u(t) + a2*u_dot(t) + a3*u_ddot(t))
                      + C*(a1*u(t) + a4*u_dot(t) + a5*u_ddot(t))

where a2, a3, a4, a5 are standard Newmark constants
```

#### Solve
```text
Keff u(t+dt) = Peff(t+dt)
```

#### Update (after solving for u(t+dt))
```text
u_ddot(t+dt) = a0*(u(t+dt) - u(t)) - a2*u_dot(t) - a3*u_ddot(t)
u_dot(t+dt)  = u_dot(t) + (1-gamma)*dt*u_ddot(t) + gamma*dt*u_ddot(t+dt)
```

### Earthquake Excitation
For horizontal ground motion `ag(t)`:
```text
r = [1, 0, 0, 1, 0, 0, ...]  (1 at every active ux DOF)
P(t) = -M * r * ag(t)
```

### Outputs
- Time vector
- Excitation history ag(t)
- Displacement, velocity, acceleration histories u(t), u_dot(t), u_ddot(t)
- Base shear V_base(t) = sum of shear reactions
- Overturning moment OTM(t) = sum of moment reactions
- Peak response quantities (max absolute values)
- Optional: step table sampling key time steps

---

## Numerical Rules
- **Prefer solving Kx=b** over explicit K^{-1}. Use Gaussian elimination or similar.
- **No explicit matrix inverse** unless dimension is <10 (e.g., element-level condensation).
- **Core math: pure Python** unless otherwise approved.
- **Required utilities:**
  - Matrix multiply, transpose, add, subtract
  - Vector norms (L2, max)
  - Linear solver (triangular substitution, Gaussian elimination)
  - Cholesky decomposition (for modal)
  - Jacobi eigenvalue solver (for generalized eigen)
  - 1D interpolation (for spectrum lookup)
  - `abs()`, `sqrt()`, `sin()`, `cos()` (standard library)

---

## Sign Conventions

**Global coordinates:** x horizontal (right +), y vertical (up +), rz rotation (CCW +).

**Element local:** runs from node_i to node_j.

**Frame DOFs:** `[ux_i, uy_i, rz_i, ux_j, uy_j, rz_j]`.

**Axial force N:** positive tension.

**Shear force V:** positive up-on-left (SAP2000 convention).

**Bending moment M:** positive sagging (concave up, tension in bottom fiber).

**Applied load w:** negative = downward.

**FEF (Fixed-End Force):** components positive in local element directions.
