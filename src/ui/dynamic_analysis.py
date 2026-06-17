"""Dynamic-analysis execution helpers for the Streamlit UI."""

from __future__ import annotations

import math
from collections.abc import MutableMapping
from dataclasses import dataclass

from dof_optimizer import DOFOptimizer
from matrix_assembly import DynamicAssembler, MatrixAssembler
from modal_solver import ModalSolver, ModalSolverError
from parser import StructuralModel
from results import DynamicAssemblyData, ModalResults, RSAResults, THAResults
from rsa_solver import RSASolverError, ResponseSpectrumSolver


@dataclass
class DynamicAnalysisRun:
    """User-facing outcome for a dynamic analysis request."""

    results: ModalResults | RSAResults | THAResults | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.results is not None


def run_modal_analysis(
    model: StructuralModel | None,
    num_modes: int = 3,
    mass_matrix_type: str = "lumped",
    rayleigh_target_mode_i: int | None = None,
    rayleigh_zeta_i: float | None = None,
    rayleigh_target_mode_j: int | None = None,
    rayleigh_zeta_j: float | None = None,
) -> DynamicAnalysisRun:
    """Run the existing modal pipeline and return ModalResults."""
    if model is None:
        return DynamicAnalysisRun(None, "Build or load a model before running modal analysis.")
    if not _has_mass(model):
        return DynamicAnalysisRun(None, "Add mass before running modal analysis.")
    if num_modes <= 0:
        return DynamicAnalysisRun(None, "Request at least one mode before running modal analysis.")

    try:
        data = _assemble_dynamic_data(model, mass_matrix_type)
        if not data.active_dynamic_dofs:
            return DynamicAnalysisRun(None, "Add mass before running modal analysis.")
        r = _influence_vector(model, data.active_dynamic_dofs, getattr(model, "excitation_direction", "x"))
        results = ModalSolver(data.Kff, data.Mff).solve(r=r, num_modes=num_modes)
        _attach_modal_dynamic_context(results, data)
        requested_rayleigh = (rayleigh_target_mode_i, rayleigh_zeta_i, rayleigh_target_mode_j, rayleigh_zeta_j)
        if all(value is not None for value in requested_rayleigh):
            try:
                _apply_modal_rayleigh_damping(
                    results,
                    data,
                    target_mode_i=rayleigh_target_mode_i,
                    zeta_i=rayleigh_zeta_i,
                    target_mode_j=rayleigh_target_mode_j,
                    zeta_j=rayleigh_zeta_j,
                )
            except ValueError as exc:
                if not (
                    _is_default_modal_rayleigh_request(
                        target_mode_i=rayleigh_target_mode_i,
                        zeta_i=rayleigh_zeta_i,
                        target_mode_j=rayleigh_target_mode_j,
                        zeta_j=rayleigh_zeta_j,
                    )
                    and _can_skip_default_modal_rayleigh_damping(exc)
                ):
                    raise
        else:
            default_rayleigh = _default_modal_rayleigh_targets(results)
            if default_rayleigh is not None:
                _apply_modal_rayleigh_damping(results, data, **default_rayleigh)
        return DynamicAnalysisRun(results)
    except (ModalSolverError, ValueError) as exc:
        return DynamicAnalysisRun(None, f"Modal analysis failed: {exc}")


def run_response_spectrum_analysis(
    modal_results: ModalResults | None,
    spectrum_periods: list[float] | None,
    spectrum_accelerations: list[float] | None,
    combination_method: str = "SRSS",
    damping_ratio: float = 0.05,
) -> DynamicAnalysisRun:
    """Run the existing response-spectrum pipeline and return RSAResults."""
    if modal_results is None:
        return DynamicAnalysisRun(None, "Run modal analysis before response spectrum analysis.")
    if not spectrum_periods or not spectrum_accelerations:
        return DynamicAnalysisRun(None, "Provide a response spectrum before running RSA.")
    if len(spectrum_periods) != len(spectrum_accelerations):
        return DynamicAnalysisRun(None, "Response spectrum periods and accelerations must have the same length.")
    if not _valid_damping(damping_ratio):
        return DynamicAnalysisRun(None, "Enter a damping ratio between 0 and 1.")

    try:
        solver = ResponseSpectrumSolver(modal_results, spectrum_periods, spectrum_accelerations)
        return DynamicAnalysisRun(solver.solve(combination_method=combination_method, damping_ratio=damping_ratio))
    except (RSASolverError, ValueError) as exc:
        return DynamicAnalysisRun(None, f"Response spectrum analysis failed: {exc}")


