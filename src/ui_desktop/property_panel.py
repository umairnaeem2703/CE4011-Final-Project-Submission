"""Context-sensitive property panel for the desktop model builder."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .canvas import ModelCanvas


class PropertyPanel(ttk.LabelFrame):
    """Right-side context panel for commands and selection inspection."""

    def __init__(self, parent, model_canvas: ModelCanvas, *, status_callback=None) -> None:
        super().__init__(parent, text="Properties / Settings", padding=8)
        self.model_canvas = model_canvas
        self.status_callback = status_callback or (lambda message: None)
        self.current_command = "Select / Inspect"
        self.selected_kind = None
        self.selected_object = None

        self.x_var = tk.StringVar(value="0.0")
        self.y_var = tk.StringVar(value="0.0")
        self.length_var = tk.StringVar(value="1.0")
        self.angle_var = tk.StringVar(value="0.0")
        self.element_type_var = tk.StringVar(value="frame")
        self.material_var = tk.StringVar(value="M1")
        self.section_var = tk.StringVar(value="S1")
        self.draw_mode_var = tk.StringVar(value="Click end node")

        self.columnconfigure(0, weight=1)
        self.show_command("Select / Inspect")

    def show_command(self, command: str) -> None:
        self.current_command = command
        self._clear()
        if command == "Draw Node":
            self._draw_node_panel()
        elif command == "Draw Member":
            self._draw_member_panel()
        elif command == "Select / Inspect":
            self._inspect_panel()
        elif command == "Assign Load":
            self._placeholder_panel("Assign Load", "Load target/type controls will be added in Task 4.")
        elif command == "Assign Support":
            self._placeholder_panel("Assign Support", "Support assignment controls will be added in Task 4.")
        elif command == "Assign Mass":
            self._placeholder_panel("Assign Mass", "Mass assignment controls will be added in Task 4.")
        elif command == "Assign Diaphragm":
            self._placeholder_panel("Assign Diaphragm", "Diaphragm assignment controls will be added in Task 4.")
        elif command == "Delete":
            self._placeholder_panel("Delete", "Click a node or member on the canvas to delete it.")
        else:
            self._placeholder_panel(command, "No settings for this command yet.")

    def show_selection(self, kind: str | None, obj: object | None) -> None:
        self.selected_kind = kind
        self.selected_object = obj
        if self.current_command == "Select / Inspect":
            self.show_command("Select / Inspect")

    def sync_from_canvas(self) -> None:
        self.material_var.set(self.model_canvas.active_material_id)
        self.section_var.set(self.model_canvas.active_section_id)
        self.element_type_var.set(self.model_canvas.active_element_type)

    def _draw_node_panel(self) -> None:
        self._title("Draw Node")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="x").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.x_var, width=12).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="y").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.y_var, width=12).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Add Node", command=self._add_node).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def _draw_member_panel(self) -> None:
        self._title("Draw Member")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)

        self._combo(form, 0, "Type", self.element_type_var, ("frame", "truss"), self._set_member_settings)
        self._combo(form, 1, "Material", self.material_var, self._material_ids(), self._set_member_settings)
        self._combo(form, 2, "Section", self.section_var, self._section_ids(), self._set_member_settings)
        self._combo(form, 3, "Draw mode", self.draw_mode_var, ("Click end node", "Length + angle"), self._set_draw_mode)

        ttk.Label(form, text="Length").grid(row=4, column=0, sticky="w", pady=(10, 2))
        ttk.Entry(form, textvariable=self.length_var, width=12).grid(row=4, column=1, sticky="ew", pady=(10, 2))
        ttk.Label(form, text="Angle").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.angle_var, width=12).grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Draw From Start", command=self._draw_member).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def _inspect_panel(self) -> None:
        self._title("Select / Inspect")
        if self.selected_kind == "node" and self.selected_object is not None:
            node = self.selected_object
            rows = [
                ("Node id", node.id),
                ("x", f"{node.x:.6g}"),
                ("y", f"{node.y:.6g}"),
                ("Support", "placeholder"),
                ("Mass", "placeholder"),
                ("Loads", "placeholder"),
            ]
        elif self.selected_kind == "element" and self.selected_object is not None:
            element = self.selected_object
            rows = [
                ("Element id", element.id),
                ("Type", element.type),
                ("Node i", element.node_i.id),
                ("Node j", element.node_j.id),
                ("Material", element.material.id),
                ("Section", element.section.id),
                ("Loads", "placeholder"),
            ]
        else:
            rows = [("Selection", "Click a node or member.")]

        info = ttk.Frame(self)
        info.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        info.columnconfigure(1, weight=1)
        for row, (label, value) in enumerate(rows):
            ttk.Label(info, text=label).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Label(info, text=str(value)).grid(row=row, column=1, sticky="w", pady=2)

    def _placeholder_panel(self, title: str, text: str) -> None:
        self._title(title)
        ttk.Label(self, text=text, wraplength=220).grid(row=1, column=0, sticky="nw", pady=(8, 0))

    def _title(self, text: str) -> None:
        ttk.Label(self, text=text, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w")

    def _combo(self, parent, row: int, label: str, variable, values, callback) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        combo = ttk.Combobox(parent, textvariable=variable, values=tuple(values), state="readonly", width=14)
        combo.grid(row=row, column=1, sticky="ew", pady=2)
        combo.bind("<<ComboboxSelected>>", lambda event: callback())

    def _add_node(self) -> None:
        try:
            x = float(self.x_var.get())
            y = float(self.y_var.get())
        except ValueError:
            self.status_callback("Draw Node: enter numeric x and y values.")
            return
        self.model_canvas.add_node_by_coordinates(x, y)

    def _draw_member(self) -> None:
        try:
            length = float(self.length_var.get())
            angle = float(self.angle_var.get())
        except ValueError:
            self.status_callback("Draw Member: enter numeric length and angle values.")
            return
        if length <= 0:
            self.status_callback("Draw Member: length must be positive.")
            return
        self._set_member_settings()
        self.model_canvas.draw_member_by_length_angle(length, angle)

    def _set_member_settings(self) -> None:
        self.model_canvas.set_active_element_type(self.element_type_var.get())
        self.model_canvas.set_active_material(self.material_var.get())
        self.model_canvas.set_active_section(self.section_var.get())
        self.status_callback(f"Draw Member: using {self.element_type_var.get()} members.")

    def _set_draw_mode(self) -> None:
        mode = "length_angle" if self.draw_mode_var.get() == "Length + angle" else "click"
        self.model_canvas.set_draw_mode(mode)
        self.status_callback(self.model_canvas.command_instruction())

    def _material_ids(self) -> tuple[str, ...]:
        return tuple(self.model_canvas.builder.model.materials.keys()) or ("M1",)

    def _section_ids(self) -> tuple[str, ...]:
        return tuple(self.model_canvas.builder.model.sections.keys()) or ("S1",)

    def _clear(self) -> None:
        for child in self.winfo_children():
            child.destroy()
