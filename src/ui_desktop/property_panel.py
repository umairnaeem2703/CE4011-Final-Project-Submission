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
        self.material_id_var = tk.StringVar(value="M1")
        self.material_type_var = tk.StringVar(value="Generic")
        self.material_e_var = tk.StringVar(value="1.0")
        self.material_alpha_var = tk.StringVar(value="0.0")
        self.material_density_var = tk.StringVar(value="0.0")
        self.section_input_mode_var = tk.StringVar(value="Geometric")
        self.section_id_var = tk.StringVar(value="S1")
        self.section_a_var = tk.StringVar(value="1.0")
        self.section_i_var = tk.StringVar(value="1.0")
        self.section_d_var = tk.StringVar(value="0.0")
        self.section_ea_var = tk.StringVar(value="")
        self.section_ei_var = tk.StringVar(value="")
        self.draw_mode_var = tk.StringVar(value="Click end node")
        self.support_type_var = tk.StringVar(value="fixed")
        self.restrain_ux_var = tk.BooleanVar(value=True)
        self.restrain_uy_var = tk.BooleanVar(value=True)
        self.restrain_rz_var = tk.BooleanVar(value=True)
        self.support_action_var = tk.StringVar(value="Replace")
        self.settlement_ux_var = tk.StringVar(value="0.0")
        self.settlement_uy_var = tk.StringVar(value="0.0")
        self.settlement_rz_var = tk.StringVar(value="0.0")
        self.load_action_var = tk.StringVar(value="Add")
        self.load_target_var = tk.StringVar(value="Node")
        self.load_type_var = tk.StringVar(value="Nodal Load")
        self.load_case_var = tk.StringVar(value="LC1")
        self.fx_var = tk.StringVar(value="0.0")
        self.fy_var = tk.StringVar(value="0.0")
        self.mz_var = tk.StringVar(value="0.0")
        self.wx_var = tk.StringVar(value="0.0")
        self.wy_var = tk.StringVar(value="0.0")
        self.load_coordinate_system_var = tk.StringVar(value="Member Local Axis")
        self.point_direction_var = tk.StringVar(value="Y")
        self.point_magnitude_var = tk.StringVar(value="0.0")
        self.position_var = tk.StringVar(value="0.5")
        self.temperature_tu_var = tk.StringVar(value="0.0")
        self.temperature_tb_var = tk.StringVar(value="0.0")
        self.mass_action_var = tk.StringVar(value="Replace")
        self.mass_ux_var = tk.StringVar(value="0.0")
        self.mass_uy_var = tk.StringVar(value="0.0")
        self.mass_rz_var = tk.StringVar(value="0.0")
        self._section_geometric_widgets = []
        self._section_direct_widgets = []

        self.columnconfigure(0, weight=1)
        self.show_command("Select / Inspect")

    def show_command(self, command: str) -> None:
        self.current_command = command
        self._clear()
        if command == "Draw Node":
            self._draw_node_panel()
        elif command == "Draw Member":
            self._draw_member_panel()
        elif command == "Materials / Sections":
            self._materials_sections_panel()
        elif command == "Select / Inspect":
            self._inspect_panel()
        elif command == "Assign Load":
            self._load_panel()
        elif command == "Assign Support":
            self._support_panel()
        elif command == "Assign Mass":
            self._mass_panel()
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
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

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
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

    def _inspect_panel(self) -> None:
        self._title("Select / Inspect")
        if self.selected_kind == "node" and self.selected_object is not None:
            node = self.selected_object
            support = self.model_canvas.builder.model.supports.get(node.id)
            support_text = _support_summary(support)
            mass_text = _mass_summary(self.model_canvas.builder.model, node.id)
            loads_text = _node_load_summary(self.model_canvas.builder.model, node.id)
            rows = [
                ("Node id", node.id),
                ("x", f"{node.x:.6g}"),
                ("y", f"{node.y:.6g}"),
                ("Support", support_text),
                ("Mass", mass_text),
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
                ("Section", _section_summary(element.section)),
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
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )

    def _materials_sections_panel(self) -> None:
        self._title("Materials / Sections")

        material = ttk.LabelFrame(self, text="Material", padding=6)
        material.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        material.columnconfigure(1, weight=1)
        ttk.Label(material, text="id/name").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(material, textvariable=self.material_id_var, width=12).grid(row=0, column=1, sticky="ew", pady=2)
        self._combo(material, 1, "Type", self.material_type_var, ("Generic", "Steel", "Concrete"), lambda: None)
        ttk.Label(material, text="E").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(material, textvariable=self.material_e_var, width=12).grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(material, text="alpha").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(material, textvariable=self.material_alpha_var, width=12).grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Label(material, text="density").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Entry(material, textvariable=self.material_density_var, width=12).grid(row=4, column=1, sticky="ew", pady=2)
        ttk.Button(material, text="Add / Update Material", command=self._add_material).grid(
            row=5,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )

        section = ttk.LabelFrame(self, text="Section", padding=6)
        section.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        section.columnconfigure(1, weight=1)
        ttk.Label(section, text="id/name").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(section, textvariable=self.section_id_var, width=12).grid(row=0, column=1, sticky="ew", pady=2)
        self._combo(
            section,
            1,
            "Input mode",
            self.section_input_mode_var,
            ("Geometric", "Direct Stiffness"),
            self._sync_section_input_mode,
        )
        a_label = ttk.Label(section, text="A")
        a_entry = ttk.Entry(section, textvariable=self.section_a_var, width=12)
        i_label = ttk.Label(section, text="I")
        i_entry = ttk.Entry(section, textvariable=self.section_i_var, width=12)
        d_label = ttk.Label(section, text="d/depth")
        d_entry = ttk.Entry(section, textvariable=self.section_d_var, width=12)
        ea_label = ttk.Label(section, text="EA direct stiffness")
        ea_entry = ttk.Entry(section, textvariable=self.section_ea_var, width=12)
        ei_label = ttk.Label(section, text="EI direct stiffness")
        ei_entry = ttk.Entry(section, textvariable=self.section_ei_var, width=12)
        thermal_d_label = ttk.Label(section, text="Thermal depth d")
        thermal_d_entry = ttk.Entry(section, textvariable=self.section_d_var, width=12)
        direct_note = ttk.Label(
            section,
            text="Material E is ignored for stiffness; material may still provide alpha/density.",
            wraplength=210,
        )
        for row, (label, entry) in enumerate(
            ((a_label, a_entry), (i_label, i_entry), (d_label, d_entry), (ea_label, ea_entry), (ei_label, ei_entry)),
            start=2,
        ):
            label.grid(row=row, column=0, sticky="w", pady=2)
            entry.grid(row=row, column=1, sticky="ew", pady=2)
        thermal_d_label.grid(row=7, column=0, sticky="w", pady=2)
        thermal_d_entry.grid(row=7, column=1, sticky="ew", pady=2)
        direct_note.grid(row=8, column=0, columnspan=2, sticky="w", pady=(4, 2))
        self._section_geometric_widgets = [a_label, a_entry, i_label, i_entry, d_label, d_entry]
        self._section_direct_widgets = [ea_label, ea_entry, ei_label, ei_entry, thermal_d_label, thermal_d_entry, direct_note]
        ttk.Button(section, text="Add / Update Section", command=self._add_section).grid(
            row=9,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )
        ttk.Button(section, text="Reset to Default", command=self._reset_current_command).grid(
            row=10,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )
        self._sync_section_input_mode()

    def _support_panel(self) -> None:
        self._title("Assign Support")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        self._combo(form, 0, "Action", self.support_action_var, ("Add", "Replace", "Delete"), self._apply_support_settings)
        self._combo(form, 1, "Type", self.support_type_var, ("fixed", "pin", "roller_x", "roller_y", "custom"), self._sync_support_type)
        ttk.Checkbutton(form, text="ux", variable=self.restrain_ux_var).grid(row=2, column=0, sticky="w")
        ttk.Checkbutton(form, text="uy", variable=self.restrain_uy_var).grid(row=2, column=1, sticky="w")
        ttk.Checkbutton(form, text="rz", variable=self.restrain_rz_var).grid(row=2, column=2, sticky="w")
        ttk.Label(form, text="set ux").grid(row=3, column=0, sticky="w", pady=(8, 2))
        ttk.Entry(form, textvariable=self.settlement_ux_var, width=10).grid(row=3, column=1, sticky="ew", pady=(8, 2))
        ttk.Label(form, text="set uy").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.settlement_uy_var, width=10).grid(row=4, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="set rz").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.settlement_rz_var, width=10).grid(row=5, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Use These Settings", command=self._apply_support_settings).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(self, text="Click a node on the canvas to assign support.", wraplength=220).grid(row=3, column=0, sticky="nw", pady=(8, 0))
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self._sync_support_type()

    def _load_panel(self) -> None:
        self._title("Assign Load")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        if self.load_target_var.get() == "Node" and self.load_type_var.get() not in ("Nodal Load", "Nodal Moment"):
            self.load_type_var.set("Nodal Load")
        elif self.load_target_var.get() == "Member" and self.load_type_var.get() not in (
            "Uniformly Distributed Load",
            "Point Load",
            "Temperature",
        ):
            self.load_type_var.set("Uniformly Distributed Load")
        self._combo(form, 0, "Target", self.load_target_var, ("Node", "Member"), self._sync_load_target)
        self._combo(form, 1, "Action", self.load_action_var, ("Add", "Replace", "Delete"), self._apply_load_settings)
        target = self.load_target_var.get()
        load_type = self.load_type_var.get()
        if target == "Node":
            self._combo(form, 2, "Type", self.load_type_var, ("Nodal Load", "Nodal Moment"), self._reload_load_panel)
            ttk.Label(form, text="Case").grid(row=3, column=0, sticky="w", pady=2)
            ttk.Entry(form, textvariable=self.load_case_var, width=10).grid(row=3, column=1, sticky="ew", pady=2)
            if load_type == "Nodal Moment":
                ttk.Label(form, text="Mz").grid(row=4, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.mz_var, width=10).grid(row=4, column=1, sticky="ew", pady=2)
            else:
                ttk.Label(form, text="Fx").grid(row=4, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.fx_var, width=10).grid(row=4, column=1, sticky="ew", pady=2)
                ttk.Label(form, text="Fy").grid(row=5, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.fy_var, width=10).grid(row=5, column=1, sticky="ew", pady=2)
        else:
            self._combo(
                form,
                2,
                "Type",
                self.load_type_var,
                ("Uniformly Distributed Load", "Point Load", "Temperature"),
                self._reload_load_panel,
            )
            if load_type != "Temperature":
                self._combo(
                    form,
                    3,
                    "Coordinate System",
                    self.load_coordinate_system_var,
                    ("Member Local Axis", "Global Axis"),
                    self._apply_load_settings,
                )
            ttk.Label(form, text="Case").grid(row=4, column=0, sticky="w", pady=2)
            ttk.Entry(form, textvariable=self.load_case_var, width=10).grid(row=4, column=1, sticky="ew", pady=2)
            if load_type == "Point Load":
                self._combo(form, 5, "Direction", self.point_direction_var, ("X", "Y"), self._apply_load_settings)
                ttk.Label(form, text="P").grid(row=6, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.point_magnitude_var, width=10).grid(row=6, column=1, sticky="ew", pady=2)
                ttk.Label(form, text="Position a/L").grid(row=7, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.position_var, width=10).grid(row=7, column=1, sticky="ew", pady=2)
            elif load_type == "Temperature":
                ttk.Label(form, text="Tu").grid(row=5, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.temperature_tu_var, width=10).grid(row=5, column=1, sticky="ew", pady=2)
                ttk.Label(form, text="Tb").grid(row=6, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.temperature_tb_var, width=10).grid(row=6, column=1, sticky="ew", pady=2)
            else:
                ttk.Label(form, text="wx").grid(row=5, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.wx_var, width=10).grid(row=5, column=1, sticky="ew", pady=2)
                ttk.Label(form, text="wy").grid(row=6, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.wy_var, width=10).grid(row=6, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Use These Settings", command=self._apply_load_settings).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(self, text="Click the selected target type on the canvas.", wraplength=220).grid(row=3, column=0, sticky="nw", pady=(8, 0))
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self._apply_load_settings()

    def _mass_panel(self) -> None:
        self._title("Assign Mass")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        self._combo(form, 0, "Action", self.mass_action_var, ("Add", "Replace", "Delete"), self._apply_mass_settings)
        ttk.Label(form, text="mass_ux").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.mass_ux_var, width=10).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="mass_uy").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.mass_uy_var, width=10).grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="mass_rz").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.mass_rz_var, width=10).grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Button(self, text="Use These Settings", command=self._apply_mass_settings).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(self, text="Click a node on the canvas to assign mass.", wraplength=220).grid(row=3, column=0, sticky="nw", pady=(8, 0))
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(row=4, column=0, sticky="ew", pady=(8, 0))
        self._apply_mass_settings()

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

    def _sync_section_input_mode(self) -> None:
        geometric = self.section_input_mode_var.get() == "Geometric"
        for widget in self._section_geometric_widgets:
            if geometric:
                widget.grid()
            else:
                widget.grid_remove()
        for widget in self._section_direct_widgets:
            if geometric:
                widget.grid_remove()
            else:
                widget.grid()

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
        self.model_canvas.set_support_action(self.support_action_var.get())
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
        target = self.load_target_var.get()
        if target == "Node" and self.load_type_var.get() not in ("Nodal Load", "Nodal Moment"):
            self.load_type_var.set("Nodal Load")
        elif target == "Member" and self.load_type_var.get() not in (
            "Uniformly Distributed Load",
            "Point Load",
            "Temperature",
        ):
            self.load_type_var.set("Uniformly Distributed Load")
        self._reload_load_panel()

    def _reload_load_panel(self) -> None:
        if self.current_command == "Assign Load":
            self.show_command("Assign Load")
        else:
            self._apply_load_settings()

    def _apply_load_settings(self) -> None:
        target = self.load_target_var.get()
        load_type = self.load_type_var.get()
        fx = fy = mz = wx = wy = 0.0
        position = 0.5
        backend_load_type = load_type
        try:
            if target == "Node" and load_type == "Nodal Moment":
                mz = float(self.mz_var.get())
            elif target == "Node":
                fx = float(self.fx_var.get())
                fy = float(self.fy_var.get())
            elif load_type == "Point Load":
                magnitude = float(self.point_magnitude_var.get())
                position = float(self.position_var.get())
                if self.point_direction_var.get() == "X":
                    fx = magnitude
                else:
                    fy = magnitude
                backend_load_type = "Point Load"
            elif load_type == "Temperature":
                wx = float(self.temperature_tu_var.get())
                wy = float(self.temperature_tb_var.get())
                backend_load_type = "Temperature"
            else:
                wx = float(self.wx_var.get())
                wy = float(self.wy_var.get())
                backend_load_type = "UDL"
        except ValueError:
            self.status_callback("Assign Load: numeric fields are required.")
            return
        if target == "Member" and load_type == "Point Load" and not 0.0 <= position <= 1.0:
            self.status_callback("Assign Load: a/L must be between 0 and 1.")
            return
        self.model_canvas.set_load_action(self.load_action_var.get())
        self.model_canvas.set_load_settings(
            LoadSettings(
                target=target,
                load_type=backend_load_type,
                load_case=self.load_case_var.get().strip() or "LC1",
                fx=fx,
                fy=fy,
                mz=mz,
                wx=wx,
                wy=wy,
                position=position,
            )
        )
        self.status_callback("Assign Load: click a node." if target == "Node" else "Assign Load: click a member.")

    def _apply_mass_settings(self) -> None:
        try:
            mass_ux = float(self.mass_ux_var.get())
            mass_uy = float(self.mass_uy_var.get())
            inertia_rz = float(self.mass_rz_var.get())
        except ValueError:
            self.status_callback("Assign Mass: mass values must be numeric.")
            return
        self.model_canvas.set_mass_settings(self.mass_action_var.get(), mass_ux, mass_uy, inertia_rz)
        self.status_callback("Assign Mass: click a node.")

    def _add_material(self) -> None:
        material_id = self.material_id_var.get().strip()
        if not material_id:
            self.status_callback("Material: id/name is required.")
            return
        try:
            E = float(self.material_e_var.get())
            alpha = float(self.material_alpha_var.get())
            density = float(self.material_density_var.get())
        except ValueError:
            self.status_callback("Material: E, alpha, and density must be numeric.")
            return
        self.model_canvas.builder.add_material(material_id, E=E, alpha=alpha, density=density)
        self.material_var.set(material_id)
        self.model_canvas.set_active_material(material_id)
        self.model_canvas.change_callback()
        self.status_callback(f"Material {material_id} saved.")

    def _add_section(self) -> None:
        section_id = self.section_id_var.get().strip()
        if not section_id:
            self.status_callback("Section: id/name is required.")
            return
        if self.section_input_mode_var.get() == "Geometric":
            try:
                A = _required_float(self.section_a_var.get(), "A")
                I = _required_float(self.section_i_var.get(), "I")
                d = _optional_float(self.section_d_var.get()) or 0.0
            except ValueError as exc:
                self.status_callback(f"Section: {exc}")
                return
            EA = EI = None
        else:
            try:
                EA = _required_float(self.section_ea_var.get(), "EA")
                EI = _required_float(self.section_ei_var.get(), "EI")
                d = _optional_float(self.section_d_var.get()) or 0.0
            except ValueError as exc:
                self.status_callback(f"Section: {exc}")
                return
            A = I = 0.0
        self.model_canvas.builder.add_section(section_id, A=A, I=I, d=d, EA=EA, EI=EI)
        self.section_var.set(section_id)
        self.model_canvas.set_active_section(section_id)
        self.model_canvas.change_callback()
        self.status_callback(f"Section {section_id} saved.")

    def _reset_current_command(self) -> None:
        command = self.current_command
        if command == "Draw Node":
            self.x_var.set("0.0")
            self.y_var.set("0.0")
        elif command == "Draw Member":
            self.element_type_var.set("frame")
            self.material_var.set(next(iter(self.model_canvas.builder.model.materials), "M1"))
            self.section_var.set(next(iter(self.model_canvas.builder.model.sections), "S1"))
            self.draw_mode_var.set("Click end node")
            self.length_var.set("1.0")
            self.angle_var.set("0.0")
            self._set_member_settings()
            self._set_draw_mode()
        elif command == "Materials / Sections":
            self.material_id_var.set("M1")
            self.material_type_var.set("Generic")
            self.material_e_var.set("1.0")
            self.material_alpha_var.set("0.0")
            self.material_density_var.set("0.0")
            self.section_input_mode_var.set("Geometric")
            self.section_id_var.set("S1")
            self.section_a_var.set("1.0")
            self.section_i_var.set("1.0")
            self.section_d_var.set("0.0")
            self.section_ea_var.set("")
            self.section_ei_var.set("")
            self._sync_section_input_mode()
        elif command == "Assign Support":
            self.support_action_var.set("Replace")
            self.support_type_var.set("fixed")
            self.restrain_ux_var.set(True)
            self.restrain_uy_var.set(True)
            self.restrain_rz_var.set(True)
            self.settlement_ux_var.set("0.0")
            self.settlement_uy_var.set("0.0")
            self.settlement_rz_var.set("0.0")
            self._apply_support_settings()
        elif command == "Assign Load":
            self.load_action_var.set("Add")
            self.load_target_var.set("Node")
            self.load_type_var.set("Nodal Load")
            self.load_case_var.set("LC1")
            self.fx_var.set("0.0")
            self.fy_var.set("0.0")
            self.mz_var.set("0.0")
            self.wx_var.set("0.0")
            self.wy_var.set("0.0")
            self.load_coordinate_system_var.set("Member Local Axis")
            self.point_direction_var.set("Y")
            self.point_magnitude_var.set("0.0")
            self.position_var.set("0.5")
            self.temperature_tu_var.set("0.0")
            self.temperature_tb_var.set("0.0")
            self._reload_load_panel()
        elif command == "Assign Mass":
            self.mass_action_var.set("Replace")
            self.mass_ux_var.set("0.0")
            self.mass_uy_var.set("0.0")
            self.mass_rz_var.set("0.0")
            self._apply_mass_settings()
        self.status_callback(f"{command}: settings reset to defaults.")

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