def run_time_history_analysis(
    model: StructuralModel | None,
    ground_motion_config: GroundMotionConfig | None,
    damping_ratio: float = 0.05,
    mass_matrix_type: str = "lumped",
) -> DynamicAnalysisRun:
    """Run the existing Newmark ground-motion pipeline and return THAResults."""
    if model is None:
        return DynamicAnalysisRun(None, "Build or load a model before running time history analysis.")
    if not _has_mass(model):
        return DynamicAnalysisRun(None, "Add mass before running time history analysis.")
    if ground_motion_config is None:
        return DynamicAnalysisRun(None, "Provide a ground motion before running time history analysis.")
    if not _valid_damping(damping_ratio):
        return DynamicAnalysisRun(None, "Enter a damping ratio between 0 and 1.")

    from ground_motion import read_ground_motion
    from newmark_solver import NewmarkSolverError, NewmarkTimeHistorySolver

    try:
        data = _assemble_dynamic_data(model, mass_matrix_type)
        if not data.active_dynamic_dofs:
            return DynamicAnalysisRun(None, "Add mass before running time history analysis.")
        r = _influence_vector(model, data.active_dynamic_dofs, ground_motion_config.excitation_direction)
        record = read_ground_motion(ground_motion_config)
        solver = NewmarkTimeHistorySolver(data.Kff, data.Mff, data.Cff)
        return DynamicAnalysisRun(solver.solve_ground_motion(record, r, damping_ratio=damping_ratio))
    except (NewmarkSolverError, ValueError, OSError) as exc:
        return DynamicAnalysisRun(None, f"Time history analysis failed: {exc}")


def run_modal_analysis_into_state(
    session_state: MutableMapping[str, object],
    num_modes: int = 3,
    mass_matrix_type: str = "lumped",
) -> DynamicAnalysisRun:
    """Execute modal analysis for the active UI model and cache the result."""
    result = run_modal_analysis(session_state.get("model"), num_modes, mass_matrix_type)
    _store_result(session_state, "modal_results", "modal_analysis_error", result)
    return result


def run_response_spectrum_analysis_into_state(
    session_state: MutableMapping[str, object],
    spectrum_periods: list[float] | None,
    spectrum_accelerations: list[float] | None,
    combination_method: str = "SRSS",
    damping_ratio: float = 0.05,
) -> DynamicAnalysisRun:
    """Execute RSA for cached modal results and cache the result."""
    result = run_response_spectrum_analysis(
        session_state.get("modal_results"),
        spectrum_periods,
        spectrum_accelerations,
        combination_method,
        damping_ratio,
    )
    _store_result(session_state, "rsa_results", "rsa_analysis_error", result)
    return result


def run_time_history_analysis_into_state(
    session_state: MutableMapping[str, object],
    ground_motion_config: GroundMotionConfig | None,
    damping_ratio: float = 0.05,
    mass_matrix_type: str = "lumped",
) -> DynamicAnalysisRun:
    """Execute THA for the active UI model and cache the result."""
    result = run_time_history_analysis(
        session_state.get("model"),
        ground_motion_config,
        damping_ratio,
        mass_matrix_type,
    )
    _store_result(session_state, "tha_results", "tha_analysis_error", result)
    return result


def _assemble_dynamic_data(model: StructuralModel, mass_matrix_type: str) -> DynamicAssemblyData:
    optimizer = DOFOptimizer(model)
    num_eq, semi_bw, _ = optimizer.optimize()
    static_assembler = MatrixAssembler(model, num_eq, semi_bw)
    K_full = static_assembler.assemble_full_stiffness_matrix()
    return DynamicAssembler(model, num_eq).assemble_dynamic_data(K_full, matrix_type=mass_matrix_type)


