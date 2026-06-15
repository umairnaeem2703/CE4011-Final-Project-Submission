"""Internal helpers for constructing StructuralModel instances without XML."""

from __future__ import annotations

from collections.abc import Iterable
import xml.etree.ElementTree as ET

from parser import (
    Element,
    LoadCase,
    LumpedMass,
    Material,
    Node,
    NodalLoad,
    PointLoad,
    Section,
    StructuralModel,
    Support,
    TemperatureL,
    UniformlyDL,
)
from structural_validator import StructuralValidator


class ModelBuilder:
    """Build a StructuralModel through the existing parser dataclasses."""

    def __init__(self, model: StructuralModel | None = None, *, name: str | None = None, unit_system: str | None = None):
        self.model = model if model is not None else StructuralModel()
        if name is not None:
            self.model.name = name
            self._mark_dirty()
        if unit_system is not None:
            self.model.unit_system = unit_system
            self._mark_dirty()

    def add_material(self, id: str, E: float, alpha: float = 0.0, density: float = 0.0) -> Material:
        material = Material(id=id, E=E, alpha=alpha, density=density)
        self.model.materials[id] = material
        self._mark_dirty()
        return material

    def add_section(
        self,
        id: str,
        A: float,
        I: float = 0.0,
        d: float = 0.0,
        EA: float | None = None,
        EI: float | None = None,
    ) -> Section:
        section = Section(id=id, A=A, I=I, d=d, EA=EA, EI=EI)
        self.model.sections[id] = section
        self._mark_dirty()
        return section

    def add_node(self, id: int, x: float, y: float) -> Node:
        node = Node(id=id, x=x, y=y)
        self.model.nodes[id] = node
        self._mark_dirty()
        return node

    def add_element(
        self,
        id: str,
        type: str,
        node_i: int | Node,
        node_j: int | Node,
        material: str | Material,
        section: str | Section,
        release_start: bool = False,
        release_end: bool = False,
        is_axially_rigid: bool = False,
    ) -> Element:
        element = Element(
            id=id,
            type=type,
            node_i=self._node(node_i),
            node_j=self._node(node_j),
            material=self._material(material),
            section=self._section(section),
            release_start=release_start,
            release_end=release_end,
            is_axially_rigid=is_axially_rigid,
        )
        self.model.elements[id] = element
        self._mark_dirty()
        return element

    def add_support(
        self,
        node: int | Node,
        restrain_ux: bool = False,
        restrain_uy: bool = False,
        restrain_rz: bool = False,
        settlement_ux: float = 0.0,
        settlement_uy: float = 0.0,
        settlement_rz: float = 0.0,
    ) -> Support:
        node_ref = self._node(node)
        support = Support(
            node=node_ref,
            restrain_ux=restrain_ux,
            restrain_uy=restrain_uy,
            restrain_rz=restrain_rz,
            settlement_ux=settlement_ux,
            settlement_uy=settlement_uy,
            settlement_rz=settlement_rz,
        )
        self.model.supports[node_ref.id] = support
        self._mark_dirty()
        return support

    def add_nodal_load(
        self,
        load_case: str,
        node: int | Node,
        fx: float = 0.0,
        fy: float = 0.0,
        mz: float = 0.0,
        *,
        load_case_name: str = "",
    ) -> NodalLoad:
        nodal_load = NodalLoad(node=self._node(node), fx=fx, fy=fy, mz=mz)
        self._load_case(load_case, load_case_name).loads.append(nodal_load)
        self._mark_dirty()
        return nodal_load

    def add_member_udl(
        self,
        load_case: str,
        element: str | Element,
        wx: float = 0.0,
        wy: float = 0.0,
        *,
        load_case_name: str = "",
    ) -> UniformlyDL:
        udl = UniformlyDL(element=self._element(element), wx=wx, wy=wy)
        self._load_case(load_case, load_case_name).loads.append(udl)
        self._mark_dirty()
        return udl

    def add_member_point_load(
        self,
        load_case: str,
        element: str | Element,
        position: float,
        fx: float = 0.0,
        fy: float = 0.0,
        *,
        load_case_name: str = "",
    ) -> PointLoad:
        point_load = PointLoad(element=self._element(element), position=position, fx=fx, fy=fy)
        self._load_case(load_case, load_case_name).loads.append(point_load)
        self._mark_dirty()
        return point_load

    def add_temperature_load(
        self,
        load_case: str,
        element: str | Element,
        Tu: float,
        Tb: float,
        *,
        load_case_name: str = "",
    ) -> TemperatureL:
        temperature_load = TemperatureL(element=self._element(element), Tu=Tu, Tb=Tb)
        self._load_case(load_case, load_case_name).loads.append(temperature_load)
        self._mark_dirty()
        return temperature_load

    def add_lumped_mass(
        self,
        node: int | Node,
        mass_ux: float = 0.0,
        mass_uy: float = 0.0,
        inertia_rz: float = 0.0,
    ) -> LumpedMass:
        node_ref = self._node(node)
        mass = LumpedMass(node=node_ref, mass_ux=mass_ux, mass_uy=mass_uy, inertia_rz=inertia_rz)
        self.model.lumped_masses[node_ref.id] = mass
        self._mark_dirty()
        return mass

    def add_diaphragm_group(self, id: str, node_ids: Iterable[int | Node]) -> list[int]:
        group = [self._node(node).id for node in node_ids]
        self.model.diaphragm_ux_groups[id] = group
        self._mark_dirty()
        return group

    def build(self, validate: bool = False) -> StructuralModel:
        if validate:
            StructuralValidator(self.model).validate()
        return self.model

    def export_xml(self, filepath: str) -> None:
        export_model_to_xml(self.model, filepath)

    def _load_case(self, id: str, name: str = "") -> LoadCase:
        if id not in self.model.load_cases:
            self.model.load_cases[id] = LoadCase(id=id, name=name)
        elif name:
            self.model.load_cases[id].name = name
        return self.model.load_cases[id]

    def _node(self, node: int | Node) -> Node:
        if isinstance(node, Node):
            return node
        try:
            return self.model.nodes[node]
        except KeyError as exc:
            raise KeyError(f"Unknown node id {node!r}.") from exc

    def _element(self, element: str | Element) -> Element:
        if isinstance(element, Element):
            return element
        try:
            return self.model.elements[element]
        except KeyError as exc:
            raise KeyError(f"Unknown element id {element!r}.") from exc

    def _material(self, material: str | Material) -> Material:
        if isinstance(material, Material):
            return material
        try:
            return self.model.materials[material]
        except KeyError as exc:
            raise KeyError(f"Unknown material id {material!r}.") from exc

    def _section(self, section: str | Section) -> Section:
        if isinstance(section, Section):
            return section
        try:
            return self.model.sections[section]
        except KeyError as exc:
            raise KeyError(f"Unknown section id {section!r}.") from exc

    def _mark_dirty(self) -> None:
        if hasattr(self.model, "mark_dirty"):
            self.model.mark_dirty()


