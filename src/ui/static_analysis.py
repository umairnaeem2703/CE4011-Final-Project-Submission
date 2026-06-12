"""Static-analysis execution helpers for the Streamlit UI."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass

from banded_solver import BandedSolver, UnstableStructureError
from dof_optimizer import DOFOptimizer
from matrix_assembly import MatrixAssembler
from parser import StructuralModel
from post_processor import PostProcessor
from results import StaticResults


@dataclass
class StaticAnalysisRun:
    """User-facing outcome for a static analysis request."""

    results: StaticResults | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.results is not None


def run_static_analysis(model: StructuralModel | None, load_case_id: str | None = None) -> StaticAnalysisRun:
    """Run the existing static solver pipeline and return StaticResults."""
    if model is None:
        return StaticAnalysisRun(None, "Build or load a model before running static analysis.")

    selected_load_case = load_case_id or _default_load_case_id(model)
    if selected_load_case is None:
        return StaticAnalysisRun(None, "Add at least one load case before running static analysis.")

    try:
        optimizer = DOFOptimizer(model)
        num_eq, semi_bw, _ = optimizer.optimize()
        assembler = MatrixAssembler(model, num_eq, semi_bw)
        K_banded, F = assembler.assemble(selected_load_case)
        displacements = BandedSolver(K_banded, F, semi_bw).solve()
        processor = PostProcessor(model, displacements, selected_load_case)
        results = processor.to_static_results(
            model.cached_K,
            model.cached_Kff,
            model.cached_F,
            model.cached_Ff,
            optimizer.dof_map,
            selected_load_case,
        )
        model.is_dirty = False
        return StaticAnalysisRun(results)
    except (UnstableStructureError, ValueError) as exc:
        return StaticAnalysisRun(None, f"Static analysis failed: {exc}")


def run_static_analysis_into_state(
    session_state: MutableMapping[str, object],
    load_case_id: str | None = None,
) -> StaticAnalysisRun:
    """Execute static analysis for the active UI model and cache the result."""
    result = run_static_analysis(session_state.get("model"), load_case_id)
    if result.ok:
        session_state["static_results"] = result.results
        session_state["static_analysis_error"] = None
        session_state["model_is_dirty"] = False
    else:
        session_state["static_results"] = None
        session_state["static_analysis_error"] = result.error
    return result


def load_case_ids(model: StructuralModel | None) -> list[str]:
    """Return load-case IDs available for UI selection."""
    if model is None:
        return []
    return list(model.load_cases.keys())


def _default_load_case_id(model: StructuralModel) -> str | None:
    load_cases = load_case_ids(model)
    return load_cases[0] if load_cases else None