def _mass_summary(model, node_id: int) -> str:
    mass = model.lumped_masses.get(node_id)
    if mass is None:
        return "none"
    if isinstance(mass, (int, float)):
        return f"mass_ux={mass:.3g}, mass_uy={mass:.3g}, mass_rz=0"
    return (
        f"mass_ux={mass.mass_ux:.3g}, "
        f"mass_uy={mass.mass_uy:.3g}, "
        f"mass_rz={mass.inertia_rz:.3g}"
    )


def _section_summary(section) -> str:
    if _is_direct_stiffness_section(section):
        parts = [
            "EA/EI direct",
            f"EA={_format_optional(section.EA)}",
            f"EI={_format_optional(section.EI)}",
            f"thermal d={section.d:.3g}" if section.d else "thermal d=unset",
            "ignores material E for stiffness",
        ]
    else:
        parts = ["Geometric", f"A={section.A:.3g}", f"I={section.I:.3g}", f"d={section.d:.3g}"]
    return f"{section.id} ({', '.join(parts)})"


def _optional_float(value: str) -> float | None:
    text = value.strip()
    return None if not text else float(text)


def _required_float(value: str, label: str) -> float:
    text = value.strip()
    if not text:
        raise ValueError(f"{label} is required.")
    return float(text)


def _is_direct_stiffness_section(section) -> bool:
    return getattr(section, "EA", None) is not None or getattr(section, "EI", None) is not None


def _format_optional(value) -> str:
    return "unset" if value is None else f"{value:.3g}"


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
            elif load.__class__.__name__ == "TemperatureL":
                labels.append(f"{load_case.id}: Temperature Tu={load.Tu:.3g}, Tb={load.Tb:.3g}")
    return "; ".join(labels) if labels else "none"
