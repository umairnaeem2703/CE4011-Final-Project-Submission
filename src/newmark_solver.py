from results import THAResults


class NewmarkSolverError(Exception):
    """Custom exception raised for time-history analysis errors."""


def build_earthquake_force_history(M: list, r: list, acceleration_history: list) -> list:
    """Return P(t) = -M r ag(t) for each acceleration sample."""
    _validate_square_matrix(M, "M")
    if len(r) != len(M):
        raise NewmarkSolverError("Influence vector length must match mass matrix size.")

    mass_influence = _mat_vec_mul(M, r)
    return [[-mass_influence[i] * ag for i in range(len(r))] for ag in acceleration_history]


class NewmarkTimeHistorySolver:
    """Generalized Newmark average-acceleration solver for M u_ddot + C u_dot + K u = P(t)."""

    def __init__(
        self,
        K: list,
        M: list,
        C: list | None = None,
        gamma: float = 0.5,
        beta: float = 0.25,
    ):
        _validate_square_matrix(K, "K")
        _validate_square_matrix(M, "M")
        if len(K) != len(M):
            raise NewmarkSolverError("K and M must have the same size.")
        self.K = [row[:] for row in K]
        self.M = [row[:] for row in M]
        self.C = [row[:] for row in C] if C is not None else _zeros(len(K), len(K))
        _validate_square_matrix(self.C, "C")
        if len(self.C) != len(K):
            raise NewmarkSolverError("C and K must have the same size.")
        self.gamma = gamma
        self.beta = beta

    def solve_ground_motion(
        self,
        ground_motion_record,
        r: list,
        damping_ratio: float = 0.0,
        initial_displacement: list | None = None,
        initial_velocity: list | None = None,
    ) -> THAResults:
        force_history = build_earthquake_force_history(
            self.M,
            r,
            ground_motion_record.acceleration_si,
        )
        return self.solve_force_history(
            time_vector=ground_motion_record.time_vector,
            force_history=force_history,
            excitation_history=ground_motion_record.acceleration_si,
            damping_ratio=damping_ratio,
            source_file=ground_motion_record.source_file,
            acceleration_unit=ground_motion_record.acceleration_unit,
            scale_factor=ground_motion_record.scale_factor,
            input_format=ground_motion_record.input_format,
            initial_displacement=initial_displacement,
            initial_velocity=initial_velocity,
        )

    def solve_force_history(
        self,
        time_vector: list,
        force_history: list,
        excitation_history: list | None = None,
        damping_ratio: float = 0.0,
        source_file: str = "",
        acceleration_unit: str = "m/s2",
        scale_factor: float = 1.0,
        input_format: str = "time_acceleration",
        initial_displacement: list | None = None,
        initial_velocity: list | None = None,
    ) -> THAResults:
        n = len(self.K)
        if len(time_vector) != len(force_history):
            raise NewmarkSolverError("time_vector and force_history must have the same length.")
        if not time_vector:
            raise NewmarkSolverError("time_vector must contain at least one step.")
        for force in force_history:
            if len(force) != n:
                raise NewmarkSolverError("Each force vector must match matrix size.")

        dt = time_vector[1] - time_vector[0] if len(time_vector) > 1 else 0.0
        if len(time_vector) > 1 and dt <= 0.0:
            raise NewmarkSolverError("Time step must be positive.")
        if len(time_vector) > 1:
            _validate_uniform_dt(time_vector, dt)

        u0 = initial_displacement[:] if initial_displacement is not None else [0.0] * n
        v0 = initial_velocity[:] if initial_velocity is not None else [0.0] * n
        residual0 = _vec_subtract(
            _vec_subtract(force_history[0], _mat_vec_mul(self.C, v0)),
            _mat_vec_mul(self.K, u0),
        )
        a0_vec = _solve_linear_system(self.M, residual0)

        displacement_history = [u0]
        velocity_history = [v0]
        acceleration_history = [a0_vec]

        if len(time_vector) > 1:
            self._step_histories(
                dt,
                force_history,
                displacement_history,
                velocity_history,
                acceleration_history,
            )

        peak_displacement = _peak_by_dof(displacement_history)
        peak_velocity = _peak_by_dof(velocity_history)
        peak_acceleration = _peak_by_dof(acceleration_history)
        base_shear_history = []
        overturning_moment_history = []

        return THAResults(
            time_vector=time_vector[:],
            excitation_history=excitation_history[:] if excitation_history is not None else [],
            applied_force_history=[row[:] for row in force_history],
            displacement_history=displacement_history,
            velocity_history=velocity_history,
            acceleration_history=acceleration_history,
            base_shear_history=base_shear_history,
            overturning_moment_history=overturning_moment_history,
            peak_displacement=peak_displacement,
            peak_velocity=peak_velocity,
            peak_acceleration=peak_acceleration,
            peak_base_shear=0.0,
            peak_overturning_moment=0.0,
            step_table=_build_step_table(
                time_vector,
                displacement_history,
                velocity_history,
                acceleration_history,
                base_shear_history,
                overturning_moment_history,
            ),
            damping_ratio=damping_ratio,
            dt=dt,
            num_steps=len(time_vector),
            source_file=source_file,
            acceleration_unit=acceleration_unit,
            scale_factor=scale_factor,
            input_format=input_format,
        )

    def _step_histories(
        self,
        dt: float,
        force_history: list,
        displacement_history: list,
        velocity_history: list,
        acceleration_history: list,
    ) -> None:
        n = len(self.K)
        gamma = self.gamma
        beta = self.beta
        a0 = 1.0 / (beta * dt * dt)
        a1 = gamma / (beta * dt)
        a2 = 1.0 / (beta * dt)
        a3 = (1.0 / (2.0 * beta)) - 1.0
        a4 = (gamma / beta) - 1.0
        a5 = dt * ((gamma / (2.0 * beta)) - 1.0)

        Keff = _matrix_add(self.K, _matrix_add(_matrix_scale(self.M, a0), _matrix_scale(self.C, a1)))

        for step in range(1, len(force_history)):
            u_prev = displacement_history[-1]
            v_prev = velocity_history[-1]
            accel_prev = acceleration_history[-1]

            mass_term = [
                a0 * u_prev[i] + a2 * v_prev[i] + a3 * accel_prev[i]
                for i in range(n)
            ]
            damping_term = [
                a1 * u_prev[i] + a4 * v_prev[i] + a5 * accel_prev[i]
                for i in range(n)
            ]
            effective_force = _vec_add(
                force_history[step],
                _vec_add(_mat_vec_mul(self.M, mass_term), _mat_vec_mul(self.C, damping_term)),
            )
            u_next = _solve_linear_system(Keff, effective_force)
            accel_next = [
                a0 * (u_next[i] - u_prev[i]) - a2 * v_prev[i] - a3 * accel_prev[i]
                for i in range(n)
            ]
            v_next = [
                v_prev[i] + (1.0 - gamma) * dt * accel_prev[i] + gamma * dt * accel_next[i]
                for i in range(n)
            ]

            displacement_history.append(u_next)
            velocity_history.append(v_next)
            acceleration_history.append(accel_next)


