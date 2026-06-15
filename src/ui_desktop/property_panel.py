"""Context-sensitive property panel for the desktop model builder."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .canvas import ModelCanvas
from .dialogs import LoadSettings, SupportSettings


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
        self.support_type_var = tk.StringVar(value="fixed")
        self.restrain_ux_var = tk.BooleanVar(value=True)
        self.restrain_uy_var = tk.BooleanVar(value=True)
        self.restrain_rz_var = tk.BooleanVar(value=True)
        self.settlement_ux_var = tk.StringVar(value="0.0")
        self.settlement_uy_var = tk.StringVar(value="0.0")
        self.settlement_rz_var = tk.StringVar(value="0.0")
        self.load_target_var = tk.StringVar(value="Node")
        self.load_type_var = tk.StringVar(value="Nodal Force/Moment")
        self.load_case_var = tk.StringVar(value="LC1")
        self.fx_var = tk.StringVar(value="0.0")
        self.fy_var = tk.StringVar(value="0.0")
        self.mz_var = tk.StringVar(value="0.0")
        self.wx_var = tk.StringVar(value="0.0")
        self.wy_var = tk.StringVar(value="0.0")
        self.position_var = tk.StringVar(value="0.5")

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
            self._load_panel()
        elif command == "Assign Support":
            self._support_panel()
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
            support = self.model_canvas.builder.model.supports.get(node.id)
            support_text = _support_summary(support)
            loads_text = _node_load_summary(self.model_canvas.builder.model, node.id)
            rows = [
                ("Node id", node.id),
                ("x", f"{node.x:.6g}"),
                ("y", f"{node.y:.6g}"),
                ("Support", support_text),
                ("Mass", "placeholder"),
                ("Loads", loads_text),
            ]
        elif self.selected_kind == "element" and self.selected_object is not None:
            element = self.selected_object
            loads_text = _member_load_summary(self.model_canvas.builder.model, element.id)
            rows = [
                ("Element id", element.id),
                ("Type", element.type),
                ("Node i", element.node_i.id),
                ("Node j", element.node_j.id),
                ("Material", element.material.id),
                ("Section", element.section.id),
                ("Loads", loads_text),
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

    def _support_panel(self) -> None:
        self._title("Assign Support")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        self._combo(form, 0, "Type", self.support_type_var, ("fixed", "pin", "roller_x", "roller_y", "custom"), self._sync_support_type)
        ttk.Checkbutton(form, text="ux", variable=self.restrain_ux_var).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(form, text="uy", variable=self.restrain_uy_var).grid(row=1, column=1, sticky="w")
        ttk.Checkbutton(form, text="rz", variable=self.restrain_rz_var).grid(row=1, column=2, sticky="w")
        ttk.Label(form, text="set ux").grid(row=2, column=0, sticky="w", pady=(8, 2))
        ttk.Entry(form, textvariable=self.settlement_ux_var, width=10).grid(row=2, column=1, sticky="ew", pady=(8, 2))
        ttk.Label(form, text="set uy").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.settlement_uy_var, width=10).grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="set rz").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.settlement_rz_var, width=10).grid(row=4, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Use These Settings", command=self._apply_support_settings).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(self, text="Click a node on the canvas to assign support.", wraplength=220).grid(row=3, column=0, sticky="nw", pady=(8, 0))
        self._sync_support_type()

    def _load_panel(self) -> None:
        self._title("Assign Load")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        self._combo(form, 0, "Target", self.load_target_var, ("Node", "Member"), self._sync_load_target)
        self._combo(form, 1, "Type", self.load_type_var, ("Nodal Force/Moment", "UDL", "Point Load"), self._apply_load_settings)
        ttk.Label(form, text="Case").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.load_case_var, width=10).grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="Fx / wx").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.fx_var, width=10).grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="Fy / wy").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.fy_var, width=10).grid(row=4, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="Mz").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.mz_var, width=10).grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="a/L").grid(row=6, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.position_var, width=10).grid(row=6, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Use These Settings", command=self._apply_load_settings).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(self, text="Click the selected target type on the canvas.", wraplength=220).grid(row=3, column=0, sticky="nw", pady=(8, 0))
        self._sync_load_target()

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

    def _sync_support_type(self) -> None:
        support_type = self.support_type_var.get()
        if support_type == "fixed":
            values = (True, True, True)
        elif support_type == "pin":
            values = (True, True, False)
        elif support_type == "roller_x":
            values = (False, True, False)
        elif support_type == "roller_y":
            values = (True, False, False)
        else:
            values = (self.restrain_ux_var.get(), self.restrain_uy_var.get(), self.restrain_rz_var.get())
        self.restrain_ux_var.set(values[0])
        self.restrain_uy_var.set(values[1])
        self.restrain_rz_var.set(values[2])
        self._apply_support_settings()

    def _apply_support_settings(self) -> None:
        try:
            settlement_ux = float(self.settlement_ux_var.get())
            settlement_uy = float(self.settlement_uy_var.get())
            settlement_rz = float(self.settlement_rz_var.get())
        except ValueError:
            self.status_callback("Assign Support: settlement values must be numeric.")
            return
        self.model_canvas.set_support_settings(
            SupportSettings(
                support_type=self.support_type_var.get(),
                restrain_ux=self.restrain_ux_var.get(),
                restrain_uy=self.restrain_uy_var.get(),
                restrain_rz=self.restrain_rz_var.get(),
                settlement_ux=settlement_ux,
                settlement_uy=settlement_uy,
                settlement_rz=settlement_rz,
            )
        )
        self.status_callback("Assign Support: click a node.")

    def _sync_load_target(self) -> None:
        if self.load_target_var.get() == "Node":
            self.load_type_var.set("Nodal Force/Moment")
        elif self.load_type_var.get() == "Nodal Force/Moment":
            self.load_type_var.set("UDL")
        self._apply_load_settings()

    def _apply_load_settings(self) -> None:
        try:
            fx = float(self.fx_var.get())
            fy = float(self.fy_var.get())
            mz = float(self.mz_var.get())
            position = float(self.position_var.get())
        except ValueError:
            self.status_callback("Assign Load: numeric fields are required.")
            return
        if not 0.0 <= position <= 1.0:
            self.status_callback("Assign Load: a/L must be between 0 and 1.")
            return
        target = self.load_target_var.get()
        load_type = self.load_type_var.get()
        self.model_canvas.set_load_settings(
            LoadSettings(
                target=target,
                load_type=load_type,
                load_case=self.load_case_var.get().strip() or "LC1",
                fx=fx,
                fy=fy,
                mz=mz,
                wx=fx,
                wy=fy,
                position=position,
            )
        )
        self.status_callback("Assign Load: click a node." if target == "Node" else "Assign Load: click a member.")

    def _material_ids(self) -> tuple[str, ...]:
        return tuple(self.model_canvas.builder.model.materials.keys()) or ("M1",)

    def _section_ids(self) -> tuple[str, ...]:
        return tuple(self.model_canvas.builder.model.sections.keys()) or ("S1",)

    def _clear(self) -> None:
        for child in self.winfo_children():
            child.destroy()


def _support_summary(support) -> str:
    if support is None:
        return "none"
    restraints = "".join(
        dof
        for dof, active in (
            ("ux ", support.restrain_ux),
            ("uy ", support.restrain_uy),
            ("rz ", support.restrain_rz),
        )
        if active
    ).strip() or "free"
    settlements = (support.settlement_ux, support.settlement_uy, support.settlement_rz)
    if any(settlements):
        return f"{restraints}; settlement=({settlements[0]:.3g}, {settlements[1]:.3g}, {settlements[2]:.3g})"
    return restraints


def _node_load_summary(model, node_id: int) -> str:
    labels = []
    for load_case in model.load_cases.values():
        for load in load_case.loads:
            if hasattr(load, "node") and load.node.id == node_id:
                labels.append(f"{load_case.id}: Fx={load.fx:.3g}, Fy={load.fy:.3g}, Mz={load.mz:.3g}")
    return "; ".join(labels) if labels else "none"


def _member_load_summary(model, element_id: str) -> str:
    labels = []
    for load_case in model.load_cases.values():
        for load in load_case.loads:
            if not hasattr(load, "element") or load.element.id != element_id:
                continue
            if load.__class__.__name__ == "UniformlyDL":
                labels.append(f"{load_case.id}: UDL wx={load.wx:.3g}, wy={load.wy:.3g}")
            elif load.__class__.__name__ == "PointLoad":
                labels.append(f"{load_case.id}: Point a/L={load.position:.3g}, Fx={load.fx:.3g}, Fy={load.fy:.3g}")
    return "; ".join(labels) if labels else "none"
