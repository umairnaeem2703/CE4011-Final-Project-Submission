import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from dof_optimizer import DOFManager, DOFOptimizer
from parser import Element, Material, Node, Section, StructuralModel, Support


def _basic_parts():
    return Material("m", E=200000.0), Section("s", A=1.0, I=1.0)


def _add_node(model, node_id, x, y):
    model.nodes[node_id] = Node(node_id, x, y)
    return model.nodes[node_id]


def _add_frame(model, element_id, i, j, release_start=False, release_end=False, rigid=False):
    material, section = next(iter(model.materials.values())), next(iter(model.sections.values()))
    model.elements[element_id] = Element(
        element_id,
        "frame",
        model.nodes[i],
        model.nodes[j],
        material,
        section,
        release_start=release_start,
        release_end=release_end,
        is_axially_rigid=rigid,
    )


def _new_model():
    model = StructuralModel()
    material, section = _basic_parts()
    model.materials[material.id] = material
    model.sections[section.id] = section
    return model


def test_simple_frame_dof_assignment():
    model = _new_model()
    _add_node(model, 1, 0.0, 0.0)
    _add_node(model, 2, 1.0, 1.0)
    _add_frame(model, "e1", 1, 2, release_end=True)
    model.supports[1] = Support(model.nodes[1], True, True, True)
    model.supports[2] = Support(model.nodes[2], False, False, True)

    num_eq, dof_map, free_dofs, restrained_dofs = DOFManager(model).build()

    assert num_eq == 2
    assert dof_map[1] == [-1, -1, -1]
    assert dof_map[2] == [0, 1, -1]
    assert free_dofs == [0, 1]
    assert (1, 0) in restrained_dofs


def test_same_y_nodes_without_diaphragm_do_not_share_ux():
    model = _new_model()
    _add_node(model, 1, 0.0, 3.0)
    _add_node(model, 2, 1.0, 3.0)
    _add_node(model, 3, 2.0, 3.0)
    _add_node(model, 4, 0.0, 0.0)
    _add_frame(model, "c1", 4, 1)
    _add_frame(model, "b1", 1, 2)
    _add_frame(model, "b2", 2, 3)
    model.supports[4] = Support(model.nodes[4], True, True, True)

    _, dof_map, _, _ = DOFManager(model).build()

    assert len({dof_map[1][0], dof_map[2][0], dof_map[3][0]}) == 3


def test_explicit_rigid_diaphragm_group_shares_ux():
    model = _new_model()
    _add_node(model, 1, 0.0, 3.0)
    _add_node(model, 2, 1.0, 3.0)
    _add_node(model, 3, 2.0, 3.0)
    _add_node(model, 4, 0.0, 0.0)
    _add_frame(model, "c1", 4, 1)
    _add_frame(model, "b1", 1, 2)
    _add_frame(model, "b2", 2, 3)
    model.supports[4] = Support(model.nodes[4], True, True, True)
    model.diaphragm_ux_groups["floor_1"] = [1, 2, 3]

    _, dof_map, _, _ = DOFManager(model).build()

    assert dof_map[1][0] == dof_map[2][0] == dof_map[3][0]
    assert len({dof_map[1][1], dof_map[2][1], dof_map[3][1]}) == 3
    assert len({dof_map[1][2], dof_map[2][2], dof_map[3][2]}) == 3


def test_axially_rigid_member_coupling():
    model = _new_model()
    _add_node(model, 1, 0.0, 1.0)
    _add_node(model, 2, 1.0, 1.0)
    _add_node(model, 3, 0.0, 0.0)
    _add_frame(model, "c1", 3, 1)
    _add_frame(model, "r1", 1, 2, rigid=True)
    model.supports[3] = Support(model.nodes[3], True, True, True)

    num_eq, dof_map, _, _ = DOFManager(model).build()

    assert dof_map[1] == dof_map[2]
    assert num_eq == 3


def test_spinning_node_suppressed_from_active_dynamic_dofs():
    model = _new_model()
    _add_node(model, 1, -1.0, 0.0)
    _add_node(model, 2, 0.0, 1.0)
    _add_node(model, 3, 1.0, 0.0)
    _add_node(model, 4, 0.0, 0.0)
    _add_frame(model, "e1", 1, 2, release_end=True)
    _add_frame(model, "e2", 3, 2, release_end=True)
    _add_frame(model, "e3", 4, 2, release_end=True)
    for node_id in (1, 3, 4):
        model.supports[node_id] = Support(model.nodes[node_id], True, True, True)

    optimizer = DOFOptimizer(model)
    optimizer.optimize()

    assert optimizer.dof_map[2][2] == -1
    assert -1 not in optimizer.active_dynamic_dofs


def test_dirty_state_clears_cache():
    model = StructuralModel()
    model.cached_dof_map = {1: [0, 1, 2]}
    model.cached_K = [[1.0]]
    model.cached_F = [[2.0]]
    model.cached_M = [[3.0]]
    model.cached_C = [[4.0]]
    model.is_dirty = False

    model.mark_dirty()

    assert model.is_dirty is True
    assert model.cached_dof_map is None
    assert model.cached_K is None
    assert model.cached_F is None
    assert model.cached_M is None
    assert model.cached_C is None
