"""Context-sensitive property panel for the desktop model builder."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk

from .canvas import ModelCanvas
from .dialogs import LoadSettings, SupportSettings


class PropertyPanel(ttk.LabelFrame):
    """Right-side context panel for commands and selection inspection."""

    def __init__(self, parent, model_canvas: ModelCanvas, *, status_callback=None, command_callback=None) -> None:
        super().__init__(parent, text="Properties / Settings", padding=8)
        self.model_canvas = model_canvas
        self.status_callback = status_callback or (lambda message: None)
        self.command_callback = command_callback
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
        self.member_material_var = tk.StringVar(value="")
        self.member_section_var = tk.StringVar(value="")
        self.member_type_var = tk.StringVar(value="frame")
        self.selected_node_id_var = tk.StringVar(value="")
        self.selected_member_id_var = tk.StringVar(value="")
        self.selected_node_x_var = tk.StringVar(value="")
        self.selected_node_y_var = tk.StringVar(value="")
        self.new_node_hinge_var = tk.BooleanVar(value=False)
        self.selected_node_hinge_var = tk.BooleanVar(value=False)
        self.material_id_var = tk.StringVar(value="M1")
        self.material_type_var = tk.StringVar(value="Generic")
        self.material_e_var = tk.StringVar(value="1.0")
        self.material_alpha_var = tk.StringVar(value="0.0")
        self.material_density_var = tk.StringVar(value="0.0")
        self.assign_material_var = tk.StringVar(value="M1")
        self.section_input_mode_var = tk.StringVar(value="Geometric")
        self.section_id_var = tk.StringVar(value="S1")
        self.section_a_var = tk.StringVar(value="1.0")
        self.section_i_var = tk.StringVar(value="1.0")
        self.section_d_var = tk.StringVar(value="0.0")
        self.section_ea_var = tk.StringVar(value="")
        self.section_ei_var = tk.StringVar(value="")
        self.assign_section_var = tk.StringVar(value="S1")
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
        self.load_coordinate_system_var = tk.StringVar(value="Local")
        self.member_load_direction_var = tk.StringVar(value="2")
        self.udl_magnitude_var = tk.StringVar(value="0.0")
        self.point_direction_var = tk.StringVar(value="2")
        self.point_magnitude_var = tk.StringVar(value="0.0")
        self.position_var = tk.StringVar(value="0.5")
        self.temperature_tu_var = tk.StringVar(value="0.0")
        self.temperature_tb_var = tk.StringVar(value="0.0")
        self.mass_action_var = tk.StringVar(value="Replace")
        self.mass_ux_var = tk.StringVar(value="0.0")
        self.mass_uy_var = tk.StringVar(value="0.0")
        self.mass_rz_var = tk.StringVar(value="0.0")
        self.diaphragm_action_var = tk.StringVar(value="Replace")
        self.diaphragm_id_var = tk.StringVar(value="D1")
        self.diaphragm_nodes_var = tk.StringVar(value="")
        self.replicate_copies_var = tk.StringVar(value="1")
        self.replicate_dx_var = tk.StringVar(value="0.0")
        self.replicate_dy_var = tk.StringVar(value="0.0")
        self.move_dx_var = tk.StringVar(value="0.0")
        self.move_dy_var = tk.StringVar(value="0.0")
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
            self._diaphragm_panel()
        elif command == "Delete":
            self._delete_panel()
        elif command == "Replicate":
            self._replicate_panel()
        else:
            self._placeholder_panel(command, "No settings for this command yet.")

    def show_selection(self, kind: str | None, obj: object | None) -> None:
        self.selected_kind = kind
        self.selected_object = obj
        if self.current_command in ("Select / Inspect", "Draw Node", "Replicate"):
            self.show_command(self.current_command)
        elif self.current_command == "Assign Diaphragm":
            self.show_command("Assign Diaphragm")

    def sync_from_canvas(self) -> None:
        self.material_var.set(self.model_canvas.active_material_id)
        self.section_var.set(self.model_canvas.active_section_id)
        self.element_type_var.set(self.model_canvas.active_element_type)

    def show_diaphragm_group(self, group_id: str) -> None:
        self.diaphragm_id_var.set(group_id)
        self.selected_kind = "diaphragm"
        self.selected_object = {
            "id": group_id,
            "nodes": self.model_canvas.builder.model.diaphragm_ux_groups.get(group_id, []),
        }
        self.show_command("Assign Diaphragm")

    def _draw_node_panel(self) -> None:
        self._title("Draw Node")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="x").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.x_var, width=12).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="y").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.y_var, width=12).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Checkbutton(
            form,
            text="New nodes are hinged",
            variable=self.new_node_hinge_var,
            command=self._sync_draw_node_hinge,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 2))
        ttk.Button(self, text="Add Node", command=self._add_node).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        if self.selected_kind == "node" and self.selected_object is not None:
            node = self.selected_object
            self.selected_node_hinge_var.set(bool(getattr(node, "is_hinged", False)))
            self._sync_draw_node_hinge()
            editor = ttk.LabelFrame(self, text="Selected Node", padding=6)
            editor.grid(row=3, column=0, sticky="ew", pady=(8, 0))
            editor.columnconfigure(1, weight=1)
            ttk.Label(editor, text=f"Node {node.id}").grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
            ttk.Checkbutton(
                editor,
                text="Hinged node (release frame end moments)",
                variable=self.selected_node_hinge_var,
                command=self._apply_node_hinge_from_draw_node,
            ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 2))
            reset_row = 4
        else:
            self._sync_draw_node_hinge()
            reset_row = 3
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(
            row=reset_row,
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
            self.selected_node_id_var.set(str(node.id))
            self.selected_node_x_var.set(f"{node.x:.6g}")
            self.selected_node_y_var.set(f"{node.y:.6g}")
            support = self.model_canvas.builder.model.supports.get(node.id)
            support_text = _support_summary(support)
            mass_text = _mass_summary(self.model_canvas.builder.model, node.id)
            loads_text = _node_load_summary(self.model_canvas.builder.model, node.id)
            rows = [
                ("Node id", node.id),
                ("Hinge", "Yes" if getattr(node, "is_hinged", False) else "No"),
                ("Support", support_text),
                ("Mass", mass_text),
                ("Diaphragm", _node_diaphragm_summary(self.model_canvas.builder.model, node.id)),
                ("Loads", loads_text),
            ]
        elif self.selected_kind == "element" and self.selected_object is not None:
            element = self.selected_object
            loads_text = _member_load_summary(self.model_canvas.builder.model, element.id)
            self.selected_member_id_var.set(element.id)
            self.member_material_var.set(element.material.id)
            self.member_section_var.set(element.section.id)
            self.member_type_var.set(element.type)
            rows = [
                ("Element id", element.id),
                ("Type", element.type),
                ("Node i", element.node_i.id),
                ("Node j", element.node_j.id),
                ("Material", element.material.id),
                ("Section", _section_summary(element.section)),
                ("Loads", loads_text),
            ]
        elif self.selected_kind == "multi" and self.selected_object is not None:
            count = self.selected_object.get("count", 0)
            node_count = len(self.selected_object.get("nodes", []))
            element_count = len(self.selected_object.get("elements", []))
            rows = [
                ("Selection", f"{count} objects selected"),
                ("Nodes", node_count),
                ("Members", element_count),
            ]
        else:
            rows = [("Selection", "Click a node or member.")]

        info = ttk.Frame(self)
        info.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        info.columnconfigure(1, weight=1)
        for row, (label, value) in enumerate(rows):
            ttk.Label(info, text=label).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Label(info, text=str(value)).grid(row=row, column=1, sticky="w", pady=2)
        if self.selected_kind == "node" and self.selected_object is not None:
            self._node_id_editor(start_row=2)
            self._node_coordinate_editor(start_row=3)
        if self.selected_kind == "element" and self.selected_object is not None:
            self._member_id_editor(start_row=2)
            self._member_properties_editor(start_row=3)
        selection_count = getattr(self.model_canvas, "selection_count", lambda: 0)()
        if selection_count > 0:
            self._move_selection_editor(start_row=4 if self.selected_kind in {"node", "element"} and self.selected_object is not None else 2)

    def _placeholder_panel(self, title: str, text: str) -> None:
        self._title(title)
        ttk.Label(self, text=text, wraplength=220).grid(row=1, column=0, sticky="nw", pady=(8, 0))
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )

    def _move_selection_editor(self, start_row: int) -> None:
        editor = ttk.LabelFrame(self, text="Move Selection", padding=6)
        editor.grid(row=start_row, column=0, sticky="ew", pady=(8, 0))
        editor.columnconfigure(1, weight=1)
        ttk.Label(editor, text="dx").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(editor, textvariable=self.move_dx_var, width=10).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(editor, text="dy").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(editor, textvariable=self.move_dy_var, width=10).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Button(editor, text="Apply Move", command=self._apply_move_selection).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

    def _delete_panel(self) -> None:
        self._title("Delete")
        ttk.Label(
            self,
            text="Click a node or member on the canvas to delete it.",
            wraplength=220,
        ).grid(row=1, column=0, sticky="nw", pady=(8, 0))

    def _replicate_panel(self) -> None:
        self._title("Replicate")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Copies").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.replicate_copies_var, width=10).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="dx").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.replicate_dx_var, width=10).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="dy").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.replicate_dy_var, width=10).grid(row=2, column=1, sticky="ew", pady=2)
        ttk.Label(
            self,
            text=f"{self.model_canvas.selection_count()} selected object(s).",
            wraplength=220,
        ).grid(row=2, column=0, sticky="nw", pady=(8, 0))
        ttk.Button(self, text="Apply Replicate", command=self._apply_replicate).grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(self, text="Cancel", command=self._cancel_replicate).grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

    def _move_panel(self) -> None:
        self._title("Move Selection")
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="dx").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.move_dx_var, width=10).grid(row=0, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="dy").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.move_dy_var, width=10).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(
            self,
            text=f"{self.model_canvas.selection_count()} selected object(s).",
            wraplength=220,
        ).grid(row=2, column=0, sticky="nw", pady=(8, 0))
        ttk.Button(self, text="Apply Move", command=self._apply_move_selection).grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )
        ttk.Button(self, text="Cancel", command=self._cancel_replicate).grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )

    def _materials_sections_panel(self) -> None:
        self._title("Materials / Sections")

        material = ttk.LabelFrame(self, text="Material", padding=6)
        material.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        material.columnconfigure(1, weight=1)
        ttk.Label(material, text="Current").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(material, text=self.assign_material_var.get() or "none").grid(row=0, column=1, sticky="w", pady=2)
        ttk.Button(material, text="Define Materials...", command=self._open_materials_dialog).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )
        self._combo(material, 2, "Assign existing", self.assign_material_var, self._material_ids(), lambda: None)
        ttk.Button(material, text="Assign Material to Selected Members", command=self._assign_material_to_selected_members).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )

        section = ttk.LabelFrame(self, text="Section", padding=6)
        section.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        section.columnconfigure(1, weight=1)
        ttk.Label(section, text="Current").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(section, text=self.assign_section_var.get() or "none").grid(row=0, column=1, sticky="w", pady=2)
        ttk.Button(section, text="Define Frame Properties...", command=self._open_sections_dialog).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )
        self._combo(section, 2, "Assign existing", self.assign_section_var, self._section_ids(), lambda: None)
        ttk.Button(section, text="Assign Section to Selected Members", command=self._assign_section_to_selected_members).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(6, 0),
        )

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
                    ("Local", "Global"),
                    self._sync_member_load_coordinate_system,
                )
                direction_values = self._member_load_direction_values()
                if load_type == "Point Load":
                    if self.point_direction_var.get() not in direction_values:
                        self.point_direction_var.set(direction_values[-1])
                elif self.member_load_direction_var.get() not in direction_values:
                    self.member_load_direction_var.set(direction_values[-1])
            ttk.Label(form, text="Case").grid(row=4, column=0, sticky="w", pady=2)
            ttk.Entry(form, textvariable=self.load_case_var, width=10).grid(row=4, column=1, sticky="ew", pady=2)
            if load_type == "Point Load":
                self._combo(form, 5, "Direction", self.point_direction_var, direction_values, self._apply_load_settings)
                ttk.Label(form, text="P").grid(row=6, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.point_magnitude_var, width=10).grid(row=6, column=1, sticky="ew", pady=2)
                ttk.Label(form, text="Position a/L").grid(row=7, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.position_var, width=10).grid(row=7, column=1, sticky="ew", pady=2)
                ttk.Label(
                    self,
                    text="Local 1 = member i-to-j axis. Local 2 = transverse axis.",
                    wraplength=220,
                ).grid(row=5, column=0, sticky="nw", pady=(8, 0))
            elif load_type == "Temperature":
                ttk.Label(form, text="Tu").grid(row=5, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.temperature_tu_var, width=10).grid(row=5, column=1, sticky="ew", pady=2)
                ttk.Label(form, text="Tb").grid(row=6, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.temperature_tb_var, width=10).grid(row=6, column=1, sticky="ew", pady=2)
            else:
                self._combo(form, 5, "Direction", self.member_load_direction_var, direction_values, self._apply_load_settings)
                ttk.Label(form, text="w").grid(row=6, column=0, sticky="w", pady=2)
                ttk.Entry(form, textvariable=self.udl_magnitude_var, width=10).grid(row=6, column=1, sticky="ew", pady=2)
                ttk.Label(
                    self,
                    text="Local 1 = member i-to-j axis. Local 2 = transverse axis.",
                    wraplength=220,
                ).grid(row=5, column=0, sticky="nw", pady=(8, 0))
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

    def _diaphragm_panel(self) -> None:
        self._title("Assign Diaphragm")
        if (
            self.selected_kind != "diaphragm"
            and (not self.diaphragm_id_var.get().strip() or self.diaphragm_id_var.get().strip() == "D1")
        ):
            self.diaphragm_id_var.set(self._next_diaphragm_id())
        form = ttk.Frame(self)
        form.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        form.columnconfigure(1, weight=1)
        self._combo(form, 0, "Action", self.diaphragm_action_var, ("Add", "Replace", "Delete"), self._sync_diaphragm_settings)
        ttk.Label(form, text="Group id").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(form, textvariable=self.diaphragm_id_var, width=10).grid(row=1, column=1, sticky="ew", pady=2)
        ttk.Label(form, text="Selected nodes").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(form, text=self._selected_diaphragm_nodes_summary(), wraplength=150).grid(
            row=2,
            column=1,
            sticky="w",
            pady=2,
        )
        ttk.Button(self, text="Apply", command=self._apply_diaphragm_assignment).grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(self, text="Clear Selection", command=self._clear_diaphragm_selection).grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(6, 0),
        )
        ttk.Label(self, text="Select nodes on the canvas first, then apply the diaphragm group.", wraplength=220).grid(
            row=4,
            column=0,
            sticky="nw",
            pady=(8, 0),
        )
        ttk.Button(self, text="Reset to Default", command=self._reset_current_command).grid(row=5, column=0, sticky="ew", pady=(8, 0))
        self._sync_diaphragm_settings()

    def _member_properties_editor(self, start_row: int) -> None:
        materials = self._material_ids()
        sections = self._section_ids()
        editor = ttk.LabelFrame(self, text="Member Properties", padding=6)
        editor.grid(row=start_row, column=0, sticky="ew", pady=(8, 0))
        editor.columnconfigure(1, weight=1)
        if not self.model_canvas.builder.model.materials:
            ttk.Label(editor, text="No materials exist. Add a material first.", wraplength=210).grid(
                row=0,
                column=0,
                columnspan=2,
                sticky="w",
                pady=2,
            )
            return
        if not self.model_canvas.builder.model.sections:
            ttk.Label(editor, text="No sections exist. Add a section first.", wraplength=210).grid(
                row=0,
                column=0,
                columnspan=2,
                sticky="w",
                pady=2,
            )
            return
        self._combo(editor, 0, "Type", self.member_type_var, ("frame", "truss"), lambda: None)
        self._combo(editor, 1, "Material", self.member_material_var, materials, lambda: None)
        self._combo(editor, 2, "Section", self.member_section_var, sections, lambda: None)
        rigid_link_value = "Yes" if getattr(self.selected_object, "is_axially_rigid", False) else "No"
        ttk.Label(editor, text="Rigid link (couple UX, UY, RZ)").grid(row=3, column=0, sticky="w", pady=(8, 2))
        ttk.Label(editor, text=rigid_link_value).grid(row=3, column=1, sticky="w", pady=(8, 2))
        ttk.Label(
            editor,
            text="Uses existing is_axially_rigid XML flag; this is not axial-only stiffness.",
            wraplength=210,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(
            editor,
            text="Flexurally rigid beam idealization is not implemented yet. Use direct EI as a stiffness approximation only.",
            wraplength=210,
        ).grid(row=5, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Button(editor, text="Apply Member Properties", command=self._apply_member_properties).grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

    def _member_id_editor(self, start_row: int) -> None:
        editor = ttk.LabelFrame(self, text="Member ID", padding=6)
        editor.grid(row=start_row, column=0, sticky="ew", pady=(8, 0))
        editor.columnconfigure(1, weight=1)
        ttk.Label(editor, text="id").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(editor, textvariable=self.selected_member_id_var, width=12).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=2,
        )
        ttk.Button(editor, text="Apply Member ID", command=self._apply_member_id).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

    def _node_id_editor(self, start_row: int) -> None:
        editor = ttk.LabelFrame(self, text="Node ID", padding=6)
        editor.grid(row=start_row, column=0, sticky="ew", pady=(8, 0))
        editor.columnconfigure(1, weight=1)
        ttk.Label(editor, text="id").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(editor, textvariable=self.selected_node_id_var, width=12).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=2,
        )
        ttk.Button(editor, text="Apply Node ID", command=self._apply_node_id).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

    def _node_coordinate_editor(self, start_row: int) -> None:
        editor = ttk.LabelFrame(self, text="Node Coordinates", padding=6)
        editor.grid(row=start_row, column=0, sticky="ew", pady=(8, 0))
        editor.columnconfigure(1, weight=1)
        ttk.Label(editor, text="x").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(editor, textvariable=self.selected_node_x_var, width=12).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=2,
        )
        ttk.Label(editor, text="y").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(editor, textvariable=self.selected_node_y_var, width=12).grid(
            row=1,
            column=1,
            sticky="ew",
            pady=2,
        )
        ttk.Button(editor, text="Apply Coordinates", command=self._apply_node_coordinates).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

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
        self.model_canvas.add_node_by_coordinates(x, y, is_hinged=self.new_node_hinge_var.get())

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

    def _sync_member_load_coordinate_system(self) -> None:
        values = self._member_load_direction_values()
        if self.point_direction_var.get() not in values:
            self.point_direction_var.set(values[-1])
        if self.member_load_direction_var.get() not in values:
            self.member_load_direction_var.set(values[-1])
        self._reload_load_panel()

    def _member_load_direction_values(self) -> tuple[str, str]:
        return ("X", "Y") if self.load_coordinate_system_var.get() == "Global" else ("1", "2")

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
        coord_system = "local"
        direction = ""
        value = None
        try:
            if target == "Node" and load_type == "Nodal Moment":
                mz = float(self.mz_var.get())
            elif target == "Node":
                fx = float(self.fx_var.get())
                fy = float(self.fy_var.get())
            elif load_type == "Point Load":
                magnitude = float(self.point_magnitude_var.get())
                position = float(self.position_var.get())
                coord_system = self.load_coordinate_system_var.get().lower()
                direction = self.point_direction_var.get()
                value = magnitude
                if direction in ("X", "1"):
                    fx = magnitude
                else:
                    fy = magnitude
                backend_load_type = "Point Load"
            elif load_type == "Temperature":
                wx = float(self.temperature_tu_var.get())
                wy = float(self.temperature_tb_var.get())
                backend_load_type = "Temperature"
            else:
                magnitude = float(self.udl_magnitude_var.get())
                coord_system = self.load_coordinate_system_var.get().lower()
                direction = self.member_load_direction_var.get()
                value = magnitude
                if direction in ("X", "1"):
                    wx = magnitude
                else:
                    wy = magnitude
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
                coord_system=coord_system,
                direction=direction,
                value=value,
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

    def _sync_diaphragm_settings(self) -> None:
        group_id = self.diaphragm_id_var.get().strip() or "D1"
        self.model_canvas.set_diaphragm_settings(self.diaphragm_action_var.get(), group_id)
        self.status_callback("Assign Diaphragm: select nodes, confirm group id/action, then click Apply.")

    def _apply_diaphragm_assignment(self) -> None:
        self._sync_diaphragm_settings()
        group = self.model_canvas.apply_diaphragm_assignment()
        if group is not None:
            self.show_command("Assign Diaphragm")

    def _clear_diaphragm_selection(self) -> None:
        self.model_canvas.clear_node_selection()
        self.show_command("Assign Diaphragm")

    def _selected_diaphragm_nodes_summary(self) -> str:
        node_ids = self.model_canvas.selected_diaphragm_node_ids()
        if not node_ids and self.selected_kind == "diaphragm" and self.selected_object is not None:
            node_ids = list(self.selected_object.get("nodes", []))
        if not node_ids:
            return "0 selected nodes"
        return f"{len(node_ids)} selected nodes: {', '.join(str(node_id) for node_id in node_ids)}"

    def _next_diaphragm_id(self) -> str:
        existing = set(self.model_canvas.builder.model.diaphragm_ux_groups)
        index = 1
        while f"D{index}" in existing:
            index += 1
        return f"D{index}"

    def _apply_member_properties(self) -> None:
        if self.selected_kind != "element" or self.selected_object is None:
            self.status_callback("Member Properties: select a member first.")
            return
        material_id = self.member_material_var.get().strip()
        section_id = self.member_section_var.get().strip()
        element_type = self.member_type_var.get().strip()
        if not material_id or not section_id:
            self.status_callback("Member Properties: choose material and section.")
            return
        updated = self.model_canvas.update_selected_member_properties(element_type, material_id, section_id)
        if updated is not None:
            self.selected_object = updated
            self.show_command("Select / Inspect")

    def _apply_member_id(self) -> None:
        if self.selected_kind != "element" or self.selected_object is None:
            self.status_callback("Member ID: select one member first.")
            return
        new_id = self.selected_member_id_var.get().strip()
        if not new_id:
            self.status_callback("Member ID: id is required.")
            return
        updated = self.model_canvas.rename_selected_member(new_id)
        if updated is not None:
            self.selected_object = updated
            self.show_command("Select / Inspect")

    def _apply_node_id(self) -> None:
        if self.selected_kind != "node" or self.selected_object is None:
            self.status_callback("Node ID: select one node first.")
            return
        raw_id = self.selected_node_id_var.get().strip()
        if not raw_id:
            self.status_callback("Node ID: id is required.")
            return
        try:
            new_id = int(raw_id)
        except ValueError:
            self.status_callback("Node ID: id must be an integer.")
            return
        updated = self.model_canvas.rename_selected_node(new_id)
        if updated is not None:
            self.selected_object = updated
            self.show_command("Select / Inspect")

    def _apply_node_coordinates(self) -> None:
        if self.selected_kind != "node" or self.selected_object is None:
            self.status_callback("Node Coordinates: select one node first.")
            return
        try:
            x = float(self.selected_node_x_var.get())
            y = float(self.selected_node_y_var.get())
        except ValueError:
            self.status_callback("Node Coordinates: x and y must be numeric.")
            return
        updated = self.model_canvas.update_selected_node_coordinates(x, y)
        if updated is not None:
            self.selected_object = updated
            self.show_command("Select / Inspect")

    def _apply_node_hinge_from_draw_node(self) -> None:
        if self.selected_kind != "node" or self.selected_object is None:
            self.status_callback("Node Hinge: select one node first.")
            return
        updated = self.model_canvas.update_selected_node_hinge(self.selected_node_hinge_var.get())
        if updated is not None:
            self.selected_object = updated
            self.show_command("Draw Node")

    def _sync_draw_node_hinge(self) -> None:
        self.model_canvas.set_active_node_hinge(self.new_node_hinge_var.get())

    def _apply_replicate(self) -> None:
        try:
            copies = int(self.replicate_copies_var.get())
            dx = float(self.replicate_dx_var.get())
            dy = float(self.replicate_dy_var.get())
        except ValueError:
            self.status_callback("Replicate: copies must be an integer; dx and dy must be numeric.")
            return
        result = self.model_canvas.replicate_selection(copies, dx, dy)
        if result is not None:
            self.show_command("Replicate")

    def _apply_move_selection(self) -> None:
        try:
            dx = float(self.move_dx_var.get())
            dy = float(self.move_dy_var.get())
        except ValueError:
            self.status_callback("Move Selection: dx and dy must be numeric.")
            return
        result = self.model_canvas.move_selection(dx, dy)
        if result is not None:
            self.show_command("Move Selection")

    def _cancel_replicate(self) -> None:
        if self.command_callback is not None:
            self.command_callback("Select / Inspect")
        else:
            self.model_canvas.set_active_command("Select / Inspect")
            self.show_command("Select / Inspect")
        self.status_callback("Replicate canceled.")

    def _open_materials_dialog(self) -> None:
        MaterialListDialog(self, self.model_canvas.builder, self._refresh_after_material_section_change)

    def _open_sections_dialog(self) -> None:
        SectionListDialog(
            self,
            self.model_canvas.builder,
            self._refresh_after_material_section_change,
            self._open_materials_dialog,
        )

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
        self.model_canvas.builder.add_material(material_id, E=E, alpha=alpha, density=density, type=self.material_type_var.get())
        self.material_var.set(material_id)
        self.assign_material_var.set(material_id)
        self.model_canvas.set_active_material(material_id)
        self._refresh_after_material_section_change()
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
        self.assign_section_var.set(section_id)
        self.model_canvas.set_active_section(section_id)
        self._refresh_after_material_section_change()
        self.status_callback(f"Section {section_id} saved.")

    def _assign_material_to_selected_members(self) -> None:
        material_id = self.assign_material_var.get().strip() or self.material_id_var.get().strip()
        if material_id not in self.model_canvas.builder.model.materials:
            self.status_callback(f"Material assignment: unknown material {material_id}.")
            return
        count = self._assign_selected_members(material_id=material_id)
        if count:
            self.status_callback(f"Assigned material {material_id} to {count} member(s).")

    def _assign_section_to_selected_members(self) -> None:
        section_id = self.assign_section_var.get().strip() or self.section_id_var.get().strip()
        if section_id not in self.model_canvas.builder.model.sections:
            self.status_callback(f"Section assignment: unknown section {section_id}.")
            return
        count = self._assign_selected_members(section_id=section_id)
        if count:
            self.status_callback(f"Assigned section {section_id} to {count} member(s).")

    def _assign_material_section_to_selected_members(self) -> None:
        material_id = self.assign_material_var.get().strip() or self.material_id_var.get().strip()
        section_id = self.assign_section_var.get().strip() or self.section_id_var.get().strip()
        if material_id not in self.model_canvas.builder.model.materials:
            self.status_callback(f"Material assignment: unknown material {material_id}.")
            return
        if section_id not in self.model_canvas.builder.model.sections:
            self.status_callback(f"Section assignment: unknown section {section_id}.")
            return
        count = self._assign_selected_members(material_id=material_id, section_id=section_id)
        if count:
            self.status_callback(f"Assigned material {material_id} and section {section_id} to {count} member(s).")

    def _assign_selected_members(self, *, material_id: str | None = None, section_id: str | None = None) -> int:
        element_ids = self._selected_member_ids()
        if not element_ids:
            self.status_callback("Select one or more members first.")
            return 0
        model = self.model_canvas.builder.model
        material = model.materials.get(material_id) if material_id is not None else None
        section = model.sections.get(section_id) if section_id is not None else None
        for element_id in element_ids:
            element = model.elements[element_id]
            if material is not None:
                element.material = material
            if section is not None:
                element.section = section
        self._mark_model_dirty()
        self.model_canvas.redraw_model()
        self.model_canvas.change_callback()
        if len(element_ids) == 1:
            self.model_canvas.select_element(element_ids[0])
        elif hasattr(self.model_canvas, "_set_multi_selection"):
            self.model_canvas._set_multi_selection(set(), set(element_ids))
        self._refresh_material_section_dropdown_defaults()
        return len(element_ids)

    def _delete_material(self) -> None:
        material_id = self.material_id_var.get().strip() or self.assign_material_var.get().strip()
        model = self.model_canvas.builder.model
        if material_id not in model.materials:
            self.status_callback(f"Material {material_id} does not exist.")
            return
        used_by = sorted(element_id for element_id, element in model.elements.items() if element.material.id == material_id)
        if used_by:
            self.status_callback(
                f"Material {material_id} is used by {len(used_by)} member(s); reassign them before deleting."
            )
            return
        del model.materials[material_id]
        self._mark_model_dirty()
        self._refresh_after_material_section_change()
        self.status_callback(f"Deleted material {material_id}.")

    def _delete_section(self) -> None:
        section_id = self.section_id_var.get().strip() or self.assign_section_var.get().strip()
        model = self.model_canvas.builder.model
        if section_id not in model.sections:
            self.status_callback(f"Section {section_id} does not exist.")
            return
        used_by = sorted(element_id for element_id, element in model.elements.items() if element.section.id == section_id)
        if used_by:
            self.status_callback(
                f"Section {section_id} is used by {len(used_by)} member(s); reassign them before deleting."
            )
            return
        del model.sections[section_id]
        self._mark_model_dirty()
        self._refresh_after_material_section_change()
        self.status_callback(f"Deleted section {section_id}.")

    def _selected_member_ids(self) -> list[str]:
        selected = getattr(self.model_canvas, "selected_element_ids", set())
        model = self.model_canvas.builder.model
        return [element_id for element_id in sorted(selected) if element_id in model.elements]

    def _mark_model_dirty(self) -> None:
        mark_dirty = getattr(self.model_canvas.builder.model, "mark_dirty", None)
        if mark_dirty is not None:
            mark_dirty()

    def _refresh_after_material_section_change(self) -> None:
        self.model_canvas.redraw_model()
        self.model_canvas.change_callback()
        self._refresh_material_section_dropdown_defaults()
        if self.current_command == "Materials / Sections":
            self.show_command("Materials / Sections")

    def _refresh_material_section_dropdown_defaults(self) -> None:
        materials = self._material_ids()
        sections = self._section_ids()
        if self.assign_material_var.get() not in materials:
            self.assign_material_var.set(materials[0])
        if self.material_var.get() not in materials:
            self.material_var.set(materials[0])
        if self.assign_section_var.get() not in sections:
            self.assign_section_var.set(sections[0])
        if self.section_var.get() not in sections:
            self.section_var.set(sections[0])

    def _reset_current_command(self) -> None:
        command = self.current_command
        if command == "Draw Node":
            self.x_var.set("0.0")
            self.y_var.set("0.0")
            self.new_node_hinge_var.set(False)
            self._sync_draw_node_hinge()
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
            self.assign_material_var.set(next(iter(self.model_canvas.builder.model.materials), "M1"))
            self.section_input_mode_var.set("Geometric")
            self.section_id_var.set("S1")
            self.section_a_var.set("1.0")
            self.section_i_var.set("1.0")
            self.section_d_var.set("0.0")
            self.section_ea_var.set("")
            self.section_ei_var.set("")
            self.assign_section_var.set(next(iter(self.model_canvas.builder.model.sections), "S1"))
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
            self.load_coordinate_system_var.set("Local")
            self.member_load_direction_var.set("2")
            self.udl_magnitude_var.set("0.0")
            self.point_direction_var.set("2")
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
        elif command == "Assign Diaphragm":
            self.diaphragm_action_var.set("Replace")
            self.diaphragm_id_var.set(self._next_diaphragm_id())
            self.diaphragm_nodes_var.set("")
            self._sync_diaphragm_settings()
        self.status_callback(f"{command}: settings reset to defaults.")

    def _material_ids(self) -> tuple[str, ...]:
        return tuple(self.model_canvas.builder.model.materials.keys()) or ("M1",)

    def _section_ids(self) -> tuple[str, ...]:
        return tuple(self.model_canvas.builder.model.sections.keys()) or ("S1",)

    def _clear(self) -> None:
        for child in self.winfo_children():
            child.destroy()


class MaterialListDialog(tk.Toplevel):
    def __init__(self, parent, builder, refresh_callback) -> None:
        super().__init__(parent)
        self.builder = builder
        self.refresh_callback = refresh_callback
        self.title("Define Materials")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        materials = ttk.LabelFrame(frame, text="Materials", padding=6)
        materials.grid(row=0, column=0, sticky="nsew")
        self.listbox = tk.Listbox(materials, height=9, width=24, exportselection=False)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        actions = ttk.LabelFrame(frame, text="Click to", padding=6)
        actions.grid(row=0, column=1, sticky="n", padx=(8, 0))
        ttk.Button(actions, text="Add New Material...", command=self._add).grid(row=0, column=0, sticky="ew", pady=2)
        ttk.Button(actions, text="Modify/Show Material...", command=self._modify).grid(row=1, column=0, sticky="ew", pady=2)
        ttk.Button(actions, text="Delete Material", command=self._delete).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(frame, text="OK", command=self.destroy).grid(row=1, column=0, sticky="e", pady=(8, 0))
        ttk.Button(frame, text="Cancel", command=self.destroy).grid(row=1, column=1, sticky="w", pady=(8, 0), padx=(8, 0))
        self._reload()

    def _reload(self, selected: str | None = None) -> None:
        self.listbox.delete(0, tk.END)
        ids = sorted(self.builder.model.materials)
        for material_id in ids:
            self.listbox.insert(tk.END, material_id)
        if ids:
            index = ids.index(selected) if selected in ids else 0
            self.listbox.selection_set(index)
            self.listbox.activate(index)

    def _selected_id(self) -> str | None:
        selection = self.listbox.curselection()
        return None if not selection else self.listbox.get(selection[0])

    def _add(self) -> None:
        MaterialEditorDialog(self, self.builder, self._material_saved)

    def _modify(self) -> None:
        material_id = self._selected_id()
        if material_id:
            MaterialEditorDialog(self, self.builder, self._material_saved, material_id)

    def _delete(self) -> None:
        material_id = self._selected_id()
        if not material_id:
            return
        used = [element_id for element_id, element in self.builder.model.elements.items() if element.material.id == material_id]
        if used:
            messagebox.showinfo("Delete Material", f"Material is used by {len(used)} member(s).")
            return
        del self.builder.model.materials[material_id]
        self.builder._mark_dirty()
        self._material_saved(None)

    def _material_saved(self, material_id: str | None) -> None:
        self._reload(material_id)
        self.refresh_callback()


class MaterialEditorDialog(tk.Toplevel):
    def __init__(self, parent, builder, saved_callback, material_id: str | None = None) -> None:
        super().__init__(parent)
        self.builder = builder
        self.saved_callback = saved_callback
        self.original_id = material_id
        material = builder.model.materials.get(material_id) if material_id else None
        self.title("Material Property Data")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.id_var = tk.StringVar(value=material.id if material else _next_named_id(builder.model.materials, "M"))
        self.type_var = tk.StringVar(value=getattr(material, "type", "Generic") if material else "Generic")
        self.e_var = tk.StringVar(value=_format_number(material.E) if material else "1.0")
        self.alpha_var = tk.StringVar(value=_format_number(material.alpha) if material else "0.0")
        self.density_var = tk.StringVar(value=_format_number(material.density) if material else "0.0")

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        data = ttk.LabelFrame(frame, text="General Data", padding=8)
        data.grid(row=0, column=0, sticky="ew")
        data.columnconfigure(1, weight=1)
        ttk.Label(data, text="Material Name").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(data, textvariable=self.id_var, width=24).grid(row=0, column=1, sticky="ew", pady=2)
        _readonly_combo(data, 1, "Material Type", self.type_var, ("Generic", "Steel", "Concrete"))

        props = ttk.LabelFrame(frame, text="Isotropic Property Data", padding=8)
        props.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        props.columnconfigure(1, weight=1)
        _entry_row(props, 0, "Modulus of Elasticity, E", self.e_var)
        _entry_row(props, 1, "Thermal Expansion, alpha", self.alpha_var)
        _entry_row(props, 2, "Mass per Unit Volume", self.density_var)

        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, pady=(10, 0))
        ttk.Button(actions, text="OK", command=self._save).grid(row=0, column=0, padx=6)
        ttk.Button(actions, text="Cancel", command=self.destroy).grid(row=0, column=1, padx=6)

    def _save(self) -> None:
        material_id = self.id_var.get().strip()
        if not material_id:
            messagebox.showerror("Material", "Material name is required.")
            return
        try:
            E = float(self.e_var.get())
            alpha = float(self.alpha_var.get())
            density = float(self.density_var.get())
        except ValueError:
            messagebox.showerror("Material", "E, alpha, and density must be numeric.")
            return
        if self.original_id and self.original_id != material_id and self.original_id in self.builder.model.materials:
            old = self.builder.model.materials[self.original_id]
            material = self.builder.add_material(material_id, E, alpha, density, self.type_var.get())
            for element in self.builder.model.elements.values():
                if element.material is old:
                    element.material = material
            del self.builder.model.materials[self.original_id]
        else:
            self.builder.add_material(material_id, E=E, alpha=alpha, density=density, type=self.type_var.get())
        self.saved_callback(material_id)
        self.destroy()


class SectionListDialog(tk.Toplevel):
    def __init__(self, parent, builder, refresh_callback, add_material_callback) -> None:
        super().__init__(parent)
        self.builder = builder
        self.refresh_callback = refresh_callback
        self.add_material_callback = add_material_callback
        self.title("Frame Properties")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        props = ttk.LabelFrame(frame, text="Properties", padding=6)
        props.grid(row=0, column=0, sticky="nsew")
        self.listbox = tk.Listbox(props, height=9, width=26, exportselection=False)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        actions = ttk.LabelFrame(frame, text="Click to", padding=6)
        actions.grid(row=0, column=1, sticky="n", padx=(8, 0))
        ttk.Button(actions, text="Add New Property...", command=self._add).grid(row=0, column=0, sticky="ew", pady=2)
        ttk.Button(actions, text="Modify/Show Property...", command=self._modify).grid(row=1, column=0, sticky="ew", pady=2)
        ttk.Button(actions, text="Delete Property", command=self._delete).grid(row=2, column=0, sticky="ew", pady=2)
        ttk.Button(frame, text="OK", command=self.destroy).grid(row=1, column=0, sticky="e", pady=(8, 0))
        ttk.Button(frame, text="Cancel", command=self.destroy).grid(row=1, column=1, sticky="w", pady=(8, 0), padx=(8, 0))
        self._reload()

    def _reload(self, selected: str | None = None) -> None:
        self.listbox.delete(0, tk.END)
        ids = sorted(self.builder.model.sections)
        for section_id in ids:
            self.listbox.insert(tk.END, section_id)
        if ids:
            index = ids.index(selected) if selected in ids else 0
            self.listbox.selection_set(index)
            self.listbox.activate(index)

    def _selected_id(self) -> str | None:
        selection = self.listbox.curselection()
        return None if not selection else self.listbox.get(selection[0])

    def _add(self) -> None:
        SectionEditorDialog(self, self.builder, self._section_saved, self.add_material_callback)

    def _modify(self) -> None:
        section_id = self._selected_id()
        if section_id:
            SectionEditorDialog(self, self.builder, self._section_saved, self.add_material_callback, section_id)

    def _delete(self) -> None:
        section_id = self._selected_id()
        if not section_id:
            return
        used = [element_id for element_id, element in self.builder.model.elements.items() if element.section.id == section_id]
        if used:
            messagebox.showinfo("Delete Property", f"Section is used by {len(used)} member(s).")
            return
        del self.builder.model.sections[section_id]
        self.builder._mark_dirty()
        self._section_saved(None)

    def _section_saved(self, section_id: str | None) -> None:
        self._reload(section_id)
        self.refresh_callback()


class SectionEditorDialog(tk.Toplevel):
    def __init__(self, parent, builder, saved_callback, add_material_callback, section_id: str | None = None) -> None:
        super().__init__(parent)
        self.builder = builder
        self.saved_callback = saved_callback
        self.add_material_callback = add_material_callback
        self.original_id = section_id
        section = builder.model.sections.get(section_id) if section_id else None
        self.title("Section Property Data")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.id_var = tk.StringVar(value=section.id if section else _next_named_id(builder.model.sections, "S"))
        self.shape_var = tk.StringVar(value=getattr(section, "shape", "Generic") if section else "Generic")
        self.material_var = tk.StringVar(value=getattr(section, "material_id", "") or next(iter(builder.model.materials), ""))
        self.depth_var = tk.StringVar(value=_format_entry_optional(getattr(section, "depth", None)))
        self.width_var = tk.StringVar(value=_format_entry_optional(getattr(section, "width", None)))
        self.diameter_var = tk.StringVar(value=_format_entry_optional(getattr(section, "outside_diameter", None)))
        self.thickness_var = tk.StringVar(value=_format_entry_optional(getattr(section, "wall_thickness", None)))
        self.a_var = tk.StringVar(value=_format_number(section.A) if section else "")
        self.i_var = tk.StringVar(value=_format_number(section.I) if section else "")
        self.d_var = tk.StringVar(value=_format_number(section.d) if section else "0.0")
        self.ea_var = tk.StringVar(value=_format_entry_optional(getattr(section, "EA", None)))
        self.ei_var = tk.StringVar(value=_format_entry_optional(getattr(section, "EI", None)))

        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        general = ttk.LabelFrame(frame, text="General", padding=8)
        general.grid(row=0, column=0, sticky="ew")
        general.columnconfigure(1, weight=1)
        _entry_row(general, 0, "Section Name", self.id_var)
        _readonly_combo(general, 1, "Section Type", self.shape_var, ("Generic", "Rectangular", "Pipe"), self._sync_shape)

        dims = ttk.LabelFrame(frame, text="Dimensions / Properties", padding=8)
        dims.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        dims.columnconfigure(1, weight=1)
        self.rect_widgets = _entry_row(dims, 0, "Depth", self.depth_var) + _entry_row(dims, 1, "Width", self.width_var)
        self.pipe_widgets = _entry_row(dims, 2, "Outside Diameter", self.diameter_var) + _entry_row(dims, 3, "Wall Thickness", self.thickness_var)
        self.generic_widgets = _entry_row(dims, 4, "A", self.a_var) + _entry_row(dims, 5, "I", self.i_var)
        _entry_row(dims, 6, "Thermal depth d", self.d_var)
        _entry_row(dims, 7, "EA direct", self.ea_var)
        _entry_row(dims, 8, "EI direct", self.ei_var)
        ttk.Button(dims, text="Section Properties...", command=self._show_section_properties).grid(
            row=9,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

        material = ttk.LabelFrame(frame, text="Material", padding=8)
        material.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        material.columnconfigure(1, weight=1)
        ttk.Button(material, text="+", width=3, command=self.add_material_callback).grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            material,
            textvariable=self.material_var,
            values=tuple(self.builder.model.materials.keys()),
            state="readonly",
            width=22,
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        actions = ttk.Frame(frame)
        actions.grid(row=3, column=0, pady=(10, 0))
        ttk.Button(actions, text="OK", command=self._save).grid(row=0, column=0, padx=6)
        ttk.Button(actions, text="Cancel", command=self.destroy).grid(row=0, column=1, padx=6)
        self._sync_shape()

    def _sync_shape(self) -> None:
        shape = self.shape_var.get()
        for widget in self.rect_widgets:
            widget.grid() if shape == "Rectangular" else widget.grid_remove()
        for widget in self.pipe_widgets:
            widget.grid() if shape == "Pipe" else widget.grid_remove()
        for widget in self.generic_widgets:
            widget.grid() if shape == "Generic" else widget.grid_remove()

    def _save(self) -> None:
        section_id = self.id_var.get().strip()
        if not section_id:
            messagebox.showerror("Section", "Section name is required.")
            return
        try:
            values = self._section_values()
        except ValueError as exc:
            messagebox.showerror("Section", str(exc))
            return
        if self.original_id and self.original_id != section_id and self.original_id in self.builder.model.sections:
            old = self.builder.model.sections[self.original_id]
            del self.builder.model.sections[self.original_id]
            section = self.builder.add_section(section_id, **values)
            for element in self.builder.model.elements.values():
                if element.section is old:
                    element.section = section
        else:
            self.builder.add_section(section_id, **values)
        self.saved_callback(section_id)
        self.destroy()

    def _section_values(self) -> dict:
        shape = self.shape_var.get()
        d = _optional_float(self.d_var.get()) or 0.0
        EA = _optional_float(self.ea_var.get())
        EI = _optional_float(self.ei_var.get())
        if shape == "Rectangular":
            depth = _required_float(self.depth_var.get(), "Depth")
            width = _required_float(self.width_var.get(), "Width")
            if depth <= 0.0 or width <= 0.0:
                raise ValueError("Rectangular dimensions must be positive.")
            A = width * depth
            I = width * depth**3 / 12.0
            return {
                "A": A,
                "I": I,
                "d": d or depth,
                "EA": EA,
                "EI": EI,
                "shape": shape,
                "material_id": self.material_var.get(),
                "depth": depth,
                "width": width,
            }
        if shape == "Pipe":
            outside_diameter = _required_float(self.diameter_var.get(), "Outside Diameter")
            wall_thickness = _required_float(self.thickness_var.get(), "Wall Thickness")
            if outside_diameter <= 0.0 or wall_thickness <= 0.0 or 2.0 * wall_thickness > outside_diameter:
                raise ValueError("Pipe dimensions must be positive and wall thickness must fit inside diameter.")
            inner = outside_diameter - 2.0 * wall_thickness
            A = math.pi * (outside_diameter**2 - inner**2) / 4.0
            I = math.pi * (outside_diameter**4 - inner**4) / 64.0
            return {
                "A": A,
                "I": I,
                "d": d or outside_diameter,
                "EA": EA,
                "EI": EI,
                "shape": shape,
                "material_id": self.material_var.get(),
                "outside_diameter": outside_diameter,
                "wall_thickness": wall_thickness,
            }
        A = _optional_float(self.a_var.get()) or 0.0
        I = _optional_float(self.i_var.get()) or 0.0
        return {
            "A": A,
            "I": I,
            "d": d,
            "EA": EA,
            "EI": EI,
            "shape": shape,
            "material_id": self.material_var.get(),
        }

    def _show_section_properties(self) -> None:
        try:
            values = self._section_values()
        except ValueError as exc:
            messagebox.showerror("Section Properties", str(exc))
            return
        SectionPropertiesDialog(self, self.id_var.get().strip(), values["A"], values["I"])


class SectionPropertiesDialog(tk.Toplevel):
    def __init__(self, parent, section_id: str, area: float, inertia: float) -> None:
        super().__init__(parent)
        self.title("Property Data")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame, text="Section Name").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Label(frame, text=section_id).grid(row=0, column=1, sticky="w", pady=2)
        ttk.Label(frame, text="Cross-section (axial) area").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Label(frame, text=_format_number(area)).grid(row=1, column=1, sticky="w", pady=2)
        ttk.Label(frame, text="Moment of Inertia about 3 axis").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(frame, text=_format_number(inertia)).grid(row=2, column=1, sticky="w", pady=2)
        ttk.Button(frame, text="OK", command=self.destroy).grid(row=3, column=0, columnspan=2, pady=(10, 0))


def _entry_row(parent, row: int, label: str, variable) -> list:
    label_widget = ttk.Label(parent, text=label)
    entry_widget = ttk.Entry(parent, textvariable=variable, width=18)
    label_widget.grid(row=row, column=0, sticky="w", pady=2)
    entry_widget.grid(row=row, column=1, sticky="ew", pady=2)
    return [label_widget, entry_widget]


def _readonly_combo(parent, row: int, label: str, variable, values, command=None) -> None:
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
    combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly", width=20)
    combo.grid(row=row, column=1, sticky="ew", pady=2)
    if command is not None:
        combo.bind("<<ComboboxSelected>>", lambda _event: command())


def _next_named_id(items, prefix: str) -> str:
    index = 1
    while f"{prefix}{index}" in items:
        index += 1
    return f"{prefix}{index}"


def _format_number(value) -> str:
    return f"{float(value):.6g}"


def _format_entry_optional(value) -> str:
    return "" if value is None else _format_number(value)


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


def _node_diaphragm_summary(model, node_id: int) -> str:
    labels = [group_id for group_id, node_ids in model.diaphragm_ux_groups.items() if node_id in node_ids]
    return ", ".join(labels) if labels else "none"


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


def _parse_node_ids(value: str) -> list[int]:
    text = value.strip()
    if not text:
        return []
    node_ids = []
    for part in text.replace(";", ",").split(","):
        item = part.strip()
        if not item:
            continue
        try:
            node_ids.append(int(item))
        except ValueError as exc:
            raise ValueError("node ids must be integers.") from exc
    return node_ids


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
                labels.append(f"{load_case.id}: UDL {_member_load_direction_label(load)}")
            elif load.__class__.__name__ == "PointLoad":
                labels.append(f"{load_case.id}: Point a/L={load.position:.3g}, {_member_load_direction_label(load)}")
            elif load.__class__.__name__ == "TemperatureL":
                labels.append(f"{load_case.id}: Temperature Tu={load.Tu:.3g}, Tb={load.Tb:.3g}")
    return "; ".join(labels) if labels else "none"


def _member_load_direction_label(load) -> str:
    value = getattr(load, "value", None)
    coord_system = getattr(load, "coord_system", "local")
    direction = getattr(load, "direction", "")
    if value is not None and direction:
        return f"{coord_system} {direction}={value:.3g}"
    if load.__class__.__name__ == "UniformlyDL":
        return f"wx={load.wx:.3g}, wy={load.wy:.3g}"
    return f"Fx={load.fx:.3g}, Fy={load.fy:.3g}"
