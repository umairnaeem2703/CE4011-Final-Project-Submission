"""Model input adapters for Streamlit forms and uploaded files."""

from __future__ import annotations

import csv
import os
import tempfile
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import dataclass
from io import StringIO
from typing import Any

from parser import (
    Element,
    LoadCase,
    LumpedMass,
    Material,
    Node,
    NodalLoad,
    Section,
    StructuralModel,
    Support,
    XMLParser,
)


@dataclass
class ModelInputResult:
    """User-facing outcome for model input operations."""

    model: StructuralModel | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.model is not None


def build_model_from_xml_upload(uploaded_file: Any) -> ModelInputResult:
    """Parse an uploaded XML file into a StructuralModel."""
    try:
        raw = uploaded_file.read() if hasattr(uploaded_file, "read") else uploaded_file
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if not raw:
            return ModelInputResult(None, "XML upload is empty.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as handle:
            handle.write(raw)
            temp_path = handle.name

        try:
            model = XMLParser(temp_path).parse()
        finally:
            os.unlink(temp_path)

        _validate_model(model)
        model.mark_dirty()
        return ModelInputResult(model)
    except Exception as exc:  # pragma: no cover - exercised through message shape
        return ModelInputResult(None, f"Could not build model from XML: {exc}")


def build_model_from_tables(
    *,
    nodes: Any,
    elements: Any,
    materials: Any,
    sections: Any,
    supports: Any | None = None,
    loads: Any | None = None,
    masses: Any | None = None,
    name: str = "Table Input Model",
) -> ModelInputResult:
    """Build a StructuralModel from spreadsheet-style rows or CSV text."""
    try:
        model = StructuralModel(name=name)
        for row in _rows(materials):
            material_id = _text(row, "id", required=True)
            model.materials[material_id] = Material(
                id=material_id,
                E=_number(row, "E", required=True),
                alpha=_number(row, "alpha", default=0.0),
                density=_number(row, "density", "rho", default=0.0),
            )

        for row in _rows(sections):
            section_id = _text(row, "id", required=True)
            model.sections[section_id] = Section(
                id=section_id,
                A=_number(row, "A", required=True),
                I=_number(row, "I", default=0.0),
                d=_number(row, "d", default=0.0),
            )

        for row in _rows(nodes):
            node_id = _integer(row, "id", required=True)
            model.nodes[node_id] = Node(
                id=node_id,
                x=_number(row, "x", required=True),
                y=_number(row, "y", required=True),
            )

        for row in _rows(elements):
            element_id = _text(row, "id", required=True)
            node_i_id = _integer(row, "node_i", required=True)
            node_j_id = _integer(row, "node_j", required=True)
            material_id = _text(row, "material", required=True)
            section_id = _text(row, "section", required=True)
            node_i = _required_lookup(model.nodes, node_i_id, f"Element {element_id} references missing node {node_i_id}.")
            node_j = _required_lookup(model.nodes, node_j_id, f"Element {element_id} references missing node {node_j_id}.")
            material = _required_lookup(
                model.materials,
                material_id,
                f"Element {element_id} references missing material '{material_id}'.",
            )
            section = _required_lookup(
                model.sections,
                section_id,
                f"Element {element_id} references missing section '{section_id}'.",
            )
            model.elements[element_id] = Element(
                id=element_id,
                type=_text(row, "type", default="frame").lower(),
                node_i=node_i,
                node_j=node_j,
                material=material,
                section=section,
                release_start=_boolean(row, "release_start", default=False),
                release_end=_boolean(row, "release_end", default=False),
                is_axially_rigid=_boolean(row, "is_axially_rigid", default=False),
            )

        for row in _rows(supports):
            node_id = _integer(row, "node", "node_id", required=True)
            node = _required_lookup(model.nodes, node_id, f"Support references missing node {node_id}.")
            support_type = _text(row, "type", default="").lower()
            ux, uy, rz = _support_restraints(row, support_type)
            model.supports[node.id] = Support(
                node=node,
                restrain_ux=ux,
                restrain_uy=uy,
                restrain_rz=rz,
                settlement_ux=_number(row, "settlement_ux", default=0.0),
                settlement_uy=_number(row, "settlement_uy", default=0.0),
                settlement_rz=_number(row, "settlement_rz", default=0.0),
            )

        for row in _rows(loads):
            load_case_id = _text(row, "load_case", "case", default="LC1")
            load_case = model.load_cases.setdefault(load_case_id, LoadCase(id=load_case_id, name=load_case_id))
            load_type = _text(row, "type", default="nodal").lower()
            if load_type not in {"nodal", "point"}:
                raise ValueError("Table input currently supports nodal loads only.")
            node_id = _integer(row, "node", "node_id", required=True)
            node = _required_lookup(model.nodes, node_id, f"Load references missing node {node_id}.")
            load_case.loads.append(
                NodalLoad(
                    node=node,
                    fx=_number(row, "fx", default=0.0),
                    fy=_number(row, "fy", default=0.0),
                    mz=_number(row, "mz", default=0.0),
                )
            )

        for row in _rows(masses):
            node_id = _integer(row, "node", "node_id", required=True)
            node = _required_lookup(model.nodes, node_id, f"Mass references missing node {node_id}.")
            model.lumped_masses[node.id] = LumpedMass(
                node=node,
                mass_ux=_number(row, "mass_ux", "mx", default=0.0),
                mass_uy=_number(row, "mass_uy", "my", default=0.0),
                inertia_rz=_number(row, "inertia_rz", "mrz", default=0.0),
            )

        _validate_model(model)
        model.mark_dirty()
        return ModelInputResult(model)
    except Exception as exc:
        return ModelInputResult(None, f"Could not build model from table input: {exc}")


def store_model_in_state(session_state: MutableMapping[str, object], model: StructuralModel) -> None:
    """Store the active model and mark analysis results stale."""
    model.mark_dirty()
    session_state["model"] = model
    session_state["model_is_dirty"] = True
    session_state["static_results"] = None
    session_state["modal_results"] = None
    session_state["rsa_results"] = None
    session_state["tha_results"] = None


def mark_model_dirty(session_state: MutableMapping[str, object]) -> None:
    """Mark the current UI model dirty after input edits."""
    model = session_state.get("model")
    if hasattr(model, "mark_dirty"):
        model.mark_dirty()
    session_state["model_is_dirty"] = True


def _validate_model(model: StructuralModel) -> None:
    if not model.nodes:
        raise ValueError("At least one node is required.")
    if not model.elements:
        raise ValueError("At least one element is required.")

    for element in model.elements.values():
        if element.node_i.id not in model.nodes or element.node_j.id not in model.nodes:
            raise ValueError(f"Element {element.id} references a missing node.")
        if element.node_i.id == element.node_j.id:
            raise ValueError(f"Element {element.id} has invalid connectivity.")
        dx = element.node_j.x - element.node_i.x
        dy = element.node_j.y - element.node_i.y
        if (dx * dx + dy * dy) ** 0.5 == 0.0:
            raise ValueError(f"Element {element.id} has zero length.")
        if element.material.id not in model.materials:
            raise ValueError(f"Element {element.id} references a missing material.")
        if element.section.id not in model.sections:
            raise ValueError(f"Element {element.id} references a missing section.")
        if element.type not in {"frame", "truss"}:
            raise ValueError(f"Element {element.id} has unsupported type '{element.type}'.")

    for node_id, support in model.supports.items():
        if node_id not in model.nodes or support.node.id not in model.nodes:
            raise ValueError(f"Support references missing node {node_id}.")
        restraints = (support.restrain_ux, support.restrain_uy, support.restrain_rz)
        if not all(isinstance(value, bool) for value in restraints):
            raise ValueError(f"Support at node {node_id} has invalid restraints.")


def _rows(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return [dict(row) for row in csv.DictReader(StringIO(text))]
    if isinstance(value, Mapping):
        return [dict(value)]
    if isinstance(value, Iterable):
        return [dict(row) for row in value if row]
    return []


def _field(row: Mapping[str, Any], *names: str, required: bool = False, default: Any = None) -> Any:
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for name in names:
        value = normalized.get(name.lower())
        if value not in (None, ""):
            return value
    if required:
        raise ValueError(f"Missing required field '{names[0]}'.")
    return default


def _required_lookup(values: Mapping[Any, Any], key: Any, message: str) -> Any:
    if key not in values:
        raise ValueError(message)
    return values[key]


def _text(row: Mapping[str, Any], *names: str, required: bool = False, default: str = "") -> str:
    value = _field(row, *names, required=required, default=default)
    return str(value).strip()


def _number(row: Mapping[str, Any], *names: str, required: bool = False, default: float = 0.0) -> float:
    return float(_field(row, *names, required=required, default=default))


def _integer(row: Mapping[str, Any], *names: str, required: bool = False, default: int = 0) -> int:
    return int(float(_field(row, *names, required=required, default=default)))


def _boolean(row: Mapping[str, Any], *names: str, default: bool = False) -> bool:
    value = _field(row, *names, default=default)
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "fixed"}:
        return True
    if normalized in {"0", "false", "no", "n", "free"}:
        return False
    raise ValueError(f"Invalid boolean restraint value '{value}'.")


def _support_restraints(row: Mapping[str, Any], support_type: str) -> tuple[bool, bool, bool]:
    if support_type == "fixed":
        return True, True, True
    if support_type == "pin":
        return True, True, False
    if support_type == "roller_x":
        return False, True, False
    if support_type == "roller_y":
        return True, False, False
    if support_type and support_type not in {"custom", "restraints"}:
        raise ValueError(f"Invalid support type '{support_type}'.")
    return (
        _boolean(row, "ux", "restrain_ux", default=False),
        _boolean(row, "uy", "restrain_uy", default=False),
        _boolean(row, "rz", "restrain_rz", default=False),
    )