def _has_mass(model: StructuralModel) -> bool:
    if getattr(model, "lumped_masses", None):
        return True
    return any(abs(getattr(element.material, "density", 0.0)) > 1.0e-12 for element in model.elements.values())


def _influence_vector(model: StructuralModel, active_dynamic_dofs: list[int], direction: str) -> list[float]:
    local_index = 1 if direction == "y" else 0
    active_set = set(active_dynamic_dofs)
    vector = []
    for dof in active_dynamic_dofs:
        value = 0.0
        for node in model.nodes.values():
            if node.dofs[local_index] == dof and dof in active_set:
                value = 1.0
                break
        vector.append(value)
    return vector


def _valid_damping(damping_ratio: float) -> bool:
    return 0.0 <= damping_ratio < 1.0


def _default_modal_rayleigh_targets(results: ModalResults | object) -> dict[str, float | int] | None:
    if len(_modal_omegas(results)) < 2:
        return None
    return {
        "target_mode_i": 1,
        "zeta_i": 0.05,
        "target_mode_j": 2,
        "zeta_j": 0.05,
    }


def _attach_modal_dynamic_context(results: ModalResults, data: DynamicAssemblyData) -> None:
    """Expose the reduced dynamic matrices used by the modal solver on the cached result."""
    results.dynamic_assembly = data
    results.Kff = [row[:] for row in data.Kff]
    results.Mff = [row[:] for row in data.Mff]
    results.Cff = None
    results.omegas = _modal_omegas(results)
    results.rayleigh_alpha = None
    results.rayleigh_beta = None
    results.rayleigh_target_mode_i = None
    results.rayleigh_target_mode_j = None
    results.rayleigh_zeta_i = None
    results.rayleigh_zeta_j = None
    results.rayleigh_target_modes = None
    results.rayleigh_target_damping_ratios = None
    results.modal_damping_ratios = None


def _apply_modal_rayleigh_damping(
    results: ModalResults,
    data: DynamicAssemblyData,
    *,
    target_mode_i: int,
    zeta_i: float,
    target_mode_j: int,
    zeta_j: float,
) -> None:
    _validate_modal_rayleigh_request(
        target_mode_i=target_mode_i,
        zeta_i=zeta_i,
        target_mode_j=target_mode_j,
        zeta_j=zeta_j,
    )
    _record_modal_rayleigh_request(
        results,
        target_mode_i=target_mode_i,
        zeta_i=zeta_i,
        target_mode_j=target_mode_j,
        zeta_j=zeta_j,
    )
    rayleigh = _build_rayleigh_damping_data(
        results,
        data.Kff,
        data.Mff,
        target_mode_i=target_mode_i,
        zeta_i=zeta_i,
        target_mode_j=target_mode_j,
        zeta_j=zeta_j,
    )

    data.Cff = [row[:] for row in rayleigh["Cff"]]
    data.rayleigh_alpha = rayleigh["alpha"]
    data.rayleigh_beta = rayleigh["beta"]

    results.Cff = [row[:] for row in rayleigh["Cff"]]
    results.rayleigh_alpha = rayleigh["alpha"]
    results.rayleigh_beta = rayleigh["beta"]
    results.modal_damping_ratios = rayleigh["modal_damping_ratios"]


def _build_rayleigh_damping_data(
    results: ModalResults | object,
    Kff: list[list[float]],
    Mff: list[list[float]],
    *,
    target_mode_i: int,
    zeta_i: float,
    target_mode_j: int,
    zeta_j: float,
) -> dict[str, object]:
    _validate_modal_rayleigh_request(
        target_mode_i=target_mode_i,
        zeta_i=zeta_i,
        target_mode_j=target_mode_j,
        zeta_j=zeta_j,
    )

    omegas = _modal_omegas(results)
    mode_count = len(omegas)
    if target_mode_i > mode_count or target_mode_j > mode_count:
        raise ValueError("Selected Rayleigh target modes must exist in the extracted modal results.")

    omega_i = omegas[target_mode_i - 1]
    omega_j = omegas[target_mode_j - 1]
    if omega_i <= 0.0 or omega_j <= 0.0:
        raise ValueError("Selected Rayleigh target modes must have positive frequencies.")

    denominator = (omega_j * omega_j) - (omega_i * omega_i)
    if abs(denominator) <= 1.0e-12:
        raise ValueError("Selected Rayleigh target modes must have distinct positive frequencies.")

    beta = 2.0 * ((zeta_j * omega_j) - (zeta_i * omega_i)) / denominator
    alpha = (2.0 * zeta_i * omega_i) - (beta * omega_i * omega_i)
    Cff = [
        [
            (alpha * Mff[row_index][column_index]) + (beta * Kff[row_index][column_index])
            for column_index in range(len(Kff[row_index]))
        ]
        for row_index in range(len(Kff))
    ]
    modal_damping_ratios = [
        ((alpha / (2.0 * omega)) + ((beta * omega) / 2.0)) if omega > 0.0 else None
        for omega in omegas
    ]
    return {
        "alpha": alpha,
        "beta": beta,
        "Cff": Cff,
        "modal_damping_ratios": modal_damping_ratios,
    }


