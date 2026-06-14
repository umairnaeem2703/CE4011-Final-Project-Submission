"""Canvas geometry editor backed by ModelBuilder."""

from __future__ import annotations

import math
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk
from typing import Callable


StatusCallback = Callable[[str], None]


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

    def __init__(self, parent, *, status_callback: StatusCallback | None = None) -> None:
        super().__init__(parent, padding=4)
        self.status_callback = status_callback or (lambda message: None)

        ModelBuilder = _load_model_builder()
        self.builder = ModelBuilder(name="Desktop Model")
        self._ensure_placeholder_properties()

        self.active_tool = "Select"
        self.active_element_type = "frame"
        self.active_material_id = "M1"
        self.active_section_id = "S1"

        self.scale = 40.0
        self.grid_spacing = 40
        self.snap_tolerance = 12.0
        self.node_radius = 5
        self.next_node_id = 1
        self.next_element_number = 1
        self.pending_start_node_id: int | None = None

        self.item_to_node_id: dict[int, int] = {}
        self.node_id_to_item: dict[int, int] = {}
        self.item_to_element_id: dict[int, str] = {}
        self.element_id_to_item: dict[str, int] = {}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, background="white", highlightthickness=1, highlightbackground="#b8b8b8")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas.bind("<Configure>", lambda event: self._redraw_grid())
        self.canvas.bind("<Button-1>", self._handle_click)

    def load_builder(self, builder) -> None:
        self.builder = builder
        self.pending_start_node_id = None
        self.item_to_node_id.clear()
        self.node_id_to_item.clear()
        self.item_to_element_id.clear()
        self.element_id_to_item.clear()
        self.canvas.delete("all")
        self._redraw_grid()

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

        for node_id, node in self.builder.model.nodes.items():
            self._draw_node(node_id, node.x, node.y)
        for element_id, element in self.builder.model.elements.items():
            self._draw_element(element_id, element.node_i.id, element.node_j.id, element_type=element.type)

        self.status_callback(
            f"Loaded model with {len(self.builder.model.nodes)} nodes and {len(self.builder.model.elements)} elements."
        )

    def set_active_tool(self, tool_name: str) -> None:
        self.active_tool = tool_name
        if tool_name == "Draw Frame":
            self.active_element_type = "frame"
        elif tool_name == "Draw Truss":
            self.active_element_type = "truss"
        if tool_name not in ("Draw Frame", "Draw Truss"):
            self.pending_start_node_id = None

    def set_active_element_type(self, element_type: str) -> None:
        self.active_element_type = element_type
        if element_type == "frame":
            self.active_tool = "Draw Frame"
        elif element_type == "truss":
            self.active_tool = "Draw Truss"

    def set_active_material(self, material_id: str) -> None:
        self.active_material_id = material_id

    def set_active_section(self, section_id: str) -> None:
        self.active_section_id = section_id

    def add_node_by_coordinates(self, x: float, y: float) -> int:
        existing_node_id = self._find_node_near_model_point(x, y)
        if existing_node_id is not None:
            self._set_pending_or_report(existing_node_id)
            return existing_node_id

        node_id = self.next_node_id
        self.next_node_id += 1
        self.builder.add_node(node_id, x, y)
        self._draw_node(node_id, x, y)
        self.status_callback(f"Added node {node_id} at ({x:.3g}, {y:.3g}).")
        return node_id

    def draw_member_by_length_angle(self, length: float, angle_degrees: float) -> str | None:
        if self.pending_start_node_id is None:
            self.status_callback("Select a start node before entering length and angle.")
            return None

        start_node_id = self.pending_start_node_id
        start_node = self.builder.model.nodes[start_node_id]
        angle_radians = math.radians(angle_degrees)
        end_x = start_node.x + length * math.cos(angle_radians)
        end_y = start_node.y + length * math.sin(angle_radians)
        end_node_id = self.add_node_by_coordinates(end_x, end_y)
        return self._create_element(start_node_id, end_node_id)

    def _ensure_placeholder_properties(self) -> None:
        self.builder.add_material("M1", E=1.0)
        self.builder.add_section("S1", A=1.0, I=1.0)

    def _handle_click(self, event) -> None:
        x, y = self._canvas_to_model(event.x, event.y)
        snapped_node_id = self._find_node_near_canvas_point(event.x, event.y)

        if self.active_tool in ("Draw Frame", "Draw Truss"):
            node_id = snapped_node_id if snapped_node_id is not None else self.add_node_by_coordinates(x, y)
            self._set_pending_or_create_element(node_id)
        elif snapped_node_id is not None:
            self._set_pending_or_report(snapped_node_id)
        else:
            node_id = self.add_node_by_coordinates(x, y)
            self._set_pending_or_report(node_id)

    def _set_pending_or_create_element(self, node_id: int) -> None:
        if self.pending_start_node_id is None:
            self.pending_start_node_id = node_id
            self.status_callback(f"Start node {node_id} selected.")
            return

        if self.pending_start_node_id == node_id:
            self.status_callback(f"Start node {node_id} remains selected.")
            return

        self._create_element(self.pending_start_node_id, node_id)

    def _set_pending_or_report(self, node_id: int) -> None:
        self.pending_start_node_id = node_id
        self.status_callback(f"Node {node_id} selected.")

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
        self._draw_element(element_id, start_node_id, end_node_id, element_type=self.active_element_type)
        self.pending_start_node_id = end_node_id
        self.status_callback(f"Added {self.active_element_type} member {element_id}.")
        return element_id

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
        self.canvas.tag_lower(item_id, "node")
        self.item_to_element_id[item_id] = element_id
        self.element_id_to_item[element_id] = item_id

    def _redraw_grid(self) -> None:
        self.canvas.delete("grid")
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)

        origin_x = width / 2
        origin_y = height / 2
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
        self.canvas.tag_lower("grid")

    def _find_node_near_canvas_point(self, canvas_x: float, canvas_y: float) -> int | None:
        for node_id, item_id in self.node_id_to_item.items():
            x1, y1, x2, y2 = self.canvas.coords(item_id)
            node_x = (x1 + x2) / 2
            node_y = (y1 + y2) / 2
            if math.hypot(canvas_x - node_x, canvas_y - node_y) <= self.snap_tolerance:
                return node_id
        return None

    def _find_node_near_model_point(self, x: float, y: float) -> int | None:
        tolerance = self.snap_tolerance / self.scale
        for node_id, node in self.builder.model.nodes.items():
            if math.hypot(x - node.x, y - node.y) <= tolerance:
                return node_id
        return None

    def _model_to_canvas(self, x: float, y: float) -> tuple[float, float]:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        return width / 2 + x * self.scale, height / 2 - y * self.scale

    def _canvas_to_model(self, canvas_x: float, canvas_y: float) -> tuple[float, float]:
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        return (canvas_x - width / 2) / self.scale, (height / 2 - canvas_y) / self.scale


def _element_number(element_id: str) -> int:
    if element_id.startswith("E") and element_id[1:].isdigit():
        return int(element_id[1:])
    return 0
