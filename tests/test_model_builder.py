import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from model_builder import ModelBuilder
from banded_solver import UnstableStructureError
from parser import PointLoad, StructuralModel, TemperatureL, UniformlyDL, XMLParser
import pytest


def test_model_builder_creates_minimal_valid_model():
    builder = ModelBuilder(name="Builder Demo")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)

    model = builder.build(validate=True)

    assert model.elements["e1"].node_j is model.nodes[2]
    assert model.supports[1].restrain_rz is True


def test_model_builder_returns_existing_structural_model_instance():
    existing = StructuralModel(name="Existing")
    model = ModelBuilder(existing).build()

    assert model is existing


def test_model_builder_marks_dirty_when_supported():
    model = StructuralModel()
    model.is_dirty = False
    model.cached_K = [[1.0]]

    ModelBuilder(model).add_node(1, 0.0, 0.0)

    assert model.is_dirty is True
    assert model.cached_K is None


def test_model_builder_validate_raises_without_supports():
    builder = ModelBuilder()
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")

    with pytest.raises(UnstableStructureError, match="No boundary conditions"):
        builder.build(validate=True)


def test_model_builder_validate_raises_on_floating_unsupported_substructure():
    builder = ModelBuilder()
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    for node_id, x in [(1, 0.0), (2, 3.0), (3, 10.0), (4, 13.0)]:
        builder.add_node(node_id, x, 0.0)
    builder.add_element("supported", "frame", 1, 2, "m1", "s1")
    builder.add_element("floating", "frame", 3, 4, "m1", "s1")
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)

    with pytest.raises(UnstableStructureError, match="floating"):
        builder.build(validate=True)


def test_model_builder_validate_false_returns_incomplete_model():
    builder = ModelBuilder()
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")

    model = builder.build(validate=False)

    assert model is builder.model
    assert model.supports == {}


def test_model_builder_add_temperature_load_stores_existing_backend_load():
    builder = ModelBuilder()
    builder.add_material("m1", E=200000.0, alpha=1.2e-5)
    builder.add_section("s1", A=0.02, I=0.0001, d=0.3)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    member = builder.add_element("e1", "frame", 1, 2, "m1", "s1")

    load = builder.add_temperature_load("LC_TEMP", "e1", Tu=25.0, Tb=10.0)

    assert isinstance(load, TemperatureL)
    assert builder.model.load_cases["LC_TEMP"].loads == [load]
    assert load.element is member
    assert (load.Tu, load.Tb) == pytest.approx((25.0, 10.0))


def test_model_builder_xml_export_round_trips_counts(tmp_path):
    builder = ModelBuilder(name="Round Trip")
    builder.add_material("m1", E=200000.0, alpha=1.2e-5, density=7.85)
    builder.add_section("s1", A=0.02, I=0.0001, d=0.3)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1", release_end=True)
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True, settlement_rz=0.01)
    builder.add_nodal_load("LC1", 2, fy=-10.0)

    xml_path = tmp_path / "round_trip.xml"
    builder.export_xml(xml_path)
    parsed = XMLParser(xml_path).parse()
    model = builder.model

    assert (
        len(parsed.nodes),
        len(parsed.elements),
        len(parsed.supports),
        len(parsed.materials),
        len(parsed.sections),
        len(parsed.load_cases),
    ) == (
        len(model.nodes),
        len(model.elements),
        len(model.supports),
        len(model.materials),
        len(model.sections),
        len(model.load_cases),
    )
    assert parsed.supports[1].settlement_rz == pytest.approx(model.supports[1].settlement_rz)


def test_model_builder_xml_export_round_trips_direct_ea_ei(tmp_path):
    builder = ModelBuilder(name="Effective Stiffness Round Trip")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001, d=0.3, EA=1234.0, EI=56.7)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)

    xml_path = tmp_path / "effective_stiffness_round_trip.xml"
    builder.export_xml(xml_path)
    section_el = ET.parse(xml_path).getroot().find("./sections/section")
    parsed = XMLParser(xml_path).parse()
    parsed_section = parsed.sections["s1"]

    assert section_el.attrib["EA"] == "1234"
    assert section_el.attrib["EI"] == "56.7"
    assert parsed_section.EA == pytest.approx(1234.0)
    assert parsed_section.EI == pytest.approx(56.7)


