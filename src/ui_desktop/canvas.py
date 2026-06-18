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

CANVAS_BACKGROUND = "#ffffff"
GRID_COLOR = "#ebebeb"
GRID_AXIS_COLOR = "#d2d2d2"
MEMBER_COLOR = "#1f4e79"
MEMBER_TRUSS_COLOR = "#184e77"
NODE_FILL_COLOR = "#1f4e79"
NODE_OUTLINE_COLOR = "#1f4e79"
LABEL_COLOR = "#2f2f2f"
SELECTED_COLOR = "#ff8c00"
SYMBOL_COLOR = "#6b7280"


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

        self.active_command: str | None = None
        self.active_element_type = "frame"
        self.active_material_id = "M1"
        self.active_section_id = "S1"
        self.active_node_is_hinged = False
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
        self.grid_visible = True
        self.local_axes_visible = False
        self.snap_to_grid = False
        self.grid_spacing = 1.0
        self.snap_tolerance = 12.0
        self.node_radius = 5
        self._view_initialized = False
        self._pan_last: tuple[int, int] | None = None
        self._window_start: tuple[int, int] | None = None
        self._window_rect_id: int | None = None
        self._window_dragging = False
        self.next_node_id = 1
        self.next_element_number = 1
        self.pending_start_node_id: int | None = None
        self.selected_kind: str | None = None
        self.selected_id: int | str | None = None
        self.selected_node_ids: set[int] = set()
        self.selected_element_ids: set[str] = set()

        self.item_to_node_id: dict[int, int] = {}
        self.node_id_to_item: dict[int, int] = {}
        self.item_to_element_id: dict[int, str] = {}
        self.element_id_to_item: dict[str, int] = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, background=CANVAS_BACKGROUND, highlightthickness=1, highlightbackground="#cfd8e3")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", self._handle_configure)
        self.canvas.bind("<Button-1>", self._handle_click)
        self.canvas.bind("<ButtonPress-1>", self._handle_button_press, add="+")
        self.canvas.bind("<B1-Motion>", self._handle_drag)
        self.canvas.bind("<ButtonRelease-1>", self._handle_button_release)
        self.canvas.bind("<MouseWheel>", self._handle_mouse_wheel)
        self.canvas.bind("<Button-4>", self._handle_mouse_wheel)
        self.canvas.bind("<Button-5>", self._handle_mouse_wheel)
        self.canvas.bind("<ButtonPress-2>", self._handle_middle_button_press)
        self.canvas.bind("<B2-Motion>", self._handle_middle_drag)
        self.canvas.bind("<ButtonRelease-2>", self._handle_middle_button_release)

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

        self.restore_full_view(notify=False)
        self.change_callback()
        self.status_callback(
            f"Loaded model with {len(self.builder.model.nodes)} nodes and {len(self.builder.model.elements)} elements."
        )

    def redraw_model(self, *, fit_view: bool = False) -> None:
        """Reload canvas items from the current builder model."""
        self.canvas.delete("all")
        self.item_to_node_id.clear()
        self.node_id_to_item.clear()
        self.item_to_element_id.clear()
        self.element_id_to_item.clear()
        if fit_view or not self._view_initialized:
            self._fit_view_to_model()
            self._view_initialized = True
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
        self.active_command = None if command == "Select / Inspect" else command
        if command != "Pan":
            self._pan_last = None
        if command != "Select / Inspect":
            self._clear_window_selection_preview()
        if command != "Draw Member":
            self.pending_start_node_id = None
        self.status_callback(self.command_instruction())

    def command_instruction(self) -> str:
        if self.active_command == "Pan":
            return "Pan: drag the canvas to move the viewport."
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
            return "Assign Diaphragm: select nodes, choose a group id/action, then apply."
        if self.active_command == "Delete":
            return "Delete: click a node or member to remove it."
        if self.active_command == "Replicate":
            return "Replicate: select nodes or members, set copies/dx/dy, then apply."
        return "Select / Inspect: click a node or member to inspect it."

    def set_active_element_type(self, element_type: str) -> None:
        self.active_element_type = element_type

    def set_active_material(self, material_id: str) -> None:
        self.active_material_id = material_id

    def set_active_section(self, section_id: str) -> None:
        self.active_section_id = section_id

    def set_active_node_hinge(self, is_hinged: bool) -> None:
        self.active_node_is_hinged = bool(is_hinged)

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

    def set_diaphragm_settings(self, action: str, group_id: str) -> None:
        self.diaphragm_action = action
        self.diaphragm_group_id = group_id

    def set_grid_visible(self, visible: bool) -> None:
        self.grid_visible = visible
        self.redraw_model()
        self.status_callback("Grid On." if visible else "Grid Off.")

    def set_snap_to_grid(self, enabled: bool) -> None:
        self.snap_to_grid = enabled
        self.status_callback("Snap On." if enabled else "Snap Off.")

    def set_local_axes_visible(self, visible: bool) -> None:
        self.local_axes_visible = visible
        self.redraw_model()
        self.status_callback("Local Axes On." if visible else "Local Axes Off.")

    def set_grid_spacing(self, spacing: float) -> bool:
        if spacing <= 0:
            self.status_callback("Grid spacing must be positive.")
            return False
        self.grid_spacing = spacing
        self.redraw_model()
        self.status_callback(f"Grid spacing set to {spacing:.6g}.")
        return True

    def zoom_in(self) -> None:
        self._zoom(1.25)
        self.status_callback("Zoom In.")

    def zoom_out(self) -> None:
        self._zoom(0.8)
        self.status_callback("Zoom Out.")

    def restore_full_view(self, *, notify: bool = True) -> None:
        self.redraw_model(fit_view=True)
        if notify:
            self.status_callback("Full View.")

    def selection_count(self) -> int:
        return self._selection_count()

    def add_node_by_coordinates(self, x: float, y: float, *, is_hinged: bool | None = None) -> int:
        existing_node_id = self._find_node_near_model_point(x, y)
        if existing_node_id is not None:
            self.select_node(existing_node_id)
            return existing_node_id

        node_id = self.next_node_id
        self.next_node_id += 1
        node_is_hinged = self.active_node_is_hinged if is_hinged is None else bool(is_hinged)
        self.builder.add_node(node_id, x, y, is_hinged=node_is_hinged)
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
        end_node_id = self.add_node_by_coordinates(end_x, end_y, is_hinged=False)
        return self._create_element(start_node_id, end_node_id)

    def select_node(self, node_id: int) -> None:
        self.selected_kind = "node"
        self.selected_id = node_id
        self.selected_node_ids = {node_id}
        self.selected_element_ids.clear()
        self._refresh_selection_display()
        self.selection_callback("node", self.builder.model.nodes.get(node_id))

    def select_element(self, element_id: str) -> None:
        self.selected_kind = "element"
        self.selected_id = element_id
        self.selected_node_ids.clear()
        self.selected_element_ids = {element_id}
        self._refresh_selection_display()
        self.selection_callback("element", self.builder.model.elements.get(element_id))

    def clear_selection(self, *, notify: bool = True) -> None:
        self.selected_kind = None
        self.selected_id = None
        self.selected_node_ids.clear()
        self.selected_element_ids.clear()
        self._refresh_selection_display()
        if notify:
            self.selection_callback(None, None)

    def _ensure_placeholder_properties(self) -> None:
        self.builder.add_material("M1", E=1.0)
        self.builder.add_section("S1", A=1.0, I=1.0)

    def _handle_configure(self, _event) -> None:
        if not self._view_initialized:
            self.redraw_model(fit_view=True)
        else:
            self.redraw_model()

    def _handle_button_press(self, event) -> None:
        if self.active_command == "Pan":
            self._pan_last = (event.x, event.y)
        elif self._is_neutral_selection_mode() and not self._event_has_ctrl(event):
            node_id = self._find_node_near_canvas_point(event.x, event.y)
            element_id = self._find_element_near_canvas_point(event.x, event.y) if node_id is None else None
            if node_id is None and element_id is None:
                self._window_start = (event.x, event.y)
                self._window_dragging = False

    def _handle_drag(self, event) -> None:
        if self._is_neutral_selection_mode() and self._window_start is not None:
            self._update_window_selection_preview(event.x, event.y)
            return
        if self.active_command != "Pan" or self._pan_last is None:
            return
        self._pan_view(event.x, event.y)

    def _handle_button_release(self, event) -> None:
        if self._is_neutral_selection_mode() and self._window_start is not None:
            self._finish_window_selection(event.x, event.y)
        self._pan_last = None

    def _handle_middle_button_press(self, event) -> None:
        self._pan_last = (event.x, event.y)

    def _handle_middle_drag(self, event) -> None:
        if self._pan_last is None:
            return
        self._pan_view(event.x, event.y)

    def _handle_middle_button_release(self, _event) -> None:
        self._pan_last = None

    def _handle_mouse_wheel(self, event) -> str | None:
        delta = getattr(event, "delta", 0)
        if not delta:
            num = getattr(event, "num", None)
            if num == 4:
                delta = 120
            elif num == 5:
                delta = -120
        if not delta:
            return None
        factor = 1.15 if delta > 0 else 1 / 1.15
        self._zoom(factor, getattr(event, "x", None), getattr(event, "y", None))
        return "break"

    def _handle_click(self, event) -> None:
        if self.active_command == "Pan":
            return
        node_id = self._find_node_near_canvas_point(event.x, event.y)
        element_id = self._find_element_near_canvas_point(event.x, event.y) if node_id is None else None

        if self.active_command == "Draw Node":
            x, y = self._canvas_to_model_point(event.x, event.y)
            self.add_node_by_coordinates(x, y)
        elif self.active_command == "Draw Member":
            if node_id is None:
                x, y = self._canvas_to_model_point(event.x, event.y)
                node_id = self.add_node_by_coordinates(x, y, is_hinged=False)
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
                self.status_callback("Assign Diaphragm: select nodes, then click Apply.")
                return
            if self._event_has_ctrl(event):
                self._toggle_node_selection(node_id)
            else:
                self.select_node(node_id)
            self.status_callback("Assign Diaphragm: select at least two nodes, then click Apply.")
        elif node_id is not None:
            if self._event_has_ctrl(event):
                self._toggle_node_selection(node_id)
            else:
                self.select_node(node_id)
                self.status_callback(f"Selected node {node_id}.")
        elif element_id is not None:
            if self._event_has_ctrl(event):
                self._toggle_element_selection(element_id)
            else:
                self.select_element(element_id)
                self.status_callback(f"Selected member {element_id}.")
        else:
            self.clear_selection()
            self.status_callback(self.command_instruction())

    def _is_neutral_selection_mode(self) -> bool:
        return self.active_command in (None, "Materials / Sections", "Replicate")

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
        selection_count = self._selection_count()
        if selection_count > 0 and (
            (node_id is None and element_id is None)
            or (
                selection_count > 1
                and (
                    (node_id is not None and node_id in self.selected_node_ids)
                    or (element_id is not None and element_id in self.selected_element_ids)
                )
            )
        ):
            self._delete_selected_targets()
            return
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

    def _delete_selected_targets(self) -> None:
        deleted_members = 0
        blocked_nodes = []
        for element_id in sorted(self.selected_element_ids):
            if self.builder.model.elements.pop(element_id, None) is not None:
                deleted_members += 1

        deleted_nodes = 0
        for node_id in sorted(self.selected_node_ids):
            connected = [
                element_id
                for element_id, element in self.builder.model.elements.items()
                if element.node_i.id == node_id or element.node_j.id == node_id
            ]
            if connected:
                blocked_nodes.append(node_id)
                continue
            if self.builder.model.nodes.pop(node_id, None) is None:
                continue
            self.builder.model.supports.pop(node_id, None)
            self.builder.model.lumped_masses.pop(node_id, None)
            for diaphragm_id, node_ids in list(self.builder.model.diaphragm_ux_groups.items()):
                self.builder.model.diaphragm_ux_groups[diaphragm_id] = [
                    existing_id for existing_id in node_ids if existing_id != node_id
                ]
                if not self.builder.model.diaphragm_ux_groups[diaphragm_id]:
                    self.builder.model.diaphragm_ux_groups.pop(diaphragm_id, None)
            deleted_nodes += 1

        self.clear_selection()
        self.redraw_model()
        self.change_callback()
        parts = []
        if deleted_nodes:
            parts.append(f"deleted {deleted_nodes} node(s)")
        if deleted_members:
            parts.append(f"deleted {deleted_members} member(s)")
        if blocked_nodes:
            parts.append(f"blocked node(s): {', '.join(str(node_id) for node_id in blocked_nodes)}")
        self.status_callback("Delete selection: " + "; ".join(parts) if parts else "Delete selection: nothing deleted.")

    def replicate_selection(self, copies: int, dx: float, dy: float) -> tuple[int, int] | None:
        if copies < 1:
            self.status_callback("Replicate: number of copies must be at least 1.")
            return None
        if self._selection_count() == 0:
            self.status_callback("Replicate: select nodes or members first.")
            return None

        selected_elements = [
            self.builder.model.elements[element_id]
            for element_id in sorted(self.selected_element_ids)
            if element_id in self.builder.model.elements
        ]
        node_ids_to_copy = {
            node_id for node_id in self.selected_node_ids if node_id in self.builder.model.nodes
        }
        for element in selected_elements:
            node_ids_to_copy.add(element.node_i.id)
            node_ids_to_copy.add(element.node_j.id)

        new_node_ids: set[int] = set()
        new_element_ids: set[str] = set()
        for copy_index in range(1, copies + 1):
            node_map: dict[int, int] = {}
            offset_x = copy_index * dx
            offset_y = copy_index * dy
            for old_node_id in sorted(node_ids_to_copy):
                old_node = self.builder.model.nodes.get(old_node_id)
                if old_node is None:
                    continue
                new_node_id = self.next_node_id
                self.next_node_id += 1
                self.builder.add_node(
                    new_node_id,
                    old_node.x + offset_x,
                    old_node.y + offset_y,
                    is_hinged=getattr(old_node, "is_hinged", False),
                )
                node_map[old_node_id] = new_node_id
                new_node_ids.add(new_node_id)

            for old_element in selected_elements:
                start_node_id = node_map.get(old_element.node_i.id)
                end_node_id = node_map.get(old_element.node_j.id)
                if start_node_id is None or end_node_id is None:
                    continue
                new_element_id = f"E{self.next_element_number}"
                self.next_element_number += 1
                self.builder.add_element(
                    new_element_id,
                    old_element.type,
                    start_node_id,
                    end_node_id,
                    old_element.material.id,
                    old_element.section.id,
                    release_start=old_element.release_start,
                    release_end=old_element.release_end,
                    is_axially_rigid=old_element.is_axially_rigid,
                )
                new_element_ids.add(new_element_id)

        self._mark_model_dirty()
        self.redraw_model()
        self.change_callback()
        self._set_multi_selection(new_node_ids, new_element_ids)
        self.status_callback(
            f"Replicated {len(new_node_ids)} node(s) and {len(new_element_ids)} member(s)."
        )
        return len(new_node_ids), len(new_element_ids)

    def move_selection(self, dx: float, dy: float) -> tuple[int, int] | None:
        if self._selection_count() == 0:
            self.status_callback("Move Selection: select nodes or members first.")
            return None

        node_ids_to_move = {node_id for node_id in self.selected_node_ids if node_id in self.builder.model.nodes}
        element_ids_to_move = {
            element_id for element_id in self.selected_element_ids if element_id in self.builder.model.elements
        }
        for element_id in element_ids_to_move:
            element = self.builder.model.elements[element_id]
            node_ids_to_move.add(element.node_i.id)
            node_ids_to_move.add(element.node_j.id)

        moved_nodes = 0
        for node_id in sorted(node_ids_to_move):
            node = self.builder.model.nodes.get(node_id)
            if node is None:
                continue
            node.x += dx
            node.y += dy
            moved_nodes += 1

        self._mark_model_dirty()
        self.redraw_model()
        self.change_callback()
        self._set_multi_selection(node_ids_to_move, element_ids_to_move)
        self.status_callback(f"Moved {moved_nodes} node(s) by dx={dx:.6g}, dy={dy:.6g}.")
        return moved_nodes, len(element_ids_to_move)

    def _toggle_node_selection(self, node_id: int) -> None:
        if node_id in self.selected_node_ids:
            self.selected_node_ids.remove(node_id)
        else:
            self.selected_node_ids.add(node_id)
        self._notify_current_selection()

    def _toggle_element_selection(self, element_id: str) -> None:
        if element_id in self.selected_element_ids:
            self.selected_element_ids.remove(element_id)
        else:
            self.selected_element_ids.add(element_id)
        self._notify_current_selection()

    def _set_multi_selection(self, node_ids: set[int], element_ids: set[str]) -> None:
        self.selected_node_ids = {node_id for node_id in node_ids if node_id in self.builder.model.nodes}
        self.selected_element_ids = {
            element_id for element_id in element_ids if element_id in self.builder.model.elements
        }
        self._notify_current_selection()

    def _notify_current_selection(self) -> None:
        count = self._selection_count()
        if count == 0:
            self.selected_kind = None
            self.selected_id = None
            self._refresh_selection_display()
            self.selection_callback(None, None)
            self.status_callback("Selection cleared.")
            return
        if count == 1 and self.selected_node_ids:
            node_id = next(iter(self.selected_node_ids))
            self.selected_kind = "node"
            self.selected_id = node_id
            self._refresh_selection_display()
            self.selection_callback("node", self.builder.model.nodes.get(node_id))
            self.status_callback(f"Selected node {node_id}.")
            return
        if count == 1 and self.selected_element_ids:
            element_id = next(iter(self.selected_element_ids))
            self.selected_kind = "element"
            self.selected_id = element_id
            self._refresh_selection_display()
            self.selection_callback("element", self.builder.model.elements.get(element_id))
            self.status_callback(f"Selected member {element_id}.")
            return

        self.selected_kind = "multi"
        self.selected_id = None
        self._refresh_selection_display()
        selection = {
            "nodes": sorted(self.selected_node_ids),
            "elements": sorted(self.selected_element_ids),
            "count": count,
        }
        self.selection_callback("multi", selection)
        self.status_callback(f"Selected {count} objects.")

    def _selection_count(self) -> int:
        return len(self.selected_node_ids) + len(self.selected_element_ids)

    def _event_has_ctrl(self, event) -> bool:
        return bool(getattr(event, "state", 0) & 0x0004)

    def _clear_window_selection_preview(self) -> None:
        if self._window_rect_id is not None:
            self.canvas.delete(self._window_rect_id)
        self._window_rect_id = None
        self._window_start = None
        self._window_dragging = False

    def _update_window_selection_preview(self, x: int, y: int) -> None:
        if self._window_start is None:
            return
        start_x, start_y = self._window_start
        if abs(x - start_x) < 4 and abs(y - start_y) < 4:
            return
        self._window_dragging = True
        if self._window_rect_id is None:
            self._window_rect_id = self.canvas.create_rectangle(
                start_x,
                start_y,
                x,
                y,
                outline="#0b65c2",
                dash=(4, 2),
                width=1,
                tags="selection-window",
            )
        else:
            self.canvas.coords(self._window_rect_id, start_x, start_y, x, y)

    def _finish_window_selection(self, x: int, y: int) -> None:
        if self._window_start is None:
            return
        start_x, start_y = self._window_start
        dragging = self._window_dragging
        self._clear_window_selection_preview()
        if not dragging:
            return
        left_to_right = x >= start_x
        x1, x2 = sorted((start_x, x))
        y1, y2 = sorted((start_y, y))
        self._set_multi_selection(
            self._nodes_in_window(x1, y1, x2, y2),
            self._elements_in_window(x1, y1, x2, y2, fully_inside=left_to_right),
        )

    def _nodes_in_window(self, x1: float, y1: float, x2: float, y2: float) -> set[int]:
        selected = set()
        for node_id, node in self.builder.model.nodes.items():
            cx, cy = self._model_to_canvas(node.x, node.y)
            if x1 <= cx <= x2 and y1 <= cy <= y2:
                selected.add(node_id)
        return selected

    def _elements_in_window(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        fully_inside: bool,
    ) -> set[str]:
        selected = set()
        for element_id, element in self.builder.model.elements.items():
            ax, ay = self._model_to_canvas(element.node_i.x, element.node_i.y)
            bx, by = self._model_to_canvas(element.node_j.x, element.node_j.y)
            if fully_inside:
                if _point_in_rect(ax, ay, x1, y1, x2, y2) and _point_in_rect(bx, by, x1, y1, x2, y2):
                    selected.add(element_id)
            elif _segment_intersects_rect(ax, ay, bx, by, x1, y1, x2, y2):
                selected.add(element_id)
        return selected

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
                coord_system=settings.coord_system,
                direction=settings.direction,
                value=settings.value,
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
                coord_system=settings.coord_system,
                direction=settings.direction,
                value=settings.value,
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

    def selected_diaphragm_node_ids(self) -> list[int]:
        return sorted(node_id for node_id in self.selected_node_ids if node_id in self.builder.model.nodes)

    def clear_node_selection(self) -> None:
        self.clear_selection()

    def apply_diaphragm_assignment(self) -> list[int] | None:
        group_id = self.diaphragm_group_id.strip() or "D1"
        action = self.diaphragm_action
        if action == "Delete":
            removed = self.builder.model.diaphragm_ux_groups.pop(group_id, None)
            self._mark_model_dirty()
            self.redraw_model()
            self.change_callback()
            self.status_callback(f"Deleted diaphragm group {group_id}." if removed is not None else f"Diaphragm group {group_id} not found.")
            return []

        selected_node_ids = self.selected_diaphragm_node_ids()
        if len(selected_node_ids) < 2:
            self.status_callback("Assign Diaphragm: select at least two nodes.")
            return None

        if action == "Add":
            existing = self.builder.model.diaphragm_ux_groups.get(group_id, [])
            node_ids = list(dict.fromkeys([*existing, *selected_node_ids]))
        else:
            node_ids = list(dict.fromkeys(selected_node_ids))
        self.builder.add_diaphragm_group(group_id, node_ids)
        self.diaphragm_node_ids = node_ids
        self.redraw_model()
        self._set_multi_selection(set(node_ids), set())
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

    def update_selected_node_coordinates(self, x: float, y: float):
        if self.selected_kind != "node" or self.selected_id not in self.builder.model.nodes:
            self.status_callback("Node Coordinates: select one node first.")
            return None

        node_id = int(self.selected_id)
        node = self.builder.model.nodes[node_id]
        node.x = x
        node.y = y
        self._mark_model_dirty()
        self.redraw_model()
        self.select_node(node_id)
        self.change_callback()
        self.status_callback(f"Updated node {node_id} coordinates to ({x:.6g}, {y:.6g}).")
        return node

    def update_selected_node_hinge(self, is_hinged: bool):
        if self.selected_kind != "node" or self.selected_id not in self.builder.model.nodes:
            self.status_callback("Node Hinge: select one node first.")
            return None

        node_id = int(self.selected_id)
        node = self.builder.model.nodes[node_id]
        node.is_hinged = bool(is_hinged)
        self._mark_model_dirty()
        self.redraw_model()
        self.select_node(node_id)
        self.change_callback()
        state = "hinged" if node.is_hinged else "moment-continuous"
        self.status_callback(f"Node {node_id} set to {state}.")
        return node

    def rename_selected_node(self, new_node_id: int):
        if self.selected_kind != "node" or self.selected_id not in self.builder.model.nodes:
            self.status_callback("Node ID: select one node first.")
            return None

        old_node_id = int(self.selected_id)
        try:
            node = self.builder.rename_node(old_node_id, new_node_id)
        except (KeyError, ValueError) as exc:
            self.status_callback(f"Node ID: {exc}")
            return None

        self.next_node_id = max(self.builder.model.nodes, default=0) + 1
        self.redraw_model()
        self.select_node(node.id)
        self.change_callback()
        self.status_callback(f"Renamed node {old_node_id} to {node.id}.")
        return node

    def rename_selected_member(self, new_element_id: str):
        if self.selected_kind != "element" or self.selected_id not in self.builder.model.elements:
            self.status_callback("Member ID: select one member first.")
            return None

        old_element_id = str(self.selected_id)
        try:
            element = self.builder.rename_element(old_element_id, new_element_id)
        except (KeyError, ValueError) as exc:
            self.status_callback(f"Member ID: {exc}")
            return None

        element_numbers = [_element_number(element_id) for element_id in self.builder.model.elements]
        self.next_element_number = max(element_numbers, default=0) + 1
        self.redraw_model()
        self.select_element(element.id)
        self.change_callback()
        self.status_callback(f"Renamed member {old_element_id} to {element.id}.")
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
        node = self.builder.model.nodes[node_id]
        fill, outline, width = self._node_style(node)
        item_id = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline=outline, width=width)
        label_id = self.canvas.create_text(cx + 10, cy - 10, text=str(node_id), fill=LABEL_COLOR, anchor="w", font=("Segoe UI", 8))
        self.canvas.addtag_withtag("node", item_id)
        self.canvas.addtag_withtag("node-label", label_id)
        self.item_to_node_id[item_id] = node_id
        self.node_id_to_item[node_id] = item_id

    def _draw_element(self, element_id: str, start_node_id: int, end_node_id: int, *, element_type: str) -> None:
        start_node = self.builder.model.nodes[start_node_id]
        end_node = self.builder.model.nodes[end_node_id]
        x1, y1 = self._model_to_canvas(start_node.x, start_node.y)
        x2, y2 = self._model_to_canvas(end_node.x, end_node.y)
        color = SELECTED_COLOR if element_id in self.selected_element_ids else self._element_color(element_type)
        width = 5 if element_id in self.selected_element_ids else 3
        item_id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        self.canvas.tag_lower(item_id)
        self.item_to_element_id[item_id] = element_id
        self.element_id_to_item[element_id] = item_id
        element = self.builder.model.elements[element_id]
        if element_type == "truss" or element.release_start:
            self._draw_member_end_hinge_symbol(x1, y1, x2, y2, color)
        if element_type == "truss" or element.release_end:
            self._draw_member_end_hinge_symbol(x2, y2, x1, y1, color)

    def _draw_member_end_hinge_symbol(self, x: float, y: float, toward_x: float, toward_y: float, color: str) -> None:
        length = math.hypot(toward_x - x, toward_y - y)
        if length <= 0:
            return
        ux = (toward_x - x) / length
        uy = (toward_y - y) / length
        cx = x + ux * (self.node_radius + 5)
        cy = y + uy * (self.node_radius + 5)
        r = max(2, self.node_radius - 2)
        self.canvas.create_oval(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            fill="white",
            outline=color,
            width=1.5,
            tags="symbol",
        )

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
        if self.local_axes_visible:
            self._draw_member_local_axes()

    def _draw_member_local_axes(self) -> None:
        for element in self.builder.model.elements.values():
            x1, y1 = self._model_to_canvas(element.node_i.x, element.node_i.y)
            x2, y2 = self._model_to_canvas(element.node_j.x, element.node_j.y)
            axis = _unit_vector(x2 - x1, y2 - y1)
            if axis is None:
                continue
            tx, ty = axis
            nx, ny = ty, -tx
            mid_x = x1 + (x2 - x1) * 0.42
            mid_y = y1 + (y2 - y1) * 0.42
            length = 24.0
            head_1 = self._draw_local_axis_arrow(mid_x, mid_y, tx, ty, length, "#1f77b4")
            head_2 = self._draw_local_axis_arrow(mid_x, mid_y, nx, ny, length * 0.78, "#2ca02c")
            self.canvas.create_text(
                head_1[0] + 3,
                head_1[1] - 3,
                text="1",
                fill=MEMBER_COLOR,
                anchor="w",
                font=("Segoe UI", 8),
                tags=("symbol", "local-axis"),
            )
            self.canvas.create_text(
                head_2[0] + 3,
                head_2[1] - 3,
                text="2",
                fill=MEMBER_TRUSS_COLOR,
                anchor="w",
                font=("Segoe UI", 8),
                tags=("symbol", "local-axis"),
            )

    def _draw_local_axis_arrow(
        self,
        tail_x: float,
        tail_y: float,
        dx: float,
        dy: float,
        length: float,
        color: str,
    ) -> tuple[float, float]:
        head_x = tail_x + dx * length
        head_y = tail_y + dy * length
        self.canvas.create_line(
            tail_x,
            tail_y,
            head_x,
            head_y,
            arrow=tk.LAST,
            fill=color,
            width=1.5,
            tags=("symbol", "local-axis"),
        )
        return head_x, head_y

    def _draw_support_symbol(self, support) -> None:
        x, y = self._model_to_canvas(support.node.x, support.node.y)
        if support.restrain_ux and support.restrain_uy and support.restrain_rz:
            self.canvas.create_rectangle(x - 9, y + 8, x + 9, y + 13, fill=SYMBOL_COLOR, outline="", tags="symbol")
        elif support.restrain_ux and support.restrain_uy:
            self.canvas.create_polygon(x, y + 7, x - 9, y + 17, x + 9, y + 17, fill=SYMBOL_COLOR, tags="symbol")
        else:
            self.canvas.create_oval(x - 8, y + 8, x + 8, y + 17, outline=SYMBOL_COLOR, tags="symbol")
        self._draw_settlement_symbol(x, y, support)

    def _draw_settlement_symbol(self, x: float, y: float, support) -> None:
        if support.settlement_ux:
            dx = 1 if support.settlement_ux > 0 else -1
            head_x, head_y = self._draw_vector_arrow(x, y, dx, 0, length=18, color="#c00000")
            self._draw_symbol_label(head_x + 4 * dx, head_y + 8, f"ux={_fmt_value(support.settlement_ux)}", "#a94442")
        if support.settlement_uy:
            dy = -1 if support.settlement_uy > 0 else 1
            head_x, head_y = self._draw_vector_arrow(x, y, 0, dy, length=18, color="#c00000")
            self._draw_symbol_label(head_x - 4, head_y + 6 * dy, f"uy={_fmt_value(support.settlement_uy)}", "#a94442")
        if support.settlement_rz:
            self._draw_curved_arrow(x, y, clockwise=support.settlement_rz < 0, color="#c00000", radius=15)
            self._draw_symbol_label(x + 18, y + 24, f"rz={_fmt_value(support.settlement_rz)}", "#a94442")

    def _draw_nodal_load_symbol(self, load) -> None:
        node = self.builder.model.nodes.get(load.node.id)
        if node is None:
            return
        x, y = self._model_to_canvas(node.x, node.y)
        if load.fx:
            dx = 1 if load.fx > 0 else -1
            head_x, head_y = self._draw_vector_arrow(x, y, dx, 0, length=22, color="#d62728")
            self._draw_symbol_label(head_x + 4 * dx, head_y + 9, f"Fx={_fmt_value(load.fx)}", "#a94442")
        if load.fy:
            dy = -1 if load.fy > 0 else 1
            head_x, head_y = self._draw_vector_arrow(x, y, 0, dy, length=22, color="#d62728")
            self._draw_symbol_label(head_x - 4, head_y + 6 * dy, f"Fy={_fmt_value(load.fy)}", "#a94442")
        if load.mz:
            self._draw_curved_arrow(x, y, clockwise=load.mz < 0, color="#d62728", radius=17)
            self._draw_symbol_label(x + 20, y + 18, f"Mz={_fmt_value(load.mz)}", "#a94442")

    def _draw_member_udl_symbol(self, load) -> None:
        element = self.builder.model.elements.get(load.element.id)
        if element is None:
            return
        x1, y1 = self._model_to_canvas(element.node_i.x, element.node_i.y)
        x2, y2 = self._model_to_canvas(element.node_j.x, element.node_j.y)
        direction = _member_load_display_vector(load, x1, y1, x2, y2, load.wx, load.wy)
        if direction is None:
            return
        dx, dy = direction
        start = _offset_point(x1, y1, dx, dy, -18)
        end = _offset_point(x2, y2, dx, dy, -18)
        self.canvas.create_line(start[0], start[1], end[0], end[1], fill="#ff8c00", width=1, tags="symbol")
        for factor in (0.25, 0.5, 0.75):
            x = x1 + (x2 - x1) * factor
            y = y1 + (y2 - y1) * factor
            self._draw_vector_arrow(x - dx * 18, y - dy * 18, dx, dy, length=18, color="#ff7f0e")
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        self._draw_symbol_label(mid_x + 8, mid_y - 8, _member_load_label("w", load, load.wx, load.wy), "#ff7f0e")

    def _draw_member_point_load_symbol(self, load) -> None:
        element = self.builder.model.elements.get(load.element.id)
        if element is None:
            return
        x1, y1 = self._model_to_canvas(element.node_i.x, element.node_i.y)
        x2, y2 = self._model_to_canvas(element.node_j.x, element.node_j.y)
        factor = max(0.0, min(1.0, load.position))
        x = x1 + (x2 - x1) * factor
        y = y1 + (y2 - y1) * factor
        direction = _member_load_display_vector(load, x1, y1, x2, y2, load.fx, load.fy)
        if direction is None:
            return
        dx, dy = direction
        head_x, head_y = self._draw_vector_arrow(x - dx * 26, y - dy * 26, dx, dy, length=26, color="#d62728")
        self._draw_symbol_label(head_x + 8, head_y - 8, _member_load_label("P", load, load.fx, load.fy), "#d62728")

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
        self.canvas.create_line(*points, smooth=True, arrow=tk.LAST, fill=color, width=1.5, tags="symbol")

    def _draw_symbol_label(self, x: float, y: float, text: str, color: str) -> None:
        self.canvas.create_text(x, y, text=text, fill=color, anchor="w", font=("Segoe UI", 7), tags="symbol")

    def _draw_mass_symbol(self, node_id: int, mass) -> None:
        node = self.builder.model.nodes.get(node_id)
        if node is None:
            return
        x, y = self._model_to_canvas(node.x, node.y)
        r = self.node_radius + 5
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="", outline="#a94442", width=1.5, tags="symbol")
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
        self.canvas.create_line(x1, y1 - 16, x2, y2 - 16, fill="#6f42c1", dash=(4, 3), width=1.5, tags="symbol")
        self._draw_symbol_label(x1 + 8, y1 - 28, "D", "#6f42c1")

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
        if not self.grid_visible:
            return
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        spacing = self.grid_spacing * self.view_scale
        if spacing < 4:
            return

        x = self.view_origin_x % spacing
        while x < width:
            self.canvas.create_line(x, 0, x, height, fill=GRID_COLOR, tags="grid")
            x += spacing

        y = self.view_origin_y % spacing
        while y < height:
            self.canvas.create_line(0, y, width, y, fill=GRID_COLOR, tags="grid")
            y += spacing

        self.canvas.create_line(0, self.view_origin_y, width, self.view_origin_y, fill=GRID_AXIS_COLOR, tags="grid")
        self.canvas.create_line(self.view_origin_x, 0, self.view_origin_x, height, fill=GRID_AXIS_COLOR, tags="grid")

    def _refresh_selection_display(self) -> None:
        if self.canvas.find_all():
            self.redraw_model()
        else:
            self._apply_selection_highlight()

    def _apply_selection_highlight(self) -> None:
        for node_id, item_id in self.node_id_to_item.items():
            node = self.builder.model.nodes.get(node_id)
            fill, outline, width = self._node_style(node)
            self.canvas.itemconfigure(item_id, fill=fill, outline=outline, width=width)
        for element_id, item_id in self.element_id_to_item.items():
            element = self.builder.model.elements.get(element_id)
            color = self._element_color(getattr(element, "type", "frame"))
            self.canvas.itemconfigure(item_id, fill=color, width=3)

        for node_id in self.selected_node_ids:
            if node_id in self.node_id_to_item:
                self.canvas.itemconfigure(
                    self.node_id_to_item[node_id],
                    fill=SELECTED_COLOR,
                    outline=SELECTED_COLOR,
                    width=4,
                )
        for element_id in self.selected_element_ids:
            if element_id in self.element_id_to_item:
                self.canvas.itemconfigure(self.element_id_to_item[element_id], width=5, fill=SELECTED_COLOR)

    def _node_style(self, node) -> tuple[str, str, int]:
        if node is not None and getattr(node, "is_hinged", False):
            return "", NODE_OUTLINE_COLOR, 2
        return NODE_FILL_COLOR, "", 1

    def _element_color(self, element_type: str) -> str:
        return MEMBER_COLOR if element_type == "frame" else MEMBER_TRUSS_COLOR

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
        tolerance = self.snap_tolerance / self.view_scale
        for node_id, node in self.builder.model.nodes.items():
            if math.hypot(x - node.x, y - node.y) <= tolerance:
                return node_id
        return None

    def _pan_view(self, canvas_x: float, canvas_y: float) -> None:
        if self._pan_last is None:
            return
        last_x, last_y = self._pan_last
        self.view_origin_x += canvas_x - last_x
        self.view_origin_y += canvas_y - last_y
        self._pan_last = (canvas_x, canvas_y)
        self.redraw_model()

    def _zoom(self, factor: float, focus_x: float | None = None, focus_y: float | None = None) -> None:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        center_x = width / 2 if focus_x is None else focus_x
        center_y = height / 2 if focus_y is None else focus_y
        model_x, model_y = self._canvas_to_model(center_x, center_y)
        self.view_scale = max(5.0, min(self.view_scale * factor, 400.0))
        self.view_origin_x = center_x - model_x * self.view_scale
        self.view_origin_y = center_y + model_y * self.view_scale
        self.redraw_model()

    def _canvas_to_model_point(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
        x, y = self._canvas_to_model(canvas_x, canvas_y)
        if self.snap_to_grid:
            return self._snap_model_point_to_grid(x, y)
        return x, y

    def _snap_model_point_to_grid(self, x: float, y: float) -> tuple[float, float]:
        spacing = self.grid_spacing
        return round(x / spacing) * spacing, round(y / spacing) * spacing

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


def _point_in_rect(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> bool:
    return x1 <= px <= x2 and y1 <= py <= y2


def _segment_intersects_rect(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> bool:
    if _point_in_rect(ax, ay, x1, y1, x2, y2) or _point_in_rect(bx, by, x1, y1, x2, y2):
        return True
    return any(
        _segments_intersect(ax, ay, bx, by, rx1, ry1, rx2, ry2)
        for rx1, ry1, rx2, ry2 in (
            (x1, y1, x2, y1),
            (x2, y1, x2, y2),
            (x2, y2, x1, y2),
            (x1, y2, x1, y1),
        )
    )


def _segments_intersect(
    ax: float,
    ay: float,
    bx: float,
    by: float,
    cx: float,
    cy: float,
    dx: float,
    dy: float,
) -> bool:
    def orientation(px, py, qx, qy, rx, ry):
        value = (qy - py) * (rx - qx) - (qx - px) * (ry - qy)
        if abs(value) < 1e-9:
            return 0
        return 1 if value > 0 else 2

    def on_segment(px, py, qx, qy, rx, ry):
        return min(px, rx) - 1e-9 <= qx <= max(px, rx) + 1e-9 and min(py, ry) - 1e-9 <= qy <= max(py, ry) + 1e-9

    o1 = orientation(ax, ay, bx, by, cx, cy)
    o2 = orientation(ax, ay, bx, by, dx, dy)
    o3 = orientation(cx, cy, dx, dy, ax, ay)
    o4 = orientation(cx, cy, dx, dy, bx, by)
    if o1 != o2 and o3 != o4:
        return True
    return (
        (o1 == 0 and on_segment(ax, ay, cx, cy, bx, by))
        or (o2 == 0 and on_segment(ax, ay, dx, dy, bx, by))
        or (o3 == 0 and on_segment(cx, cy, ax, ay, dx, dy))
        or (o4 == 0 and on_segment(cx, cy, bx, by, dx, dy))
    )


def _unit_vector(dx: float, dy: float) -> tuple[float, float] | None:
    length = math.hypot(dx, dy)
    if length == 0:
        return None
    return dx / length, dy / length


def _member_load_display_vector(
    load,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    component_1: float,
    component_2: float,
) -> tuple[float, float] | None:
    value = getattr(load, "value", None)
    direction = (getattr(load, "direction", "") or "").upper()
    coord_system = (getattr(load, "coord_system", "local") or "local").lower()
    if value is None or not direction:
        return _unit_vector(component_1, -component_2)

    sign = 1.0 if value >= 0 else -1.0
    if coord_system == "global":
        if direction == "X":
            return sign, 0.0
        if direction == "Y":
            return 0.0, -sign
    else:
        axis = _unit_vector(x2 - x1, y2 - y1)
        if axis is None:
            return None
        tx, ty = axis
        if direction == "1":
            return sign * tx, sign * ty
        if direction == "2":
            return sign * ty, -sign * tx
    return _unit_vector(component_1, -component_2)


def _member_load_label(prefix: str, load, component_1: float, component_2: float) -> str:
    value = getattr(load, "value", None)
    direction = getattr(load, "direction", "")
    coord_system = getattr(load, "coord_system", "local")
    if value is not None and direction:
        return f"{prefix}={_fmt_value(value)} {coord_system.title()}-{direction}"
    return f"{prefix}=({_fmt_value(component_1)}, {_fmt_value(component_2)})"


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
