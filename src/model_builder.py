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

    def add_material(
        self,
        id: str,
        E: float,
        alpha: float = 0.0,
        density: float = 0.0,
        type: str = "Generic",
    ) -> Material:
        material = Material(id=id, E=E, alpha=alpha, density=density, type=type)
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
        shape: str = "Generic",
        material_id: str = "",
        depth: float | None = None,
        width: float | None = None,
        outside_diameter: float | None = None,
        wall_thickness: float | None = None,
    ) -> Section:
        section = Section(
            id=id,
            A=A,
            I=I,
            d=d,
            EA=EA,
            EI=EI,
            shape=shape,
            material_id=material_id,
            depth=depth,
            width=width,
            outside_diameter=outside_diameter,
            wall_thickness=wall_thickness,
        )
        self.model.sections[id] = section
        self._mark_dirty()
        return section

    def add_node(self, id: int, x: float, y: float, is_hinged: bool = False) -> Node:
        node = Node(id=id, x=x, y=y, is_hinged=is_hinged)
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
        coord_system: str = "local",
        direction: str = "",
        value: float | None = None,
        load_case_name: str = "",
    ) -> UniformlyDL:
        udl = UniformlyDL(
            element=self._element(element),
            wx=wx,
            wy=wy,
            coord_system=coord_system,
            direction=direction,
            value=value,
        )
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
        coord_system: str = "local",
        direction: str = "",
        value: float | None = None,
        load_case_name: str = "",
    ) -> PointLoad:
        point_load = PointLoad(
            element=self._element(element),
            position=position,
            fx=fx,
            fy=fy,
            coord_system=coord_system,
            direction=direction,
            value=value,
        )
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

    def rename_node(self, old_id: int, new_id: int) -> Node:
        if not isinstance(new_id, int) or isinstance(new_id, bool):
            raise ValueError("Node id must be an integer.")
        if old_id not in self.model.nodes:
            raise KeyError(f"Unknown node id {old_id!r}.")
        if old_id == new_id:
            return self.model.nodes[old_id]
        if new_id in self.model.nodes:
            raise ValueError(f"Node id {new_id!r} already exists.")

        node = self.model.nodes.pop(old_id)
        node.id = new_id
        self.model.nodes[new_id] = node

        support = self.model.supports.pop(old_id, None)
        if support is not None:
            self.model.supports[new_id] = support

        mass = self.model.lumped_masses.pop(old_id, None)
        if mass is not None:
            if hasattr(mass, "node"):
                mass.node = node
            self.model.lumped_masses[new_id] = mass

        for group_id, node_ids in list(self.model.diaphragm_ux_groups.items()):
            self.model.diaphragm_ux_groups[group_id] = [
                new_id if node_id == old_id else node_id for node_id in node_ids
            ]

        self._mark_dirty()
        return node

    def rename_element(self, old_id: str, new_id: str) -> Element:
        new_id = str(new_id).strip()
        if not new_id:
            raise ValueError("Member id is required.")
        if old_id not in self.model.elements:
            raise KeyError(f"Unknown element id {old_id!r}.")
        if old_id == new_id:
            return self.model.elements[old_id]
        if new_id in self.model.elements:
            raise ValueError(f"Member id {new_id!r} already exists.")

        element = self.model.elements.pop(old_id)
        element.id = new_id
        self.model.elements[new_id] = element
        self._mark_dirty()
        return element

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
    root = ET.Element("model", {"name": model.name, "unit_system": model.unit_system})

    materials_el = ET.SubElement(root, "materials")
    for material in sorted(model.materials.values(), key=lambda item: item.id):
        ET.SubElement(
            materials_el,
            "material",
            {
                "id": material.id,
                "E": _fmt(material.E),
                "alpha": _fmt(material.alpha),
                "density": _fmt(material.density),
                "type": getattr(material, "type", "Generic"),
            },
        )

    sections_el = ET.SubElement(root, "sections")
    for section in sorted(model.sections.values(), key=lambda item: item.id):
        attrs = {"id": section.id, "A": _fmt(section.A), "I": _fmt(section.I), "d": _fmt(section.d)}
        for attr_name in (
            "shape",
            "material_id",
            "depth",
            "width",
            "outside_diameter",
            "wall_thickness",
        ):
            value = getattr(section, attr_name, None)
            if value not in (None, ""):
                attrs[attr_name] = _fmt(value) if isinstance(value, (int, float)) else str(value)
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
    for node in sorted(model.nodes.values(), key=lambda item: item.id):
        attrs = {"id": str(node.id), "x": _fmt(node.x), "y": _fmt(node.y)}
        if getattr(node, "is_hinged", False):
            attrs["is_hinged"] = "true"
        ET.SubElement(nodes_el, "node", attrs)

    if model.lumped_masses:
        lumped_masses_el = ET.SubElement(root, "lumped_masses")
        for node_id, mass in sorted(model.lumped_masses.items(), key=lambda item: item[0]):
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
    for element in sorted(model.elements.values(), key=lambda item: item.id):
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
        for group_id, node_ids in sorted(model.diaphragm_ux_groups.items(), key=lambda item: item[0]):
            ET.SubElement(
                diaphragms_el,
                "diaphragm",
                {"id": group_id, "nodes": ",".join(str(node_id) for node_id in node_ids)},
            )

    boundaries_el = ET.SubElement(root, "boundary_conditions")
    for support in sorted(model.supports.values(), key=lambda item: item.node.id):
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
        for load_case in sorted(model.load_cases.values(), key=lambda item: item.id):
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
                    attrs = {"element": load.element.id, "wx": _fmt(load.wx), "wy": _fmt(load.wy)}
                    _append_member_load_metadata(attrs, load)
                    ET.SubElement(
                        lc_el,
                        "member_udl",
                        attrs,
                    )
                elif isinstance(load, PointLoad):
                    attrs = {
                        "element": load.element.id,
                        "position": _fmt(load.position),
                        "fx": _fmt(load.fx),
                        "fy": _fmt(load.fy),
                    }
                    _append_member_load_metadata(attrs, load)
                    ET.SubElement(
                        lc_el,
                        "member_point_load",
                        attrs,
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


def _append_member_load_metadata(attrs: dict[str, str], load: UniformlyDL | PointLoad) -> None:
    coord_system = getattr(load, "coord_system", "local")
    direction = getattr(load, "direction", "")
    value = getattr(load, "value", None)
    if coord_system != "local":
        attrs["coord_system"] = coord_system
    if direction:
        attrs["direction"] = direction
    if value is not None:
        attrs["value"] = _fmt(value)


def _bool_int(value: bool) -> str:
    return "1" if value else "0"


def _fmt(value: float) -> str:
    return format(value, ".12g")