def test_model_builder_xml_export_round_trips_node_hinge(tmp_path):
    builder = ModelBuilder(name="Node Hinge Round Trip")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0, is_hinged=True)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)

    xml_path = tmp_path / "node_hinge_round_trip.xml"
    builder.export_xml(xml_path)
    node_el = ET.parse(xml_path).getroot().find("./nodes/node[@id='2']")
    parsed = XMLParser(xml_path).parse()

    assert node_el.attrib["is_hinged"] == "true"
    assert parsed.nodes[2].is_hinged is True
    assert parsed.elements["e1"].effective_release_end() is True


def test_model_builder_xml_export_round_trips_lumped_mass(tmp_path):
    builder = ModelBuilder(name="Mass Round Trip")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)
    builder.add_lumped_mass(2, mass_ux=10.0, mass_uy=12.5, inertia_rz=0.75)

    xml_path = tmp_path / "lumped_mass_round_trip.xml"
    builder.export_xml(xml_path)
    mass_el = ET.parse(xml_path).getroot().find("./lumped_masses/lumped_mass")
    parsed = XMLParser(xml_path).parse()
    parsed_mass = parsed.lumped_masses[2]

    assert mass_el.attrib == {"node": "2", "mass_ux": "10", "mass_uy": "12.5", "inertia_rz": "0.75"}
    assert len(parsed.lumped_masses) == 1
    assert parsed_mass.node.id == 2
    assert parsed_mass.mass_ux == pytest.approx(10.0)
    assert parsed_mass.mass_uy == pytest.approx(12.5)
    assert parsed_mass.inertia_rz == pytest.approx(0.75)


def test_model_builder_xml_export_preserves_member_load_coordinate_metadata(tmp_path):
    builder = ModelBuilder(name="Member Load Metadata")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 4.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    builder.add_member_udl("LC1", "e1", coord_system="global", direction="Y", value=-5.0)
    builder.add_member_point_load("LC1", "e1", position=2.0, coord_system="local", direction="2", value=-7.0)

    xml_path = tmp_path / "member_load_metadata.xml"
    builder.export_xml(xml_path)
    root = ET.parse(xml_path).getroot()
    udl_el = root.find("./load_cases/load_case/member_udl")
    point_el = root.find("./load_cases/load_case/member_point_load")
    parsed_loads = XMLParser(xml_path).parse().load_cases["LC1"].loads

    assert udl_el.attrib["coord_system"] == "global"
    assert udl_el.attrib["direction"] == "Y"
    assert udl_el.attrib["value"] == "-5"
    assert point_el.attrib["direction"] == "2"
    assert isinstance(parsed_loads[0], UniformlyDL)
    assert isinstance(parsed_loads[1], PointLoad)
    assert parsed_loads[0].coord_system == "global"
    assert parsed_loads[0].direction == "Y"
    assert parsed_loads[0].value == pytest.approx(-5.0)
    assert parsed_loads[1].coord_system == "local"
    assert parsed_loads[1].direction == "2"
    assert parsed_loads[1].value == pytest.approx(-7.0)


