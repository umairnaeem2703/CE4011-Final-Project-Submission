import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from dof_optimizer import DOFOptimizer
from matrix_assembly import DynamicAssembler, MatrixAssembler
from model_builder import ModelBuilder
from modal_solver import ModalSolver
from parser import Element, LoadCase, LumpedMass, Material, Node, Section, StructuralModel, Support, XMLParser


def _cantilever(density=0.0, tip_mass=0.0, unit_system="kN_m_tonne"):
    model = StructuralModel("dynamic_cantilever")
    model.unit_system = unit_system
    mat = Material("m", E=10.0, density=density)
    sec = Section("s", A=2.0, I=1.0)
    n1, n2 = Node(1, 0.0, 0.0), Node(2, 4.0, 0.0)
    element = Element("e1", "frame", n1, n2, mat, sec)
    model.materials = {mat.id: mat}
    model.sections = {sec.id: sec}
    model.nodes = {1: n1, 2: n2}
    model.elements = {element.id: element}
    model.supports = {1: Support(n1, True, True, True)}
    model.load_cases = {"LC1": LoadCase("LC1")}
    if tip_mass:
        model.lumped_masses = {2: tip_mass}
    return model


def _assemble(model, matrix_type="lumped"):
    optimizer = DOFOptimizer(model)
    num_eq, semi_bw, _ = optimizer.optimize()
    static_assembler = MatrixAssembler(model, num_eq, semi_bw)
    static_assembler.assemble("LC1")
    return DynamicAssembler(model, num_eq).assemble_dynamic_data(model.cached_K, matrix_type=matrix_type)


def test_lumped_mass_cantilever_with_tip_mass():
    """Verify element self-mass plus explicit tip mass on free translations."""
    data = _assemble(_cantilever(density=3.0, tip_mass=5.0))

    assert data.M[0][0] == 12.0 + 5.0
    assert data.M[1][1] == 12.0 + 5.0
    assert data.M[2][2] == 0.0


def test_rayleigh_damping_matrix():
    """Verify C = alpha*M + beta*K for a one-element cantilever."""
    model = _cantilever(density=1.0)
    model.rayleigh_alpha = 0.5
    model.rayleigh_beta = 0.25

    data = _assemble(model)

    assert data.C[1][1] == 0.5 * data.M[1][1] + 0.25 * data.K[1][1]


def test_active_dynamic_dofs_exclude_massless_nodes():
    """Verify massless rotational/free equations are excluded from dynamic DOFs."""
    data = _assemble(_cantilever(density=0.0, tip_mass=5.0))

    assert data.active_dynamic_dofs == [0, 1]


def test_reduced_dynamic_matrices_free_dofs():
    """Verify reduced dynamic matrices are condensed to active dynamic DOFs."""
    data = _assemble(_cantilever(density=0.0, tip_mass=5.0))

    assert data.Mff == [[5.0, 0.0], [0.0, 5.0]]
    assert data.Kff[1][1] == 30.0 / 64.0
    assert data.condensed_massless_dofs == [2]


def test_uy_only_lumped_mass_cantilever_modal_pipeline():
    """Verify a cantilever with only tip UY mass remains dynamically active."""
    model = _cantilever(density=0.0)
    model.lumped_masses = {2: LumpedMass(model.nodes[2], mass_ux=0.0, mass_uy=5.0, inertia_rz=0.0)}

    data = _assemble(model)
    results = ModalSolver(data.Kff, data.Mff).solve(num_modes=1)

    assert data.active_dynamic_dofs == [model.nodes[2].dofs[1]]
    assert data.Mff == [[5.0]]
    assert data.Kff[0][0] > 0.0
    assert results.frequencies[0] > 0.0


def test_density_unit_conversion_kg_to_tonne():
    """Verify N-m-kg density is converted to internal tonne mass."""
    data = _assemble(_cantilever(density=3000.0, unit_system="N_m_kg"))

    assert data.M[0][0] == 12.0


def test_massless_dof_static_condensation_reduces_stiffness():
    """Verify Kaa - Kam*Kmm^-1*Kma for a massless rotational DOF."""
    data = _assemble(_cantilever(density=0.0, tip_mass=5.0))

    assert data.Kff[1][1] == 0.46875


def test_dynamic_reduction_does_not_directly_delete_coupled_massless_dofs():
    """Verify stiffness-coupled massless DOFs are condensed, not directly sliced."""
    data = _assemble(_cantilever(density=0.0, tip_mass=5.0))

    assert data.Kff[1][1] != data.K[1][1]
    assert data.condensed_massless_dofs == [2]


def test_rotation_excluded_without_rotational_inertia():
    """Verify consistent-mass rotations are excluded unless explicit inertia exists."""
    data = _assemble(_cantilever(density=1.0), matrix_type="consistent")

    assert 2 not in data.active_dynamic_dofs


def test_dynamic_assembly_data_contains_phase4_ready_fields():
    """Verify Phase 4 can inspect unit system and condensed DOF metadata."""
    model = _cantilever(density=0.0)
    model.lumped_masses = {2: LumpedMass(model.nodes[2], mass_ux=5.0, mass_uy=5.0, inertia_rz=2.0)}

    data = _assemble(model)

    assert data.unit_system == "kN_m_tonne"
    assert data.condensed_massless_dofs == []
    assert data.active_dynamic_dofs == [0, 1, 2]


def test_parsed_lumped_mass_contributes_to_mass_matrix(tmp_path):
    """Verify XML round-tripped nodal mass is scattered to dynamic DOFs."""
    builder = ModelBuilder(name="parsed_mass")
    builder.add_material("m", E=10.0, density=0.0)
    builder.add_section("s", A=2.0, I=1.0)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 4.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m", "s")
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)
    builder.model.load_cases = {"LC1": LoadCase("LC1")}
    builder.add_lumped_mass(2, mass_ux=4.0, mass_uy=6.0, inertia_rz=1.5)

    xml_path = tmp_path / "parsed_mass.xml"
    builder.export_xml(xml_path)
    data = _assemble(XMLParser(xml_path).parse())

    assert [data.M[i][i] for i in range(3)] == [4.0, 6.0, 1.5]
