import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from parser import StructuralModel
from ui.model_input import build_model_from_tables, build_model_from_xml_upload, store_model_in_state


XML_MODEL = """\
<model name="XML Demo" unit_system="kN_m_tonne">
  <materials><material id="m1" E="200000" density="7.85" /></materials>
  <sections><section id="s1" A="0.02" I="0.0001" /></sections>
  <nodes>
    <node id="1" x="0" y="0" />
    <node id="2" x="3" y="0" />
  </nodes>
  <elements><frame id="e1" node_i="1" node_j="2" material="m1" section="s1" /></elements>
  <boundary_conditions><support node="1" type="fixed" /></boundary_conditions>
  <load_cases><load_case id="LC1"><point_load node="2" fy="-10" /></load_case></load_cases>
</model>
"""


def test_xml_upload_builds_structural_model():
    result = build_model_from_xml_upload(io.BytesIO(XML_MODEL.encode("utf-8")))

    assert result.ok and isinstance(result.model, StructuralModel)
    assert result.model.name == "XML Demo"
    assert result.model.is_dirty is True
    assert result.model.elements["e1"].node_j.id == 2


def test_table_input_builds_structural_model():
    result = build_model_from_tables(
        materials="id,E,density\nm1,200000,7.85\n",
        sections="id,A,I\ns1,0.02,0.0001\n",
        nodes="id,x,y\n1,0,0\n2,3,0\n",
        elements="id,type,node_i,node_j,material,section\ne1,frame,1,2,m1,s1\n",
        supports="node,type\n1,fixed\n",
        loads="load_case,type,node,fx,fy,mz\nLC1,nodal,2,0,-10,0\n",
        masses="node,mass_ux,mass_uy,inertia_rz\n2,1.5,1.5,0\n",
    )

    assert result.ok and result.model.nodes[2].x == 3.0
    assert result.model.load_cases["LC1"].loads[0].fy == -10.0
    assert result.model.lumped_masses[2].mass_ux == 1.5


def test_invalid_model_input_returns_user_facing_error():
    result = build_model_from_tables(
        materials="id,E\nm1,200000\n",
        sections="id,A,I\ns1,0.02,0.0001\n",
        nodes="id,x,y\n1,0,0\n2,0,0\n",
        elements="id,type,node_i,node_j,material,section\ne1,frame,1,2,m1,s1\n",
        supports="node,type\n1,fixed\n",
    )

    assert result.model is None
    assert "zero length" in result.error.lower()


def test_missing_element_node_returns_user_facing_error():
    result = build_model_from_tables(
        materials="id,E\nm1,200000\n",
        sections="id,A,I\ns1,0.02,0.0001\n",
        nodes="id,x,y\n1,0,0\n",
        elements="id,type,node_i,node_j,material,section\ne1,frame,1,2,m1,s1\n",
    )

    assert result.model is None
    assert "missing node 2" in result.error.lower()


def test_missing_material_or_section_returns_user_facing_error():
    result = build_model_from_tables(
        materials="id,E\nm1,200000\n",
        sections="id,A,I\ns1,0.02,0.0001\n",
        nodes="id,x,y\n1,0,0\n2,3,0\n",
        elements="id,type,node_i,node_j,material,section\ne1,frame,1,2,m2,s1\n",
    )

    assert result.model is None
    assert "missing material" in result.error.lower()


def test_invalid_support_returns_user_facing_error():
    result = build_model_from_tables(
        materials="id,E\nm1,200000\n",
        sections="id,A,I\ns1,0.02,0.0001\n",
        nodes="id,x,y\n1,0,0\n2,3,0\n",
        elements="id,type,node_i,node_j,material,section\ne1,frame,1,2,m1,s1\n",
        supports="node,type\n1,clamped-ish\n",
    )

    assert result.model is None
    assert "invalid support" in result.error.lower()


def test_store_model_in_state_marks_model_dirty():
    model = StructuralModel()
    model.is_dirty = False
    state = {"static_results": object(), "modal_results": object(), "rsa_results": object(), "tha_results": object()}

    store_model_in_state(state, model)

    assert state["model"] is model
    assert state["model_is_dirty"] is True
    assert model.is_dirty is True
    assert state["static_results"] is None