def test_model_builder_xml_export_preserves_live_builder_state(tmp_path):
    builder = ModelBuilder(name="Live State Export")
    builder.add_material("M1", E=200000.0, alpha=1.2e-5, density=7.85)
    builder.add_material("M2", E=150000.0, alpha=9.5e-6, density=6.9)
    builder.add_section("S1", A=0.02, I=0.0001, d=0.3)
    builder.add_section("S2", A=0.03, I=0.0002, d=0.4, EA=1234.0, EI=567.0)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_node(3, 6.0, 0.0)
    builder.add_element("E1", "frame", 1, 2, "M1", "S1")
    builder.add_element("E2", "frame", 2, 3, "M2", "S2")
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)
    builder.add_lumped_mass(3, mass_ux=4.5, mass_uy=5.5, inertia_rz=0.75)
    builder.add_diaphragm_group("D1", [2, 3])

    xml_path = tmp_path / "live_state_export.xml"
    builder.export_xml(xml_path)
    root = ET.parse(xml_path).getroot()
    parsed = XMLParser(xml_path).parse()

    assert [mat.attrib["id"] for mat in root.find("./materials").findall("material")] == ["M1", "M2"]
    assert [sec.attrib["id"] for sec in root.find("./sections").findall("section")] == ["S1", "S2"]
    assert root.find("./elements/frame[@id='E1']").attrib["material"] == "M1"
    assert root.find("./elements/frame[@id='E2']").attrib["section"] == "S2"
    assert root.find("./lumped_masses/lumped_mass").attrib["node"] == "3"
    assert root.find("./diaphragms/diaphragm").attrib["nodes"] == "2,3"
    assert parsed.materials["M2"].density == pytest.approx(6.9)
    assert parsed.sections["S2"].EA == pytest.approx(1234.0)
    assert parsed.lumped_masses[3].mass_uy == pytest.approx(5.5)
    assert parsed.diaphragm_ux_groups["D1"] == [2, 3]


def test_model_builder_rename_node_preserves_references():
    builder = ModelBuilder()
    builder.add_material("M1", E=200000.0)
    builder.add_section("S1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("E1", "frame", 1, 2, "M1", "S1")
    builder.add_support(2, restrain_ux=True)
    builder.add_lumped_mass(2, mass_ux=5.0)
    builder.add_diaphragm_group("D1", [1, 2])
    builder.add_nodal_load("LC1", 2, fy=-10.0)

    node = builder.rename_node(2, 5)

    assert builder.model.elements["E1"].node_j is node
    assert builder.model.load_cases["LC1"].loads[0].node is node
    assert 5 in builder.model.supports and 5 in builder.model.lumped_masses
    assert builder.model.diaphragm_ux_groups["D1"] == [1, 5]


def test_model_builder_rename_node_xml_export_uses_new_id(tmp_path):
    builder = ModelBuilder()
    builder.add_material("M1", E=200000.0)
    builder.add_section("S1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("E1", "frame", 1, 2, "M1", "S1")
    builder.add_support(2, restrain_ux=True)
    builder.add_lumped_mass(2, mass_ux=5.0)

    builder.rename_node(2, 5)
    xml_path = tmp_path / "renamed_node.xml"
    builder.export_xml(xml_path)
    root = ET.parse(xml_path).getroot()

    assert root.find("./nodes/node[@id='5']") is not None
    assert root.find("./elements/frame[@id='E1']").attrib["node_j"] == "5"
    assert root.find("./boundary_conditions/support").attrib["node"] == "5"
    assert root.find("./lumped_masses/lumped_mass").attrib["node"] == "5"


def test_model_builder_rename_member_preserves_load_reference_and_xml(tmp_path):
    builder = ModelBuilder()
    builder.add_material("M1", E=200000.0)
    builder.add_section("S1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    member = builder.add_element("E1", "frame", 1, 2, "M1", "S1")
    builder.add_member_udl("LC1", "E1", wy=-5.0)

    renamed = builder.rename_element("E1", "GirderA")
    xml_path = tmp_path / "renamed_member.xml"
    builder.export_xml(xml_path)
    root = ET.parse(xml_path).getroot()

    assert renamed is member
    assert builder.model.load_cases["LC1"].loads[0].element is renamed
    assert root.find("./elements/frame[@id='GirderA']") is not None
    assert root.find("./load_cases/load_case/member_udl").attrib["element"] == "GirderA"


def test_model_builder_rename_rejects_invalid_duplicate_ids():
    builder = ModelBuilder()
    builder.add_material("M1", E=200000.0)
    builder.add_section("S1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("E1", "frame", 1, 2, "M1", "S1")

    with pytest.raises(ValueError, match="already exists"):
        builder.rename_node(1, 2)
    with pytest.raises(ValueError, match="integer"):
        builder.rename_node(1, "N1")
    with pytest.raises(ValueError, match="required"):
        builder.rename_element("E1", " ")
