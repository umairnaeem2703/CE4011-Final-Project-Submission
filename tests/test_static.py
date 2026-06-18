import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from banded_solver import BandedSolver
from dof_optimizer import DOFOptimizer
from matrix_assembly import MatrixAssembler
from parser import (
    Element,
    LoadCase,
    Material,
    Node,
    NodalLoad,
    PointLoad,
    Section,
    StructuralModel,
    Support,
    UniformlyDL,
    XMLParser,
)
from post_processor import PostProcessor


def _run_static(model, load_case_id):
    optimizer = DOFOptimizer(model)
    num_eq, semi_bw, _ = optimizer.optimize()
    assembler = MatrixAssembler(model, num_eq, semi_bw)
    K_banded, F = assembler.assemble(load_case_id)
    D = BandedSolver(K_banded, F, semi_bw).solve()
    processor = PostProcessor(model, D, load_case_id)
    return processor.to_static_results(
        model.cached_K,
        model.cached_Kff,
        model.cached_F,
        model.cached_Ff,
        optimizer.dof_map,
        load_case_id,
    )


def test_axial_bar_tip_displacement_and_static_results():
    """Verify axial bar tip displacement u = PL/(EA) and Phase 2 result fields."""
    model = StructuralModel("axial_bar")
    mat = Material("m", E=2.0e6)
    sec = Section("s", A=0.01)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, 5.0, 0.0)
    element = Element("e1", "truss", n1, n2, mat, sec)

    model.materials = {mat.id: mat}
    model.sections = {sec.id: sec}
    model.nodes = {1: n1, 2: n2}
    model.elements = {element.id: element}
    model.supports = {
        1: Support(n1, restrain_ux=True, restrain_uy=True),
        2: Support(n2, restrain_uy=True),
    }
    load_case = LoadCase("LC1")
    load_case.loads.append(NodalLoad(n2, fx=10.0))
    model.load_cases = {load_case.id: load_case}

    results = _run_static(model, "LC1")

    assert abs(results.displacements[2][0] - 0.0025) < 0.001 * 0.0025
    assert results.K == [[4000.0]]
    assert results.Kff == [[4000.0]]
    assert results.F == [[10.0]]
    assert results.Ff == [[10.0]]
    assert results.reactions[1][0] == -10.0
    assert "e1" in results.element_forces
    assert set(results.nvm_data["e1"]) == {"x", "N", "V", "M"}


def test_cantilever_beam_tip_deflection():
    """Verify Euler-Bernoulli cantilever tip deflection u = PL^3/(3EI)."""
    model = StructuralModel("cantilever")
    mat = Material("m", E=2.0e8)
    sec = Section("s", A=1.0, I=1.0e-4)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, 3.0, 0.0)
    element = Element("e1", "frame", n1, n2, mat, sec)

    model.materials = {mat.id: mat}
    model.sections = {sec.id: sec}
    model.nodes = {1: n1, 2: n2}
    model.elements = {element.id: element}
    model.supports = {1: Support(n1, restrain_ux=True, restrain_uy=True, restrain_rz=True)}
    load_case = LoadCase("LC1")
    load_case.loads.append(NodalLoad(n2, fy=-10.0))
    model.load_cases = {load_case.id: load_case}

    results = _run_static(model, "LC1")

    expected_tip_uy = -(10.0 * 3.0**3) / (3.0 * 2.0e8 * 1.0e-4)
    assert abs(results.displacements[2][1] - expected_tip_uy) < 0.01 * abs(expected_tip_uy)
    assert abs(results.reactions[1][1] - 10.0) < 1.0e-9
    assert abs(results.reactions[1][2] - 30.0) < 1.0e-9


def test_assignment3_portal_frame_reactions_benchmark():
    """Verify Assignment 3 Example 2 portal-frame reactions and equilibrium."""
    xml_path = os.path.join(os.path.dirname(__file__), "../data/test-frame.xml")
    model = XMLParser(xml_path).parse()

    results = _run_static(model, "LC1")

    assert abs(results.reactions[1][0] - (-20.0)) < 0.02 * 20.0
    assert abs(results.reactions[1][1] - (-5.0)) < 0.02 * 5.0
    assert abs(results.reactions[4][0] - 0.0) < 1.0e-9
    assert abs(results.reactions[4][1] - 25.0) < 0.02 * 25.0
    assert abs(sum(reaction[0] for reaction in results.reactions.values()) + 20.0) < 1.0e-9
    assert abs(sum(reaction[1] for reaction in results.reactions.values()) - 20.0) < 1.0e-9


def test_assignment3_portal_frame_displacements_and_reactions_regression():
    """Lock handout-compatible Example 2 static displacements and reactions."""
    xml_path = os.path.join(os.path.dirname(__file__), "../data/test-frame.xml")
    model = XMLParser(xml_path).parse()

    assert model.materials["M1"].E == 200000.0

    results = _run_static(model, "LC1")

    assert abs(results.displacements[2][0] - 0.03127717530931107) < 1.0e-12
    assert abs(results.displacements[3][1] - (-0.018749999999999968)) < 1.0e-12
    assert abs(results.reactions[1][0] - (-20.0)) < 1.0e-12
    assert abs(results.reactions[4][1] - 25.0) < 1.0e-12


