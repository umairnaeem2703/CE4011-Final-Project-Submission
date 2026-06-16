"""Canvas geometry editor backed by ModelBuilder."""

from __future__ import annotations

import math
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
from typing import Callable

from .dialogs import LoadSettings, SupportSettings


StatusCallback = Callable[[str], None]
SelectionCallback = Callable[[str | None, object | None], None]
ChangeCallback = Callable[[], None]


def _load_model_builder():
    try:
        from src.model_builder import ModelBuilder
    except ModuleNotFoundError:
        src_dir = Path(__file__).resolve().parents[1]
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        from model_builder import ModelBuilder

    return ModelBuilder


class ModelCanvas(ttk.Frame):
    """Simple 2D geometry canvas with ModelBuilder-backed creation."""

    def __init__(
        self,
        parent,
        *,
        status_callback: StatusCallback | None = None,
        selection_callback: SelectionCallback | None = None,
        change_callback: ChangeCallback | None = None,
    ) -> None:
        super().__init__(parent, padding=4)
        self.status_callback = status_callback or (lambda message: None)
        self.selection_callback = selection_callback or (lambda kind, obj: None)
        self.change_callback = change_callback or (lambda: None)

        ModelBuilder = _load_model_builder()
        self.builder = ModelBuilder(name="Desktop Model")
        self._ensure_placeholder_properties()

        self.active_command = "Select / Inspect"
        self.active_element_type = "frame"
        self.active_material_id = "M1"
        self.active_section_id = "S1"
        self.support_settings = SupportSettings()
        self.load_settings = LoadSettings()
        self.support_action = "Replace"
        self.load_action = "Add"
        self.mass_action = "Replace"
        self.mass_settings = (0.0, 0.0, 0.0)
        self.diaphragm_action = "Replace"
        self.diaphragm_group_id = "D1"
        self.diaphragm_node_ids: list[int] = []
        self.draw_mode = "click"

        self.scale = 40.0
        self.view_scale = self.scale
        self.view_origin_x = 0.0
        self.view_origin_y = 0.0
        self.grid_spacing = 40
        self.snap_tolerance = 12.0
        self.node_radius = 5
        self.next_node_id = 1
        self.next_element_number = 1
        self.pending_start_node_id: int | None = None
        self.selected_kind: str | None = None
        self.selected_id: int | str | None = None

        self.item_to_node_id: dict[int, int] = {}
        self.node_id_to_item: dict[int, int] = {}
        self.item_to_element_id: dict[int, str] = {}
        self.element_id_to_item: dict[str, int] = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, background="white", highlightthickness=1, highlightbackground="#b8b8b8")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda event: self.redraw_model())
        self.canvas.bind("<Button-1>", self._handle_click)

    def load_builder(self, builder) -> None:
        self.builder = builder
        self.pending_start_node_id = None
        self.clear_selection(notify=False)

        node_ids = [int(node_id) for node_id in self.builder.model.nodes]
        element_numbers = [_element_number(element_id) for element_id in self.builder.model.elements]
        self.next_node_id = max(node_ids, default=0) + 1
        self.next_element_number = max(element_numbers, default=0) + 1

        first_material = next(iter(self.builder.model.materials), None)
        first_section = next(iter(self.builder.model.sections), None)
        if first_material is not None:
            self.active_material_id = first_material
        if first_section is not None:
            self.active_section_id = first_section

        self.redraw_model()
        self.change_callback()
        self.status_callback(
            f"Loaded model with {len(self.builder.model.nodes)} nodes and {len(self.builder.model.elements)} elements."
        )

    def redraw_model(self) -> None:
        """Reload canvas items from the current builder model."""
        self.canvas.delete("all")
        self.item_to_node_id.clear()
        self.node_id_to_item.clear()
        self.item_to_element_id.clear()
        self.element_id_to_item.clear()
        self._fit_view_to_model()
        self._draw_grid()

        for element_id, element in self.builder.model.elements.items():
            self._draw_element(element_id, element.node_i.id, element.node_j.id, element_type=element.type)
        for node_id, node in self.builder.model.nodes.items():
            self._draw_node(node_id, node.x, node.y)
        self._draw_model_symbols()
        self._apply_selection_highlight()

    def refresh_canvas(self) -> None:
        self.redraw_model()

    def set_active_command(self, command: str) -> None:
        self.active_command = command
        if command != "Draw Member":
            self.pending_start_node_id = None
        self.status_callback(self.command_instruction())

    def command_instruction(self) -> str:
        if self.active_command == "Draw Node":
            return "Draw Node: click canvas or enter x/y, then Add Node."
        if self.active_command == "Draw Member":
            if self.pending_start_node_id is None:
                return "Draw Member: select start node."
            return "Draw Member: select end node or enter length/angle."
        if self.active_command == "Materials / Sections":
            return "Materials / Sections: define reusable material and section properties."
        if self.active_command == "Assign Load":
            return "Assign Load: choose load settings, then click target."
        if self.active_command == "Assign Support":
            return "Assign Support: choose support settings, then click node."
        if self.active_command == "Assign Mass":
            return "Assign Mass: choose mass settings, then click node."
        if self.active_command == "Assign Diaphragm":
            return "Assign Diaphragm: click nodes to collect them, then apply the diaphragm."
        if self.active_command == "Delete":
            return "Delete: click a node or member to remove it."
        return "Select / Inspect: click a node or member to inspect it."

    def set_active_element_type(self, element_type: str) -> None:
        self.active_element_type = element_type

    def set_active_material(self, material_id: str) -> None:
        self.active_material_id = material_id

    def set_active_section(self, section_id: str) -> None:
        self.active_section_id = section_id

    def set_draw_mode(self, draw_mode: str) -> None:
        self.draw_mode = draw_mode

    def set_support_settings(self, settings: SupportSettings) -> None:
        self.support_settings = settings

    def set_support_action(self, action: str) -> None:
        self.support_action = action

    def set_load_settings(self, settings: LoadSettings) -> None:
        self.load_settings = settings

    def set_load_action(self, action: str) -> None:
        self.load_action = action

    def set_mass_settings(self, action: str, mass_ux: float, mass_uy: float, inertia_rz: float) -> None:
        self.mass_action = action
        self.mass_settings = (mass_ux, mass_uy, inertia_rz)

    def set_diaphragm_settings(self, action: str, group_id: str, node_ids: list[int]) -> None:
        self.diaphragm_action = action
        self.diaphragm_group_id = group_id
        self.diaphragm_node_ids = list(dict.fromkeys(node_ids))

    def add_node_by_coordinates(self, x: float, y: float) -> int:
        existing_node_id = self._find_node_near_model_point(x, y)
        if existing_node_id is not None:
            self.select_node(existing_node_id)
            return existing_node_id

        node_id = self.next_node_id
        self.next_node_id += 1
        self.builder.add_node(node_id, x, y)
        self.redraw_model()
        self.select_node(node_id)
        self.change_callback()
        self.status_callback(f"Added node {node_id} at ({x:.3g}, {y:.3g}).")
        return node_id

    def draw_member_by_length_angle(self, length: float, angle_degrees: float) -> str | None:
        if self.pending_start_node_id is None:
            self.status_callback("Draw Member: select start node.")
            return None

        start_node_id = self.pending_start_node_id
        start_node = self.builder.model.nodes[start_node_id]
        angle_radians = math.radians(angle_degrees)
        end_x = start_node.x + length * math.cos(angle_radians)
        end_y = start_node.y + length * math.sin(angle_radians)
        end_node_id = self.add_node_by_coordinates(end_x, end_y)
        return self._create_element(start_node_id, end_node_id)

    def select_node(self, node_id: int) -> None:
        self.selected_kind = "node"
        self.selected_id = node_id
        self._apply_selection_highlight()
        self.selection_callback("node", self.builder.model.nodes.get(node_id))

    def select_element(self, element_id: str) -> None:
        self.selected_kind = "element"
        self.selected_id = element_id
        self._apply_selection_highlight()
        self.selection_callback("element", self.builder.model.elements.get(element_id))

    def clear_selection(self, *, notify: bool = True) -> None:
        self.selected_kind = None
        self.selected_id = None
        if notify:
            self.selection_callback(None, None)

    def _ensure_placeholder_properties(self) -> None:
        self.builder.add_material("M1", E=1.0)
        self.builder.add_section("S1", A=1.0, I=1.0)

    def _handle_click(self, event) -> None:
        node_id = self._find_node_near_canvas_point(event.x, event.y)
        element_id = self._find_element_near_canvas_point(event.x, event.y) if node_id is None else None

        if self.active_command == "Draw Node":
            x, y = self._canvas_to_model(event.x, event.y)
            self.add_node_by_coordinates(x, y)
        elif self.active_command == "Draw Member":
            if node_id is None:
                x, y = self._canvas_to_model(event.x, event.y)
                node_id = self.add_node_by_coordinates(x, y)
            self._set_pending_or_create_element(node_id)
        elif self.active_command == "Delete":
            self._delete_target(node_id, element_id)
        elif self.active_command == "Assign Support":
            if node_id is None:
                self.status_callback("Assign Support: click a node.")
                return
            self.assign_support_to_node(node_id)
        elif self.active_command == "Assign Load":
            if self.load_settings.target == "Node":
                if node_id is None:
                    self.status_callback("Nodal Load: click a node.")
                    return
                self.assign_load_to_node(node_id)
            else:
                if element_id is None:
                    self.status_callback("Member Load: click a member.")
                    return
                self.assign_load_to_element(element_id)
        elif self.active_command == "Assign Mass":
            if node_id is None:
                self.status_callback("Assign Mass: click a node.")
                return
            self.assign_mass_to_node(node_id)
        elif self.active_command == "Assign Diaphragm":
            if node_id is None:
                self.status_callback("Assign Diaphragm: click a node.")
                return
            self.collect_diaphragm_node(node_id)
        elif node_id is not None:
            self.select_node(node_id)
            self.status_callback(f"Selected node {node_id}.")
        elif element_id is not None:
            self.select_element(element_id)
            self.status_callback(f"Selected member {element_id}.")
        else:
            self.clear_selection()
            self.status_callback(self.command_instruction())

    def _set_pending_or_create_element(self, node_id: int) -> None:
        if self.pending_start_node_id is None:
            self.pending_start_node_id = node_id
            self.select_node(node_id)
            self.status_callback("Draw Member: select end node or enter length/angle.")
            return

        if self.pending_start_node_id == node_id:
            self.status_callback(f"Draw Member: start node {node_id} remains selected.")
            return

        self._create_element(self.pending_start_node_id, node_id)

    def _create_element(self, start_node_id: int, end_node_id: int) -> str | None:
        if start_node_id == end_node_id:
            self.status_callback("Member needs two different nodes.")
            return None

        element_id = f"E{self.next_element_number}"
        self.next_element_number += 1
        self.builder.add_element(
            element_id,
            self.active_element_type,
            start_node_id,
            end_node_id,
            self.active_material_id,
            self.active_section_id,
        )
        self.pending_start_node_id = end_node_id
        self.refresh_canvas()
        self.select_element(element_id)
        self.change_callback()
        self.status_callback("Draw Member: select end node or enter length/angle.")
        return element_id

    def _delete_target(self, node_id: int | None, element_id: str | None) -> None:
        if element_id is not None:
            self.builder.model.elements.pop(element_id, None)
            self.clear_selection()
            self.refresh_canvas()
            self.change_callback()
            self.status_callback(f"Deleted member {element_id}.")
            return
        if node_id is not None:
            connected = [
                element_id
                for element_id, element in self.builder.model.elements.items()
                if element.node_i.id == node_id or element.node_j.id == node_id
            ]
            if connected:
                self.status_callback(f"Delete blocked: node {node_id} has connected members.")
                return
            self.builder.model.nodes.pop(node_id, None)
            self.builder.model.supports.pop(node_id, None)
            self.builder.model.lumped_masses.pop(node_id, None)
            for diaphragm_id, node_ids in list(self.builder.model.diaphragm_ux_groups.items()):
                self.builder.model.diaphragm_ux_groups[diaphragm_id] = [
                    existing_id for existing_id in node_ids if existing_id != node_id
                ]
                if not self.builder.model.diaphragm_ux_groups[diaphragm_id]:
                    self.builder.model.diaphragm_ux_groups.pop(diaphragm_id, None)
            self.clear_selection()
            self.redraw_model()
            self.change_callback()
            self.status_callback(f"Deleted node {node_id}.")
            return
        self.status_callback("Delete: click a node or member to remove it.")

    def assign_support_to_node(self, node_id: int) -> None:
        if node_id not in self.builder.model.nodes:
            self.status_callback("Assign Support: click a node.")
            return
        settings = self.support_settings
        if self.support_action == "Delete":
            self.builder.model.supports.pop(node_id, None)
            self._mark_model_dirty()
            message = f"Deleted support/settlement assignment from node {node_id}."
        else:
            restrain_ux = settings.restrain_ux
            restrain_uy = settings.restrain_uy
            restrain_rz = settings.restrain_rz
            settlement_ux = settings.settlement_ux
            settlement_uy = settings.settlement_uy
            settlement_rz = settings.settlement_rz
            if self.support_action == "Add":
                existing = self.builder.model.supports.get(node_id)
                if existing is not None:
                    restrain_ux = existing.restrain_ux or restrain_ux
                    restrain_uy = existing.restrain_uy or restrain_uy
                    restrain_rz = existing.restrain_rz or restrain_rz
                    settlement_ux += existing.settlement_ux
                    settlement_uy += existing.settlement_uy
                    settlement_rz += existing.settlement_rz
            self.builder.add_support(
                node_id,
                restrain_ux=restrain_ux,
                restrain_uy=restrain_uy,
                restrain_rz=restrain_rz,
                settlement_ux=settlement_ux,
                settlement_uy=settlement_uy,
                settlement_rz=settlement_rz,
            )
            message = f"Assigned {settings.support_type} support to node {node_id}."
        self.redraw_model()
        self.select_node(node_id)
        self.change_callback()
        self.status_callback(message)

    def assign_load_to_node(self, node_id: int) -> None:
        settings = self.load_settings
        action = self.load_action
        if action in ("Replace", "Delete"):
            self._remove_loads(settings.load_case, lambda load: getattr(getattr(load, "node", None), "id", None) == node_id)
        if action != "Delete":
            self.builder.add_nodal_load(
                settings.load_case,
                node_id,
                fx=settings.fx,
                fy=settings.fy,
                mz=settings.mz,
            )
        self.redraw_model()
        self.select_node(node_id)
        self.change_callback()
        verb = "Deleted" if action == "Delete" else "Assigned"
        self.status_callback(f"{verb} nodal load assignment for node {node_id}.")

    def assign_load_to_element(self, element_id: str) -> None:
        settings = self.load_settings
        action = self.load_action
        if element_id not in self.builder.model.elements:
            self.status_callback("Member Load: click a member.")
            return
        element = self.builder.model.elements[element_id]
        if action != "Delete" and settings.load_type == "Temperature":
            if settings.wx != settings.wy and element.section.d <= 0:
                self.status_callback("Temperature gradient requires section depth d. Set Thermal depth d in the section.")
                return
            if settings.wx != settings.wy and element.type == "truss":
                self.status_callback("Temperature load: truss members require Tu and Tb to match.")
                return
        if action in ("Replace", "Delete"):
            if settings.load_type == "Temperature":
                self._remove_loads(
                    settings.load_case,
                    lambda load: (
                        load.__class__.__name__ == "TemperatureL"
                        and getattr(getattr(load, "element", None), "id", None) == element_id
                    ),
                )
            else:
                self._remove_loads(
                    settings.load_case,
                    lambda load: getattr(getattr(load, "element", None), "id", None) == element_id,
                )
        if action == "Delete":
            label = "temperature load" if settings.load_type == "Temperature" else "load"
        elif settings.load_type == "UDL":
            self.builder.add_member_udl(
                settings.load_case,
                element_id,
                wx=settings.wx,
                wy=settings.wy,
            )
            label = "UDL"
        elif settings.load_type == "Temperature":
            self.builder.add_temperature_load(
                settings.load_case,
                element_id,
                Tu=settings.wx,
                Tb=settings.wy,
            )
            label = "temperature load"
        else:
            self.builder.add_member_point_load(
                settings.load_case,
                element_id,
                position=settings.position,
                fx=settings.fx,
                fy=settings.fy,
            )
            label = "point load"
        self.redraw_model()
        self.select_element(element_id)
        self.change_callback()
        verb = "Deleted" if action == "Delete" else "Assigned"
        self.status_callback(f"{verb} member {label} assignment for {element_id}.")

    def assign_mass_to_node(self, node_id: int) -> None:
        if node_id not in self.builder.model.nodes:
            self.status_callback("Assign Mass: click a node.")
            return

        action = self.mass_action
        if action == "Delete":
            self.builder.model.lumped_masses.pop(node_id, None)
            self._mark_model_dirty()
            message = f"Deleted nodal mass from node {node_id}."
        else:
            mass_ux, mass_uy, inertia_rz = self.mass_settings
            if action == "Add":
                existing_ux, existing_uy, existing_rz = self._existing_mass_components(node_id)
                mass_ux += existing_ux
                mass_uy += existing_uy
                inertia_rz += existing_rz
            self.builder.add_lumped_mass(node_id, mass_ux=mass_ux, mass_uy=mass_uy, inertia_rz=inertia_rz)
            message = f"Assigned nodal mass to node {node_id}."

        self.redraw_model()
        self.select_node(node_id)
        self.change_callback()
        self.status_callback(message)

    def collect_diaphragm_node(self, node_id: int) -> None:
        if node_id not in self.builder.model.nodes:
            self.status_callback("Assign Diaphragm: click a node.")
            return
        if node_id not in self.diaphragm_node_ids:
            self.diaphragm_node_ids.append(node_id)
        self.select_node(node_id)
        self.status_callback(
            f"Assign Diaphragm {self.diaphragm_group_id}: selected nodes {self._diaphragm_nodes_label()}."
        )

    def apply_diaphragm_assignment(self) -> list[int] | None:
        group_id = self.diaphragm_group_id.strip() or "D1"
        action = self.diaphragm_action
        if action == "Delete":
            removed = self.builder.model.diaphragm_ux_groups.pop(group_id, None)
            self._mark_model_dirty()
            self.redraw_model()
            self.clear_selection()
            self.change_callback()
            self.status_callback(f"Deleted diaphragm group {group_id}." if removed is not None else f"Diaphragm group {group_id} not found.")
            return []

        missing = [node_id for node_id in self.diaphragm_node_ids if node_id not in self.builder.model.nodes]
        if missing:
            self.status_callback(f"Assign Diaphragm: unknown node id {missing[0]}.")
            return None
        if len(self.diaphragm_node_ids) < 2:
            self.status_callback("Assign Diaphragm: select at least two nodes.")
            return None

        if action == "Add":
            existing = self.builder.model.diaphragm_ux_groups.get(group_id, [])
            node_ids = list(dict.fromkeys([*existing, *self.diaphragm_node_ids]))
        else:
            node_ids = list(dict.fromkeys(self.diaphragm_node_ids))
        self.builder.add_diaphragm_group(group_id, node_ids)
        self.diaphragm_node_ids = node_ids
        self.redraw_model()
        self.clear_selection()
        self.change_callback()
        self.status_callback(f"Assigned diaphragm group {group_id} to nodes {self._diaphragm_nodes_label()}.")
        return node_ids

    def update_selected_member_properties(self, element_type: str, material_id: str, section_id: str):
        if self.selected_kind != "element" or self.selected_id not in self.builder.model.elements:
            self.status_callback("Member Properties: select a member first.")
            return None
        if element_type not in ("frame", "truss"):
            self.status_callback("Member Properties: type must be frame or truss.")
            return None
        if material_id not in self.builder.model.materials:
            self.status_callback(f"Member Properties: unknown material {material_id}.")
            return None
        if section_id not in self.builder.model.sections:
            self.status_callback(f"Member Properties: unknown section {section_id}.")
            return None

        element_id = str(self.selected_id)
        section = self.builder.model.sections[section_id]
        if self._member_has_temperature_gradient_load(element_id):
            if element_type == "truss":
                self.status_callback("Member Properties blocked: temperature-gradient loads require a frame member.")
                return None
            if section.d <= 0:
                self.status_callback(
                    "Member Properties blocked: temperature-gradient loads require section depth d."
                )
                return None

        element = self.builder.model.elements[element_id]
        element.type = element_type
        element.material = self.builder.model.materials[material_id]
        element.section = section
        self._mark_model_dirty()
        self.redraw_model()
        self.select_element(element_id)
        self.change_callback()
        self.status_callback(f"Updated member {element_id} properties.")
        return element

    def _remove_loads(self, load_case_id: str, matches) -> int:
        load_case = self.builder.model.load_cases.get(load_case_id)
        if load_case is None:
            return 0
        kept_loads = [load for load in load_case.loads if not matches(load)]
        removed_count = len(load_case.loads) - len(kept_loads)
        if removed_count:
            load_case.loads = kept_loads
            self._mark_model_dirty()
        return removed_count

    def _existing_mass_components(self, node_id: int) -> tuple[float, float, float]:
        existing = self.builder.model.lumped_masses.get(node_id)
        if existing is None:
            return (0.0, 0.0, 0.0)
        if isinstance(existing, (int, float)):
            return (float(existing), float(existing), 0.0)
        return (existing.mass_ux, existing.mass_uy, existing.inertia_rz)

    def _mark_model_dirty(self) -> None:
        mark_dirty = getattr(self.builder.model, "mark_dirty", None)
        if mark_dirty is not None:
            mark_dirty()

    def _member_has_temperature_gradient_load(self, element_id: str) -> bool:
        for load_case in self.builder.model.load_cases.values():
            for load in load_case.loads:
                if load.__class__.__name__ != "TemperatureL":
                    continue
                if getattr(getattr(load, "element", None), "id", None) != element_id:
                    continue
                if load.Tu != load.Tb:
                    return True
        return False

    def _diaphragm_nodes_label(self) -> str:
        return ", ".join(str(node_id) for node_id in self.diaphragm_node_ids) or "none"

    def _draw_node(self, node_id: int, x: float, y: float) -> None:
        cx, cy = self._model_to_canvas(x, y)
        r = self.node_radius
        item_id = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill="#1f77b4", outline="")
        label_id = self.canvas.create_text(cx + 10, cy - 10, text=str(node_id), fill="#1f77b4", anchor="w")
        self.canvas.addtag_withtag("node", item_id)
        self.canvas.addtag_withtag("node-label", label_id)
        self.item_to_node_id[item_id] = node_id
        self.node_id_to_item[node_id] = item_id

    def _draw_element(self, element_id: str, start_node_id: int, end_node_id: int, *, element_type: str) -> None:
        start_node = self.builder.model.nodes[start_node_id]
        end_node = self.builder.model.nodes[end_node_id]
        x1, y1 = self._model_to_canvas(start_node.x, start_node.y)
        x2, y2 = self._model_to_canvas(end_node.x, end_node.y)
        color = "#333333" if element_type == "frame" else "#0a7f58"
        item_id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)
        self.canvas.tag_lower(item_id)
        self.item_to_element_id[item_id] = element_id
        self.element_id_to_item[element_id] = item_id

    def _draw_model_symbols(self) -> None:
        for support in self.builder.model.supports.values():
            self._draw_support_symbol(support)
        for node_id, mass in self.builder.model.lumped_masses.items():
            self._draw_mass_symbol(node_id, mass)
        for load_case in self.builder.model.load_cases.values():
            for load in load_case.loads:
                if hasattr(load, "node"):
                    self._draw_nodal_load_symbol(load)
                elif hasattr(load, "element"):
                    if load.__class__.__name__ == "PointLoad":
                        self._draw_member_point_load_symbol(load)
                    elif load.__class__.__name__ == "UniformlyDL":
                        self._draw_member_udl_symbol(load)
                    elif load.__class__.__name__ == "TemperatureL":
                        self._draw_member_temperature_symbol(load)
        for node_ids in self.builder.model.diaphragm_ux_groups.values():
            self._draw_diaphragm_symbol(node_ids)

    def _draw_support_symbol(self, support) -> None:
        x, y = self._model_to_canvas(support.node.x, support.node.y)
        if support.restrain_ux and support.restrain_uy and support.restrain_rz:
            self.canvas.create_rectangle(x - 10, y + 8, x + 10, y + 14, fill="#666666", outline="", tags="symbol")
        elif support.restrain_ux and support.restrain_uy:
            self.canvas.create_polygon(x, y + 7, x - 10, y + 18, x + 10, y + 18, fill="#777777", tags="symbol")
        else:
            self.canvas.create_oval(x - 9, y + 8, x + 9, y + 18, outline="#777777", tags="symbol")
        self._draw_settlement_symbol(x, y, support)

    def _draw_settlement_symbol(self, x: float, y: float, support) -> None:
        if support.settlement_ux:
            dx = 1 if support.settlement_ux > 0 else -1
            head_x, head_y = self._draw_vector_arrow(x + 12 * dx, y + 24, dx, 0, length=18, color="#c00000")
            self._draw_symbol_label(head_x + 4 * dx, head_y + 8, f"ux={_fmt_value(support.settlement_ux)}", "#c00000")
        if support.settlement_uy:
            dy = -1 if support.settlement_uy > 0 else 1
            head_x, head_y = self._draw_vector_arrow(x - 22, y + 12 * dy, 0, dy, length=18, color="#c00000")
            self._draw_symbol_label(head_x - 4, head_y + 6 * dy, f"uy={_fmt_value(support.settlement_uy)}", "#c00000")
        if support.settlement_rz:
            self._draw_curved_arrow(x, y, clockwise=support.settlement_rz < 0, color="#c00000", radius=15)
            self._draw_symbol_label(x + 18, y + 24, f"rz={_fmt_value(support.settlement_rz)}", "#c00000")

    def _draw_nodal_load_symbol(self, load) -> None:
        node = self.builder.model.nodes.get(load.node.id)
        if node is None:
            return
        x, y = self._model_to_canvas(node.x, node.y)
        if load.fx:
            dx = 1 if load.fx > 0 else -1
            head_x, head_y = self._draw_vector_arrow(x + 8 * dx, y + 12, dx, 0, length=22, color="#d62728")
            self._draw_symbol_label(head_x + 4 * dx, head_y + 9, f"Fx={_fmt_value(load.fx)}", "#d62728")
        if load.fy:
            dy = -1 if load.fy > 0 else 1
            head_x, head_y = self._draw_vector_arrow(x - 12, y + 8 * dy, 0, dy, length=22, color="#d62728")
            self._draw_symbol_label(head_x - 4, head_y + 6 * dy, f"Fy={_fmt_value(load.fy)}", "#d62728")
        if load.mz:
            self._draw_curved_arrow(x, y, clockwise=load.mz < 0, color="#d62728", radius=17)
            self._draw_symbol_label(x + 20, y + 18, f"Mz={_fmt_value(load.mz)}", "#d62728")

    def _draw_member_udl_symbol(self, load) -> None:
        element = self.builder.model.elements.get(load.element.id)
        if element is None:
            return
        x1, y1 = self._model_to_canvas(element.node_i.x, element.node_i.y)
        x2, y2 = self._model_to_canvas(element.node_j.x, element.node_j.y)
        direction = _unit_vector(load.wx, -load.wy)
        if direction is None:
            return
        dx, dy = direction
        start = _offset_point(x1, y1, dx, dy, -18)
        end = _offset_point(x2, y2, dx, dy, -18)
        self.canvas.create_line(start[0], start[1], end[0], end[1], fill="#ff7f0e", width=1, tags="symbol")
        for factor in (0.25, 0.5, 0.75):
            x = x1 + (x2 - x1) * factor
            y = y1 + (y2 - y1) * factor
            self._draw_vector_arrow(x - dx * 18, y - dy * 18, dx, dy, length=18, color="#ff7f0e")
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        self._draw_symbol_label(mid_x + 8, mid_y - 8, f"w=({_fmt_value(load.wx)}, {_fmt_value(load.wy)})", "#ff7f0e")

    def _draw_member_point_load_symbol(self, load) -> None:
        element = self.builder.model.elements.get(load.element.id)
        if element is None:
            return
        x1, y1 = self._model_to_canvas(element.node_i.x, element.node_i.y)
        x2, y2 = self._model_to_canvas(element.node_j.x, element.node_j.y)
        factor = max(0.0, min(1.0, load.position))
        x = x1 + (x2 - x1) * factor
        y = y1 + (y2 - y1) * factor
        direction = _unit_vector(load.fx, -load.fy)
        if direction is None:
            return
        dx, dy = direction
        head_x, head_y = self._draw_vector_arrow(x - dx * 26, y - dy * 26, dx, dy, length=26, color="#d62728")
        self._draw_symbol_label(head_x + 8, head_y - 8, f"P=({_fmt_value(load.fx)}, {_fmt_value(load.fy)})", "#d62728")

    def _draw_member_temperature_symbol(self, load) -> None:
        element = self.builder.model.elements.get(load.element.id)
        if element is None:
            return
        x1, y1 = self._model_to_canvas(element.node_i.x, element.node_i.y)
        x2, y2 = self._model_to_canvas(element.node_j.x, element.node_j.y)
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        self._draw_symbol_label(mid_x + 8, mid_y - 18, f"T Tu={_fmt_value(load.Tu)}, Tb={_fmt_value(load.Tb)}", "#c00000")

    def _draw_vector_arrow(
        self,
        tail_x: float,
        tail_y: float,
        dx: float,
        dy: float,
        *,
        length: float,
        color: str,
        width: int = 2,
    ) -> tuple[float, float]:
        head_x = tail_x + dx * length
        head_y = tail_y + dy * length
        self.canvas.create_line(tail_x, tail_y, head_x, head_y, arrow=tk.LAST, fill=color, width=width, tags="symbol")
        return head_x, head_y

    def _draw_curved_arrow(
        self,
        x: float,
        y: float,
        *,
        clockwise: bool,
        color: str,
        radius: float = 12.0,
    ) -> None:
        if clockwise:
            angles = range(-40, 250, 20)
        else:
            angles = range(220, -70, -20)
        points = []
        for angle in angles:
            radians = math.radians(angle)
            points.extend((x + radius * math.cos(radians), y + radius * math.sin(radians)))
        self.canvas.create_line(*points, smooth=True, arrow=tk.LAST, fill=color, width=2, tags="symbol")

    def _draw_symbol_label(self, x: float, y: float, text: str, color: str) -> None:
        self.canvas.create_text(x, y, text=text, fill=color, anchor="w", font=("Segoe UI", 8), tags="symbol")

    def _draw_mass_symbol(self, node_id: int, mass) -> None:
        node = self.builder.model.nodes.get(node_id)
        if node is None:
            return
        x, y = self._model_to_canvas(node.x, node.y)
        r = self.node_radius + 5
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="", outline="#c00000", width=2, tags="symbol")
        label = _mass_label(mass)
        if label:
            self._draw_symbol_label(x + r + 6, y + 4, label, "#c00000")

    def _draw_diaphragm_symbol(self, node_ids: list[int]) -> None:
        points = [self.builder.model.nodes[node_id] for node_id in node_ids if node_id in self.builder.model.nodes]
        if len(points) < 2:
            return
        points.sort(key=lambda node: node.x)
        x1, y1 = self._model_to_canvas(points[0].x, points[0].y)
        x2, y2 = self._model_to_canvas(points[-1].x, points[-1].y)
        self.canvas.create_line(x1, y1 - 18, x2, y2 - 18, fill="#9467bd", dash=(5, 3), width=2, tags="symbol")
        for node in points:
            x, y = self._model_to_canvas(node.x, node.y)
            self.canvas.create_rectangle(x - 7, y - 7, x + 7, y + 7, outline="#9467bd", width=2, tags="symbol")
        self._draw_symbol_label(x1 + 8, y1 - 30, "D", "#9467bd")

    def _fit_view_to_model(self) -> None:
        nodes = list(self.builder.model.nodes.values())
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        if width <= 1:
            width = 800
        if height <= 1:
            height = 500

        if not nodes:
            self.view_scale = self.scale
            self.view_origin_x = width / 2
            self.view_origin_y = height / 2
            return

        min_x = min(node.x for node in nodes)
        max_x = max(node.x for node in nodes)
        min_y = min(node.y for node in nodes)
        max_y = max(node.y for node in nodes)
        span_x = max(max_x - min_x, 1.0)
        span_y = max(max_y - min_y, 1.0)
        margin = 80.0
        usable_width = max(width - 2 * margin, 100.0)
        usable_height = max(height - 2 * margin, 100.0)
        self.view_scale = min(usable_width / span_x, usable_height / span_y, self.scale)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        self.view_origin_x = width / 2 - center_x * self.view_scale
        self.view_origin_y = height / 2 + center_y * self.view_scale

    def _draw_grid(self) -> None:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        origin_x = self.view_origin_x
        origin_y = self.view_origin_y
        spacing = self.grid_spacing

        x = origin_x % spacing
        while x < width:
            self.canvas.create_line(x, 0, x, height, fill="#eeeeee", tags="grid")
            x += spacing

        y = origin_y % spacing
        while y < height:
            self.canvas.create_line(0, y, width, y, fill="#eeeeee", tags="grid")
            y += spacing

        self.canvas.create_line(0, origin_y, width, origin_y, fill="#d0d0d0", tags="grid")
        self.canvas.create_line(origin_x, 0, origin_x, height, fill="#d0d0d0", tags="grid")

    def _apply_selection_highlight(self) -> None:
        for item_id in self.node_id_to_item.values():
            self.canvas.itemconfigure(item_id, width=1, outline="")
        for item_id in self.element_id_to_item.values():
            self.canvas.itemconfigure(item_id, width=3)

        if self.selected_kind == "node" and self.selected_id in self.node_id_to_item:
            self.canvas.itemconfigure(self.node_id_to_item[int(self.selected_id)], outline="#ffbf00", width=3)
        elif self.selected_kind == "element" and self.selected_id in self.element_id_to_item:
            self.canvas.itemconfigure(self.element_id_to_item[str(self.selected_id)], width=6)

    def _find_node_near_canvas_point(self, canvas_x: float, canvas_y: float) -> int | None:
        for node_id, item_id in self.node_id_to_item.items():
            x1, y1, x2, y2 = self.canvas.coords(item_id)
            node_x = (x1 + x2) / 2
            node_y = (y1 + y2) / 2
            if math.hypot(canvas_x - node_x, canvas_y - node_y) <= self.snap_tolerance:
                return node_id
        return None

    def _find_element_near_canvas_point(self, canvas_x: float, canvas_y: float) -> str | None:
        best_id = None
        best_distance = self.snap_tolerance
        for element_id, item_id in self.element_id_to_item.items():
            x1, y1, x2, y2 = self.canvas.coords(item_id)
            distance = _point_segment_distance(canvas_x, canvas_y, x1, y1, x2, y2)
            if distance <= best_distance:
                best_id = element_id
                best_distance = distance
        return best_id

    def _find_node_near_model_point(self, x: float, y: float) -> int | None:
        tolerance = self.snap_tolerance / self.scale
        for node_id, node in self.builder.model.nodes.items():
            if math.hypot(x - node.x, y - node.y) <= tolerance:
                return node_id
        return None

    def _model_to_canvas(self, x: float, y: float) -> tuple[float, float]:
        return self.view_origin_x + x * self.view_scale, self.view_origin_y - y * self.view_scale

    def _canvas_to_model(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
        return (canvas_x - self.view_origin_x) / self.view_scale, (self.view_origin_y - canvas_y) / self.view_scale


def _element_number(element_id: str) -> int:
    if element_id.startswith("E") and element_id[1:].isdigit():
        return int(element_id[1:])
    return 0


def _point_segment_distance(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    return math.hypot(px - closest_x, py - closest_y)


def _unit_vector(dx: float, dy: float) -> tuple[float, float] | None:
    length = math.hypot(dx, dy)
    if length == 0:
        return None
    return dx / length, dy / length


def _offset_point(x: float, y: float, dx: float, dy: float, distance: float) -> tuple[float, float]:
    return x + dx * distance, y + dy * distance


def _fmt_value(value: float) -> str:
    return f"{value:.3g}"


def _mass_label(mass) -> str:
    if isinstance(mass, (int, float)):
        value = float(mass)
        parts = []
        if value:
            parts.extend((f"mass_ux={_fmt_value(value)}", f"mass_uy={_fmt_value(value)}"))
        return ", ".join(parts)
    parts = []
    if mass.mass_ux:
        parts.append(f"mass_ux={_fmt_value(mass.mass_ux)}")
    if mass.mass_uy:
        parts.append(f"mass_uy={_fmt_value(mass.mass_uy)}")
    if mass.inertia_rz:
        parts.append(f"mass_rz={_fmt_value(mass.inertia_rz)}")
    return ", ".join(parts)
