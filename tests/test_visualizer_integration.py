import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from banded_solver import BandedSolver
from dof_optimizer import DOFOptimizer
from ground_motion import GroundMotionConfig, read_ground_motion
from matrix_assembly import MatrixAssembler
from modal_solver import ModalSolver
from newmark_solver import NewmarkTimeHistorySolver
from parser import Element, LoadCase, Material, Node, NodalLoad, Section, StructuralModel, Support
from post_processor import PostProcessor
from results import RSAResults, StaticResults
from rsa_solver import ResponseSpectrumSolver
from visualizer import (
    plot_mode_shape,
    plot_response_spectrum,
    plot_static_deformed_shape,
    plot_static_nvm_diagrams,
    plot_tha_history,
)


def _static_truss_model():
    model = StructuralModel("visualizer_static_real")
    material = Material("m", E=2.0e6)
    section = Section("s", A=0.01)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, 5.0, 0.0)
    element = Element("e1", "truss", n1, n2, material, section)

    model.materials = {material.id: material}
    model.sections = {section.id: section}
    model.nodes = {1: n1, 2: n2}
    model.elements = {element.id: element}
    model.supports = {
        1: Support(n1, restrain_ux=True, restrain_uy=True),
        2: Support(n2, restrain_uy=True),
    }
    load_case = LoadCase("LC1")
    load_case.loads.append(NodalLoad(n2, fx=10.0))
    model.load_cases = {load_case.id: load_case}
    return model


def _run_static(model):
    optimizer = DOFOptimizer(model)
    num_eq, semi_bw, _ = optimizer.optimize()
    K_banded, _ = MatrixAssembler(model, num_eq, semi_bw).assemble("LC1")
    D = BandedSolver(K_banded, model.cached_F, semi_bw).solve()
    processor = PostProcessor(model, D, "LC1")
    return processor.to_static_results(
        model.cached_K,
        model.cached_Kff,
        model.cached_F,
        model.cached_Ff,
        optimizer.dof_map,
        "LC1",
    )


def _modal_model():
    model = StructuralModel("visualizer_modal_real")
    material = Material("m", E=1.0)
    section = Section("s", A=1.0, I=1.0)
    n1 = Node(1, 0.0, 0.0, dofs=[-1, -1, -1])
    n2 = Node(2, 1.0, 0.0, dofs=[0, -1, -1])
    element = Element("e1", "truss", n1, n2, material, section)
    model.materials = {material.id: material}
    model.sections = {section.id: section}
    model.nodes = {1: n1, 2: n2}
    model.elements = {element.id: element}
    model.supports = {1: Support(n1, restrain_ux=True, restrain_uy=True, restrain_rz=True)}
    return model


def test_visualizer_accepts_real_static_result_shape():
    model = _static_truss_model()
    results = _run_static(model)

    fig_def, ax_def = plot_static_deformed_shape(model, results, scale_factor=1.0, sub_segments=1)
    fig_nvm, axes = plot_static_nvm_diagrams(model, results, scale=0.1)

    assert isinstance(fig_def, plt.Figure)
    assert ax_def.lines
    assert isinstance(fig_nvm, plt.Figure)
    assert len(axes) == 3
    plt.close(fig_def)
    plt.close(fig_nvm)


def test_visualizer_accepts_real_modal_result_shape():
    model = _modal_model()
    results = ModalSolver([[8.0]], [[2.0]]).solve(r=[1.0], num_modes=1)

    fig, ax = plot_mode_shape(model, results, scale_factor=1.0)

    assert isinstance(fig, plt.Figure)
    assert ax.get_title().startswith("Mode Shape 1")
    assert len(ax.lines) >= 2
    plt.close(fig)


def test_visualizer_accepts_real_tha_result_shape(tmp_path):
    gm_file = tmp_path / "gm.txt"
    gm_file.write_text("0.0 0.0\n1.0 1.0\n", encoding="utf-8")
    record = read_ground_motion(GroundMotionConfig(str(gm_file), acceleration_unit="m/s2"))
    results = NewmarkTimeHistorySolver([[4.0]], [[2.0]], [[0.0]]).solve_ground_motion(record, [1.0])

    fig, ax = plot_tha_history(results, response="displacement")

    assert isinstance(fig, plt.Figure)
    assert list(ax.lines[0].get_xdata()) == results.time_vector
    assert list(ax.lines[0].get_ydata()) == [step[0] for step in results.displacement_history]
    plt.close(fig)


def test_visualizer_accepts_real_rsa_result_shape():
    modal_results = ModalSolver([[8.0]], [[2.0]]).solve(r=[1.0], num_modes=1)
    results = ResponseSpectrumSolver(modal_results, [0.0, modal_results.periods[0]], [1.0, 2.0]).solve()

    fig, ax = plot_response_spectrum(results)

    assert isinstance(fig, plt.Figure)
    assert list(ax.lines[0].get_xdata()) == results.spectrum_periods
    assert list(ax.lines[0].get_ydata()) == results.spectrum_accelerations
    plt.close(fig)


def test_visualizer_handles_missing_optional_result_fields_gracefully():
    model = _static_truss_model()
    static_results = StaticResults(
        K=[],
        Kff=[],
        F=[],
        Ff=[],
        displacements={1: [0.0, 0.0, 0.0], 2: [0.01, 0.0, 0.0]},
        reactions={},
        element_forces={},
        nvm_data={"e1": {"N": [1.0, -1.0], "V": [], "M": []}},
        dof_map={},
        load_case_id="LC1",
    )
    rsa_results = RSAResults(
        spectrum_periods=[0.0, 1.0],
        spectrum_accelerations=[],
        spectrum_values=[0.2, 0.4],
        num_modes=0,
        periods=[],
        modal_response_vectors=[],
        modal_base_shears=[],
        modal_overturning_moments=[],
        combination_method="SRSS",
        combined_response={},
        combined_base_shear=0.0,
        combined_overturning_moment=0.0,
        rho_matrix=[],
        damping_ratio=0.05,
    )

    fig_nvm, axes = plot_static_nvm_diagrams(model, static_results, scale=0.1)
    fig_rsa, ax_rsa = plot_response_spectrum(rsa_results)

    assert len(axes) == 3
    assert list(ax_rsa.lines[0].get_ydata()) == [0.2, 0.4]
    plt.close(fig_nvm)
    plt.close(fig_rsa)


def test_visualizer_can_save_figure_to_results_or_tmp_path(tmp_path):
    model = _static_truss_model()
    results = _run_static(model)
    fig, _ = plot_static_deformed_shape(model, results, scale_factor=1.0)
    output_path = tmp_path / "visualizer_static.png"

    fig.savefig(output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0
    plt.close(fig)