def _validate_square_matrix(matrix: list, name: str) -> None:
    if not matrix or any(len(row) != len(matrix) for row in matrix):
        raise NewmarkSolverError(f"{name} must be a non-empty square matrix.")


def _validate_uniform_dt(time_vector: list, dt: float) -> None:
    for i in range(1, len(time_vector)):
        if abs((time_vector[i] - time_vector[i - 1]) - dt) > 1.0e-9:
            raise NewmarkSolverError("Newmark solver requires a uniform time step.")


def _zeros(rows: int, cols: int) -> list:
    return [[0.0 for _ in range(cols)] for _ in range(rows)]


def _matrix_add(A: list, B: list) -> list:
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def _matrix_scale(A: list, scale: float) -> list:
    return [[scale * value for value in row] for row in A]


def _mat_vec_mul(A: list, v: list) -> list:
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]


def _vec_add(a: list, b: list) -> list:
    return [a[i] + b[i] for i in range(len(a))]


def _vec_subtract(a: list, b: list) -> list:
    return [a[i] - b[i] for i in range(len(a))]


def _peak_by_dof(history: list) -> dict:
    if not history:
        return {}
    return {
        dof: max(abs(row[dof]) for row in history)
        for dof in range(len(history[0]))
    }


def _build_step_table(
    time_vector: list,
    displacement_history: list,
    velocity_history: list,
    acceleration_history: list,
    base_shear_history: list,
    overturning_moment_history: list,
) -> list:
    table = []
    for i, time_value in enumerate(time_vector):
        base_shear = base_shear_history[i] if i < len(base_shear_history) else 0.0
        otm = overturning_moment_history[i] if i < len(overturning_moment_history) else 0.0
        table.append(
            (
                time_value,
                displacement_history[i],
                velocity_history[i],
                acceleration_history[i],
                base_shear,
                otm,
            )
        )
    return table


def _solve_linear_system(A: list, b: list) -> list:
    n = len(b)
    aug = [A[i][:] + [b[i]] for i in range(n)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
        if abs(aug[pivot][col]) < 1.0e-14:
            raise NewmarkSolverError("Cannot solve singular dynamic system.")
        aug[col], aug[pivot] = aug[pivot], aug[col]
        for row in range(col + 1, n):
            factor = aug[row][col] / aug[col][col]
            for k in range(col, n + 1):
                aug[row][k] -= factor * aug[col][k]

    x = [0.0] * n
    for row in range(n - 1, -1, -1):
        rhs = aug[row][n] - sum(aug[row][col] * x[col] for col in range(row + 1, n))
        x[row] = rhs / aug[row][row]
    return x
