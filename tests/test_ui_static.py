import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from parser import Element, LoadCase, Material, Node, NodalLoad, Section, StructuralModel, Support
from results import StaticResults
from ui.static_analysis import run_static_analysis, run_static_analysis_into_state


def _axial_bar_model(restrain_tip_uy=True):
    model = StructuralModel("ui_static")
    mat = Material("m", E=2.0e6)
    sec = Section("s", A=0.01)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, 5.0, 0.0)
    model.materials = {mat.id: mat}
    model.sections = {sec.id: sec}
    model.nodes = {1: n1, 2: n2}
    model.elements = {"e1": Element("e1", "truss", n1, n2, mat, sec)}
    model.supports = {1: Support(n1, True, True), 2: Support(n2, False, restrain_tip_uy)}
    load_case = LoadCase("LC1")
    load_case.loads.append(NodalLoad(n2, fx=10.0))
    model.load_cases = {load_case.id: load_case}
    return model


def _fixed_bar_without_load_cases(settlement_ux=0.0):
    model = StructuralModel("ui_static_settlement")
    mat = Material("m", E=2.0e6)
    sec = Section("s", A=0.01)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, 5.0, 0.0)
    model.materials = {mat.id: mat}
    model.sections = {sec.id: sec}
    model.nodes = {1: n1, 2: n2}
    model.elements = {"e1": Element("e1", "truss", n1, n2, mat, sec)}
    model.supports = {
        1: Support(n1, True, True, settlement_ux=settlement_ux),
        2: Support(n2, True, True),
    }
    return model


def test_static_ui_runs_existing_static_pipeline():
    result = run_static_analysis(_axial_bar_model(), "LC1")

    assert result.ok and isinstance(result.results, StaticResults)
    assert abs(result.results.displacements[2][0] - 0.0025) < 2.5e-6
    assert result.results.Kff == [[4000.0]]


def test_static_results_stored_in_ui_state():
    state = {"model": _axial_bar_model()}

    result = run_static_analysis_into_state(state, "LC1")

    assert result.ok
    assert state["static_results"] is result.results
    assert state["static_analysis_error"] is None
    assert state["model_is_dirty"] is False


def test_static_ui_reports_solver_error_without_crashing():
    state = {"model": _axial_bar_model(restrain_tip_uy=False), "static_results": object()}

    result = run_static_analysis_into_state(state, "LC1")

    assert not result.ok
    assert state["static_results"] is None
    assert "static analysis failed" in state["static_analysis_error"].lower()


def test_static_ui_runs_settlement_only_model_without_load_case():
    model = _fixed_bar_without_load_cases(settlement_ux=0.01)

    result = run_static_analysis(model)

    assert result.ok and isinstance(result.results, StaticResults)
    assert result.results.load_case_id == "SETTLEMENT"
    assert result.results.displacements[1][0] == 0.01
    assert abs(result.results.element_forces["e1"][0][0]) > 0.0
    assert abs(result.results.reactions[1][0]) > 0.0
    assert model.load_cases == {}


def test_static_ui_still_requires_load_case_without_settlement():
    result = run_static_analysis(_fixed_bar_without_load_cases())

    assert not result.ok
    assert result.error == "Add at least one load case before running static analysis."