def export_model_to_xml(model: StructuralModel, filepath: str) -> None:
    """Write a StructuralModel using the XMLParser-compatible schema."""
    root = ET.Element("structural_model", {"name": model.name, "unit_system": model.unit_system})

    materials_el = ET.SubElement(root, "materials")
    for material in model.materials.values():
        ET.SubElement(
            materials_el,
            "material",
            {
                "id": material.id,
                "E": _fmt(material.E),
                "alpha": _fmt(material.alpha),
                "density": _fmt(material.density),
            },
        )

    sections_el = ET.SubElement(root, "sections")
    for section in model.sections.values():
        attrs = {"id": section.id, "A": _fmt(section.A), "I": _fmt(section.I), "d": _fmt(section.d)}
        if section.EA is not None:
            attrs["EA"] = _fmt(section.EA)
        if section.EI is not None:
            attrs["EI"] = _fmt(section.EI)
        ET.SubElement(
            sections_el,
            "section",
            attrs,
        )

    nodes_el = ET.SubElement(root, "nodes")
    for node in model.nodes.values():
        ET.SubElement(nodes_el, "node", {"id": str(node.id), "x": _fmt(node.x), "y": _fmt(node.y)})

    if model.lumped_masses:
        lumped_masses_el = ET.SubElement(root, "lumped_masses")
        for node_id, mass in model.lumped_masses.items():
            if isinstance(mass, (int, float)):
                attrs = {
                    "node": str(node_id),
                    "mass_ux": _fmt(float(mass)),
                    "mass_uy": _fmt(float(mass)),
                    "inertia_rz": _fmt(0.0),
                }
            else:
                attrs = {
                    "node": str(mass.node.id),
                    "mass_ux": _fmt(mass.mass_ux),
                    "mass_uy": _fmt(mass.mass_uy),
                    "inertia_rz": _fmt(mass.inertia_rz),
                }
            ET.SubElement(lumped_masses_el, "lumped_mass", attrs)

    elements_el = ET.SubElement(root, "elements")
    for element in model.elements.values():
        element_el = ET.SubElement(
            elements_el,
            element.type,
            {
                "id": element.id,
                "node_i": str(element.node_i.id),
                "node_j": str(element.node_j.id),
                "material": element.material.id,
                "section": element.section.id,
            },
        )
        if element.is_axially_rigid:
            element_el.set("is_axially_rigid", "true")
        if element.release_start or element.release_end:
            releases_el = ET.SubElement(element_el, "releases")
            if element.release_start:
                ET.SubElement(releases_el, "release", {"end": "i", "dof": "Mz"})
            if element.release_end:
                ET.SubElement(releases_el, "release", {"end": "j", "dof": "Mz"})

    if model.diaphragm_ux_groups:
        diaphragms_el = ET.SubElement(root, "diaphragms")
        for group_id, node_ids in model.diaphragm_ux_groups.items():
            ET.SubElement(
                diaphragms_el,
                "diaphragm",
                {"id": group_id, "nodes": ",".join(str(node_id) for node_id in node_ids)},
            )

    boundaries_el = ET.SubElement(root, "boundary_conditions")
    for support in model.supports.values():
        attrs = {
            "node": str(support.node.id),
            "ux": _bool_int(support.restrain_ux),
            "uy": _bool_int(support.restrain_uy),
            "rz": _bool_int(support.restrain_rz),
        }
        if support.settlement_ux:
            attrs["settlement_ux"] = _fmt(support.settlement_ux)
        if support.settlement_uy:
            attrs["settlement_uy"] = _fmt(support.settlement_uy)
        if support.settlement_rz:
            attrs["settlement_rz"] = _fmt(support.settlement_rz)
        ET.SubElement(boundaries_el, "support", attrs)

    if model.load_cases:
        load_cases_el = ET.SubElement(root, "load_cases")
        for load_case in model.load_cases.values():
            lc_attrs = {"id": load_case.id}
            if load_case.name:
                lc_attrs["name"] = load_case.name
            lc_el = ET.SubElement(load_cases_el, "load_case", lc_attrs)
            for load in load_case.loads:
                if isinstance(load, NodalLoad):
                    ET.SubElement(
                        lc_el,
                        "point_load",
                        {
                            "node": str(load.node.id),
                            "fx": _fmt(load.fx),
                            "fy": _fmt(load.fy),
                            "mz": _fmt(load.mz),
                        },
                    )
                elif isinstance(load, UniformlyDL):
                    ET.SubElement(
                        lc_el,
                        "member_udl",
                        {"element": load.element.id, "wx": _fmt(load.wx), "wy": _fmt(load.wy)},
                    )
                elif isinstance(load, PointLoad):
                    ET.SubElement(
                        lc_el,
                        "member_point_load",
                        {
                            "element": load.element.id,
                            "position": _fmt(load.position),
                            "fx": _fmt(load.fx),
                            "fy": _fmt(load.fy),
                        },
                    )
                elif isinstance(load, TemperatureL):
                    _append_temperature_load(lc_el, load)

    ET.indent(root)
    ET.ElementTree(root).write(filepath, encoding="utf-8", xml_declaration=True)


def _append_temperature_load(parent: ET.Element, load: TemperatureL) -> None:
    attrs = {"element": load.element.id}
    if load.Tu == load.Tb:
        attrs.update({"type": "uniform", "delta_T": _fmt(load.Tu)})
    else:
        attrs.update({"type": "combined", "T_top": _fmt(load.Tu), "T_bottom": _fmt(load.Tb)})
    ET.SubElement(parent, "temperature_load", attrs)


def _bool_int(value: bool) -> str:
    return "1" if value else "0"


def _fmt(value: float) -> str:
    return format(value, ".12g")

