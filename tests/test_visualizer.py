import os
import sys

import matplotlib
from matplotlib.colors import to_rgba

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from parser import Element, LoadCase, Material, Node, Section, StructuralModel, Support
from results import ModalResults, RSAResults, StaticResults, THAResults
from visualizer import (
    plot_mode_shape,
    plot_model_preview,
    plot_response_spectrum,
    plot_static_deformed_shape,
    plot_static_nvm_diagrams,
    plot_tha_history,
)


def _frame_model():
    model = StructuralModel("visualizer_frame")
    material = Material("m", E=1.0)
    section = Section("s", A=1.0, I=1.0)
    n1 = Node(1, 0.0, 0.0, dofs=[-1, -1, -1])
    n2 = Node(2, 4.0, 0.0, dofs=[0, 1, 2])
    element = Element("e1", "frame", n1, n2, material, section, release_end=True)

    model.materials = {material.id: material}
    model.sections = {section.id: section}
    model.nodes = {1: n1, 2: n2}
    model.elements = {element.id: element}
    model.supports = {1: Support(n1, restrain_ux=True, restrain_uy=True, restrain_rz=True)}
    model.load_cases = {"LC1": LoadCase("LC1", "test")}
    return model


def _static_results():
    return StaticResults(
        K=[],
        Kff=[],
        F=[],
        Ff=[],
        displacements={1: [0.0, 0.0, 0.0], 2: [0.0, -0.1, 0.02]},
        reactions={1: [0.0, 1.0, 4.0]},
        element_forces={"e1": [[0.0], [1.0], [0.0], [0.0], [-1.0], [0.0]]},
        nvm_data={"e1": {"x": [0.0, 2.0, 4.0], "N": [1.0, 1.0, 1.0], "V": [2.0, -2.0, -2.0], "M": [0.0, 4.0, 0.0]}},
        dof_map={1: [-1, -1, -1], 2: [0, 1, 2]},
        load_case_id="LC1",
    )


def test_model_preview_returns_matplotlib_axes():
    """Verify model preview draws geometry, labels, supports, and hinges."""
    fig, ax = plot_model_preview(_frame_model())

    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)
    assert ax.get_title() == "Model Preview"
    assert len(ax.lines) >= 2
    assert len(ax.patches) >= 2
    assert {text.get_text() for text in ax.texts} >= {"1", "2", "e1"}
    plt.close(ax.figure)


def test_static_deformed_shape_uses_static_results():
    """Verify StaticResults.displacements drive the deformed-shape adapter."""
    fig, ax = plot_static_deformed_shape(_frame_model(), _static_results(), scale_factor=1.0, sub_segments=1)
    deformed_line = ax.lines[1]

    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)
    assert ax.get_title() == "Deformed Shape (Scale = 1.0x)"
    assert list(deformed_line.get_ydata()) == [0.0, -0.1]
    plt.close(ax.figure)


def test_nvm_diagrams_use_static_results_nvm_data():
    """Verify N/V/M adapters consume StaticResults.nvm_data directly."""
    fig, axes = plot_static_nvm_diagrams(_frame_model(), _static_results(), scale=0.1)

    assert isinstance(fig, plt.Figure)
    assert [ax.get_title() for ax in axes] == ["Axial Force (N)", "Shear Force (V)", "Bending Moment (M)"]
    assert len(axes[0].patches) == 2
    assert len(axes[1].patches) == 3
    assert len(axes[2].patches) == 2
    shear_colors = {patch.get_facecolor() for patch in axes[1].patches}
    assert to_rgba("tab:green", 0.35) in shear_colors
    assert to_rgba("tab:red", 0.35) in shear_colors
    plt.close(fig)


def test_mode_shape_plot_uses_modal_results():
    """Verify ModalResults.mode_shapes are mapped through model DOFs."""
    modal = ModalResults(
        K=[],
        M=[],
        eigenvalues=[4.0],
        frequencies=[1.0],
        periods=[0.5],
        mode_shapes=[[0.0, 0.2, 0.0]],
        modal_masses=[1.0],
        participation_factors=[1.0],
        effective_masses=[1.0],
        mass_participation_ratios=[1.0],
        influence_vector=[1.0, 0.0, 0.0],
        total_participating_mass=1.0,
        num_modes_requested=1,
        num_modes_extracted=1,
    )

    fig, ax = plot_mode_shape(_frame_model(), modal, scale_factor=1.0)
    deformed_line = ax.lines[1]

    assert isinstance(fig, plt.Figure)
    assert ax.get_title() == "Mode Shape 1, T = 0.5 s"
    assert list(deformed_line.get_ydata())[-1] == 0.2
    plt.close(ax.figure)


def test_tha_history_plot_uses_tha_results():
    """Verify THAResults histories feed the requested response plot."""
    results = THAResults(
        time_vector=[0.0, 1.0],
        excitation_history=[0.0, 0.1],
        applied_force_history=[[0.0], [-1.0]],
        displacement_history=[[0.0], [0.3]],
        velocity_history=[[0.0], [0.4]],
        acceleration_history=[[0.0], [0.5]],
        base_shear_history=[0.0, 6.0],
        overturning_moment_history=[0.0, 7.0],
        peak_displacement={0: 0.3},
        peak_velocity={0: 0.4},
        peak_acceleration={0: 0.5},
        peak_base_shear=6.0,
        peak_overturning_moment=7.0,
        step_table=[],
        damping_ratio=0.05,
        dt=1.0,
        num_steps=2,
        source_file="synthetic",
        acceleration_unit="m/s2",
        scale_factor=1.0,
        input_format="time_acceleration",
    )

    fig, ax = plot_tha_history(results, response="base_shear")

    assert isinstance(fig, plt.Figure)
    assert ax.get_xlabel() == "Time (s)"
    assert ax.get_ylabel() == "Base Shear (kN)"
    assert list(ax.lines[0].get_ydata()) == [0.0, 6.0]
    plt.close(ax.figure)


def test_response_spectrum_plot_uses_rsa_results():
    """Verify RSAResults spectrum arrays feed the response spectrum plot."""
    results = RSAResults(
        spectrum_periods=[0.0, 1.0, 2.0],
        spectrum_accelerations=[0.1, 0.4, 0.2],
        spectrum_values=[0.1, 0.4, 0.2],
        num_modes=1,
        periods=[1.0],
        modal_response_vectors=[{0: 0.1}],
        modal_base_shears=[1.0],
        modal_overturning_moments=[2.0],
        combination_method="SRSS",
        combined_response={0: 0.1},
        combined_base_shear=1.0,
        combined_overturning_moment=2.0,
        rho_matrix=[[1.0]],
        damping_ratio=0.05,
    )

    fig, ax = plot_response_spectrum(results)

    assert isinstance(fig, plt.Figure)
    assert ax.get_title() == "Response Spectrum"
    assert list(ax.lines[0].get_xdata()) == [0.0, 1.0, 2.0]
    assert list(ax.lines[0].get_ydata()) == [0.1, 0.4, 0.2]
    plt.close(ax.figure)
