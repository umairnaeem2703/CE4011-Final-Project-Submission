"""Dynamic-analysis execution helpers for the Streamlit UI."""

from __future__ import annotations

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
