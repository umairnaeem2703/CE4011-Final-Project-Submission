import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ground_motion import GroundMotionConfig
from parser import Element, LoadCase, LumpedMass, Material, Node, Section, StructuralModel, Support
from results import ModalResults, RSAResults, THAResults
from ui.dynamic_analysis import (
    run_modal_analysis_into_state,
    run_response_spectrum_analysis_into_state,
    run_time_history_analysis_into_state,
)


def _dynamic_cantilever():
    model = StructuralModel("ui_dynamic")
    mat = Material("m", E=10.0, density=0.0)
    sec = Section("s", A=2.0, I=1.0)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, 4.0, 0.0)
    model.materials = {mat.id: mat}
    model.sections = {sec.id: sec}
    model.nodes = {1: n1, 2: n2}
    model.elements = {"e1": Element("e1", "frame", n1, n2, mat, sec)}
    model.supports = {1: Support(n1, True, True, True)}
    model.load_cases = {"LC1": LoadCase("LC1")}
    model.lumped_masses = {2: LumpedMass(n2, mass_ux=5.0, mass_uy=5.0)}
    return model


def test_modal_ui_runs_existing_modal_pipeline():
    state = {"model": _dynamic_cantilever()}

    result = run_modal_analysis_into_state(state, num_modes=2)

    assert result.ok and isinstance(result.results, ModalResults)
    assert state["modal_results"] is result.results
    assert result.results.num_modes_extracted == 2
    assert state["modal_analysis_error"] is None


def test_rsa_ui_runs_existing_rsa_pipeline():
    state = {"model": _dynamic_cantilever()}
    modal = run_modal_analysis_into_state(state, num_modes=1).results

    result = run_response_spectrum_analysis_into_state(
        state,
        spectrum_periods=[0.0, modal.periods[0]],
        spectrum_accelerations=[1.0, 2.0],
    )

    assert result.ok and isinstance(result.results, RSAResults)
    assert state["rsa_results"] is result.results
    assert result.results.num_modes == 1
    assert state["rsa_analysis_error"] is None


def test_tha_ui_runs_existing_tha_pipeline(tmp_path):
    gm_file = tmp_path / "gm.txt"
    gm_file.write_text("0.0 0.0\n0.1 1.0\n", encoding="utf-8")
    state = {"model": _dynamic_cantilever()}

    result = run_time_history_analysis_into_state(
        state,
        GroundMotionConfig(str(gm_file), acceleration_unit="m/s2"),
        damping_ratio=0.05,
    )

    assert result.ok and isinstance(result.results, THAResults)
    assert state["tha_results"] is result.results
    assert result.results.num_steps == 2
    assert state["tha_analysis_error"] is None