def _validate_modal_rayleigh_request(
    *,
    target_mode_i: int,
    zeta_i: float,
    target_mode_j: int,
    zeta_j: float,
) -> None:
    if target_mode_i < 1 or target_mode_j < 1:
        raise ValueError("Rayleigh target modes must be at least 1.")
    if target_mode_i == target_mode_j:
        raise ValueError("Rayleigh target modes must be distinct.")
    if zeta_i < 0.0 or zeta_j < 0.0:
        raise ValueError("Rayleigh damping ratios must be nonnegative.")


def _record_modal_rayleigh_request(
    results: ModalResults | object,
    *,
    target_mode_i: int,
    zeta_i: float,
    target_mode_j: int,
    zeta_j: float,
) -> None:
    results.rayleigh_target_mode_i = target_mode_i
    results.rayleigh_target_mode_j = target_mode_j
    results.rayleigh_zeta_i = zeta_i
    results.rayleigh_zeta_j = zeta_j
    results.rayleigh_target_modes = (target_mode_i, target_mode_j)
    results.rayleigh_target_damping_ratios = (zeta_i, zeta_j)


def _is_default_modal_rayleigh_request(
    *,
    target_mode_i: int,
    zeta_i: float,
    target_mode_j: int,
    zeta_j: float,
) -> bool:
    return (
        target_mode_i == 1
        and target_mode_j == 2
        and math.isclose(zeta_i, 0.05, rel_tol=0.0, abs_tol=1.0e-12)
        and math.isclose(zeta_j, 0.05, rel_tol=0.0, abs_tol=1.0e-12)
    )


def _can_skip_default_modal_rayleigh_damping(error: ValueError) -> bool:
    message = str(error)
    return (
        "must exist in the extracted modal results" in message
        or "must have positive frequencies" in message
        or "must have distinct positive frequencies" in message
    )


def _modal_omegas(results: ModalResults | object) -> list[float]:
    eigenvalues = getattr(results, "eigenvalues", None) or []
    if eigenvalues:
        omegas = []
        for eigenvalue in eigenvalues:
            try:
                value = float(eigenvalue)
            except (TypeError, ValueError) as exc:
                raise ValueError("Modal eigenvalues must be numeric to compute Rayleigh damping.") from exc
            if value <= 0.0:
                raise ValueError("Modal frequencies must be positive to compute Rayleigh damping.")
            omegas.append(math.sqrt(value))
        return omegas

    frequencies = getattr(results, "frequencies", None) or []
    omegas = []
    for frequency in frequencies:
        try:
            value = float(frequency)
        except (TypeError, ValueError) as exc:
            raise ValueError("Modal frequencies must be numeric to compute Rayleigh damping.") from exc
        if value <= 0.0:
            raise ValueError("Modal frequencies must be positive to compute Rayleigh damping.")
        omegas.append(2.0 * math.pi * value)
    return omegas


def _store_result(
    session_state: MutableMapping[str, object],
    result_key: str,
    error_key: str,
    result: DynamicAnalysisRun,
) -> None:
    if result.ok:
        session_state[result_key] = result.results
        session_state[error_key] = None
        session_state["model_is_dirty"] = False
    else:
        session_state[result_key] = None
        session_state[error_key] = result.error