def test_member_end_forces_for_simply_supported_midspan_point_load():
    """Verify local member-end force signs for a simply supported beam."""
    model = StructuralModel("simple_beam")
    mat = Material("m", E=2.0e8)
    sec = Section("s", A=1.0, I=1.0e-4)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, 4.0, 0.0)
    element = Element("e1", "frame", n1, n2, mat, sec)

    model.materials = {mat.id: mat}
    model.sections = {sec.id: sec}
    model.nodes = {1: n1, 2: n2}
    model.elements = {element.id: element}
    model.supports = {
        1: Support(n1, restrain_ux=True, restrain_uy=True),
        2: Support(n2, restrain_uy=True),
    }
    load_case = LoadCase("LC1")
    load_case.loads.append(PointLoad(element, position=2.0, fy=-10.0))
    model.load_cases = {load_case.id: load_case}

    results = _run_static(model, "LC1")
    forces = [value[0] for value in results.element_forces["e1"]]

    assert abs(results.reactions[1][1] - 5.0) < 1.0e-9
    assert abs(results.reactions[2][1] - 5.0) < 1.0e-9
    assert abs(forces[1] - 5.0) < 1.0e-9
    assert abs(forces[4] - (-5.0)) < 1.0e-9
    assert abs(forces[2]) < 1.0e-9
    assert abs(forces[5]) < 1.0e-9


def test_nvm_data_for_simply_supported_midspan_point_load():
    """Verify N/V/M arrays include the textbook midspan moment peak."""
    model = StructuralModel("simple_beam_nvm")
    mat = Material("m", E=2.0e8)
    sec = Section("s", A=1.0, I=1.0e-4)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, 4.0, 0.0)
    element = Element("e1", "frame", n1, n2, mat, sec)

    model.materials = {mat.id: mat}
    model.sections = {sec.id: sec}
    model.nodes = {1: n1, 2: n2}
    model.elements = {element.id: element}
    model.supports = {
        1: Support(n1, restrain_ux=True, restrain_uy=True),
        2: Support(n2, restrain_uy=True),
    }
    load_case = LoadCase("LC1")
    load_case.loads.append(PointLoad(element, position=2.0, fy=-10.0))
    model.load_cases = {load_case.id: load_case}

    nvm = _run_static(model, "LC1").nvm_data["e1"]

    assert len(nvm["x"]) == len(nvm["N"]) == len(nvm["V"]) == len(nvm["M"])
    assert 2.0 in nvm["x"]
    assert abs(max(nvm["M"]) - 10.0) < 0.02 * 10.0
    assert abs(nvm["M"][0]) < 1.0e-9
    assert abs(nvm["M"][-1]) < 1.0e-9


def _frame_element(xj=4.0, yj=0.0):
    mat = Material("m", E=2.0e8)
    sec = Section("s", A=1.0, I=1.0e-4)
    n1 = Node(1, 0.0, 0.0)
    n2 = Node(2, xj, yj)
    return Element("e1", "frame", n1, n2, mat, sec)


def test_horizontal_global_y_udl_matches_existing_local_transverse_udl():
    element = _frame_element()
    local = UniformlyDL(element, wy=-10.0)
    global_y = UniformlyDL(element, coord_system="global", direction="Y", value=-10.0)

    assert global_y.local_components() == local.local_components()
    assert global_y.FEF("fixed-fixed", 4.0) == local.FEF("fixed-fixed", 4.0)


def test_inclined_global_vertical_udl_resolves_to_local_axial_and_transverse_components():
    element = _frame_element(3.0, 4.0)
    load = UniformlyDL(element, coord_system="global", direction="Y", value=-10.0)

    wx, wy = load.local_components()
    fef = load.FEF("fixed-fixed", 5.0)

    assert abs(wx - (-8.0)) < 1.0e-12
    assert abs(wy - (-6.0)) < 1.0e-12
    assert abs(fef[0][0] - (-20.0)) < 1.0e-12
    assert abs(fef[1][0] - 15.0) < 1.0e-12


def test_local_2_udl_remains_existing_local_transverse_behavior():
    element = _frame_element(3.0, 4.0)
    explicit = UniformlyDL(element, coord_system="local", direction="2", value=-7.0)
    legacy = UniformlyDL(element, wy=-7.0)

    assert explicit.local_components() == legacy.local_components()
    assert explicit.FEF("fixed-fixed", 5.0) == legacy.FEF("fixed-fixed", 5.0)


def test_member_point_load_uses_same_coordinate_system_convention_as_udl():
    element = _frame_element(3.0, 4.0)
    global_y = PointLoad(element, position=2.0, coord_system="global", direction="Y", value=-10.0)
    equivalent_local = PointLoad(element, position=2.0, fx=-8.0, fy=-6.0)

    assert global_y.local_components() == equivalent_local.local_components()
    assert global_y.FEF("fixed-fixed", 5.0) == equivalent_local.FEF("fixed-fixed", 5.0)
