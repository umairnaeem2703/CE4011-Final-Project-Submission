"""Minimal Tkinter desktop shell for the structural analysis app."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk
from collections.abc import Mapping

try:
    from ui.static_analysis import run_static_analysis
except ImportError:  # pragma: no cover - used when launched as python -m src.ui_desktop.app
    from ..ui.static_analysis import run_static_analysis

from .canvas import ModelCanvas
from .object_tree import ObjectTreePanel
from .property_panel import PropertyPanel
from .result_formatting import (
    DEFAULT_DISPLAY_TOLERANCE,
    dof_display_rows,
    format_scalar,
    format_vector,
    matrix_columns,
    matrix_rows,
    unit_labels,
)
from .template_dialog import ask_new_model


ACTIVE_COMMANDS = (
    "Select / Inspect",
    "Draw Node",
    "Draw Member",
    "Materials / Sections",
    "Assign Support",
    "Assign Load",
    "Assign Mass",
    "Assign Diaphragm",
    "Delete",
    "Replicate",
)
PLACEHOLDER_COMMANDS = (
    "Window Select",
)
COMMAND_TABS = (
    ("Model", (("action", "New"), ("action", "Open XML"), ("action", "Save XML"), ("action", "Validate"))),
    (
        "Edit",
        (
            ("command", "Select / Inspect"),
            ("command", "Delete"),
            ("command", "Replicate"),
        ),
    ),
    (
        "Assign",
        (
            ("command", "Draw Node"),
            ("command", "Draw Member"),
            ("command", "Materials / Sections"),
            ("command", "Assign Support"),
            ("command", "Assign Load"),
            ("command", "Assign Mass"),
            ("command", "Assign Diaphragm"),
        ),
    ),
    (
        "View",
        (
            ("grid_controls", "Grid"),
            ("snap_toggle", "Snap"),
            ("view_action", "Zoom In"),
            ("view_action", "Zoom Out"),
            ("command", "Pan"),
            ("placeholder", "Window Select"),
            ("local_axes_toggle", "Local Axes"),
            ("view_action", "Full View"),
        ),
    ),
    ("Analyze", (("action", "Run Static Analysis"),)),
    ("Results", (("action", "Results"),)),
)


class MainWindow:
    """Tkinter shell for model-building workflows and analysis actions."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("CE 4011 Structural Analysis")
        self.root.geometry("1280x780")
        self.root.minsize(980, 620)

        self.selected_command = tk.StringVar(value="Select / Inspect")
        self.grid_visible = tk.BooleanVar(value=True)
        self.snap_to_grid = tk.BooleanVar(value=False)
        self.local_axes_visible = tk.BooleanVar(value=False)
        self.grid_spacing = tk.StringVar(value="1.0")
        self.status_message = tk.StringVar(value="Select / Inspect: click a node or member to inspect it.")
        self.latest_static_results = None
        self.static_analysis_error = None
        self.result_view_category = None
        self.result_view_tree = None
        self.result_display_tolerance = DEFAULT_DISPLAY_TOLERANCE
        self.result_tolerance_var = None

        self._configure_grid()
        self._build_command_area()
        self._build_left_panel()
        self._build_model_canvas()
        self._build_right_panel()
        self._build_status_panel()
        self._refresh_object_tree()

    def run(self) -> None:
        self.root.mainloop()

    def _configure_grid(self) -> None:
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=0)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

    def _build_command_area(self) -> None:
        command_area = ttk.Notebook(self.root)
        command_area.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(6, 2))

        for tab_name, items in COMMAND_TABS:
            tab = ttk.Frame(command_area, padding=(8, 6))
            command_area.add(tab, text=tab_name)
            self._build_command_group(tab, items)

    def _build_command_group(self, parent: ttk.Frame, items: tuple[tuple[str, str], ...]) -> None:
        parent.columnconfigure(len(items), weight=1)
        for column, (kind, label) in enumerate(items):
            if kind == "command":
                widget = ttk.Radiobutton(
                    parent,
                    text=label,
                    value=label,
                    variable=self.selected_command,
                    command=lambda name=label: self._select_command(name),
                )
            elif kind == "action":
                widget = ttk.Button(parent, text=label, command=lambda name=label: self._toolbar_action(name))
            elif kind == "view_action":
                widget = ttk.Button(parent, text=label, command=lambda name=label: self._view_action(name))
            elif kind == "grid_controls":
                widget = self._build_grid_controls(parent)
            elif kind == "snap_toggle":
                widget = ttk.Checkbutton(
                    parent,
                    text="Snap to Grid",
                    variable=self.snap_to_grid,
                    command=self._toggle_snap_to_grid,
                )
            elif kind == "local_axes_toggle":
                widget = ttk.Checkbutton(
                    parent,
                    text="Local Axes",
                    variable=self.local_axes_visible,
                    command=self._toggle_local_axes_visible,
                )
            else:
                widget = ttk.Button(parent, text=label, state=tk.DISABLED)
            widget.grid(row=0, column=column, padx=(0, 6), sticky="w")

    def _build_grid_controls(self, parent: ttk.Frame) -> ttk.Frame:
        group = ttk.Frame(parent)
        ttk.Checkbutton(
            group,
            text="Grid",
            variable=self.grid_visible,
            command=self._toggle_grid_visible,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(group, text="Spacing").grid(row=0, column=1, padx=(8, 2), sticky="w")
        entry = ttk.Entry(group, textvariable=self.grid_spacing, width=7)
        entry.grid(row=0, column=2, sticky="w")
        entry.bind("<Return>", lambda _event: self._apply_grid_spacing())
        ttk.Button(group, text="Apply", command=self._apply_grid_spacing).grid(row=0, column=3, padx=(4, 0), sticky="w")
        return group

    def _build_left_panel(self) -> None:
        panel = ttk.Frame(self.root, padding=(8, 4))
        panel.grid(row=1, column=0, sticky="nsw")
        panel.columnconfigure(0, weight=1)

        self.object_tree = ObjectTreePanel(panel, selection_callback=self._select_from_tree)
        self.object_tree.grid(row=0, column=0, sticky="nsew")
        panel.rowconfigure(0, weight=1)

    def _build_model_canvas(self) -> None:
        self.model_canvas = ModelCanvas(
            self.root,
            status_callback=self._write_status,
            selection_callback=self._show_selection,
            change_callback=self._refresh_object_tree,
        )
        self.model_canvas.grid(row=1, column=1, sticky="nsew", pady=4)
        self.canvas = self.model_canvas.canvas

    def _build_right_panel(self) -> None:
        self.property_panel = PropertyPanel(
            self.root,
            self.model_canvas,
            status_callback=self._write_status,
            command_callback=self._select_command,
        )
        self.property_panel.grid(row=1, column=2, sticky="nse", padx=(4, 8), pady=4)
        self.property_panel.columnconfigure(0, minsize=240)

    def _build_status_panel(self) -> None:
        panel = ttk.Frame(self.root, padding=(8, 4))
        panel.grid(row=2, column=0, columnspan=3, sticky="ew")
        panel.columnconfigure(0, weight=1)
        ttk.Label(panel, textvariable=self.status_message).grid(row=0, column=0, sticky="w")
        self.log = tk.Text(panel, height=4, wrap="word")
        self.log.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.log.insert("end", "Desktop model builder ready.\n")
        self.log.configure(state="disabled")

    def _select_command(self, name: str) -> None:
        self.selected_command.set(name)
        self.model_canvas.set_active_command(name)
        self.property_panel.show_command(name)
        self._write_status(self.model_canvas.command_instruction())

    def _toggle_grid_visible(self) -> None:
        self.model_canvas.set_grid_visible(self.grid_visible.get())

    def _toggle_snap_to_grid(self) -> None:
        self.model_canvas.set_snap_to_grid(self.snap_to_grid.get())

    def _toggle_local_axes_visible(self) -> None:
        self.model_canvas.set_local_axes_visible(self.local_axes_visible.get())

    def _apply_grid_spacing(self) -> None:
        try:
            spacing = float(self.grid_spacing.get())
        except ValueError:
            self._write_status("Grid spacing must be numeric.")
            return
        if not self.model_canvas.set_grid_spacing(spacing):
            return
        self.grid_spacing.set(f"{self.model_canvas.grid_spacing:.6g}")

    def _view_action(self, name: str) -> None:
        if name == "Zoom In":
            self.model_canvas.zoom_in()
        elif name == "Zoom Out":
            self.model_canvas.zoom_out()
        elif name == "Full View":
            self.model_canvas.restore_full_view()

    def _toolbar_action(self, name: str) -> None:
        if name == "New":
            self._new_model()
            return
        if name == "Save XML":
            self._save_xml()
            return
        if name == "Run Static Analysis":
            self._run_static_analysis()
            return
        if name == "Results":
            self._show_static_results()
            return
        self._write_status(f"{name}: not wired yet.")

    def _run_static_analysis(self) -> None:
        result = run_static_analysis(self.model_canvas.builder.model)
        if not result.ok:
            self.latest_static_results = None
            self.static_analysis_error = result.error
            self._write_status(result.error or "Static analysis failed.")
            return

        self.latest_static_results = result.results
        self.static_analysis_error = None
        load_case = getattr(result.results, "load_case_id", "selected load case")
        displacement_count = len(getattr(result.results, "displacements", {}))
        reaction_count = len(getattr(result.results, "reactions", {}))
        self._write_status(
            f"Static analysis complete for {load_case}: "
            f"{displacement_count} displacement rows, {reaction_count} reaction rows."
        )

    def _show_static_results(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("Static Results")
        window.geometry("760x420")
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)

        if self.latest_static_results is None:
            ttk.Label(window, text="Run Static Analysis first.").grid(row=0, column=0, sticky="w", padx=10, pady=10)
            self._write_status("Run Static Analysis first.")
            return

        categories = tuple(self._static_result_categories())
        self.result_view_category = tk.StringVar(value=categories[0])
        selector = ttk.Combobox(window, textvariable=self.result_view_category, values=categories, state="readonly")
        selector.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_static_result_table())

        controls = ttk.Frame(window)
        controls.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        controls.columnconfigure(2, weight=1)
        ttk.Label(controls, text="Display tolerance").grid(row=0, column=0, sticky="w")
        self.result_tolerance_var = tk.StringVar(value=f"{self._display_tolerance():g}")
        tolerance_entry = ttk.Entry(controls, textvariable=self.result_tolerance_var, width=10)
        tolerance_entry.grid(row=0, column=1, padx=(8, 4), sticky="w")
        tolerance_entry.bind("<Return>", lambda _event: self._apply_result_tolerance())
        ttk.Button(controls, text="Apply", command=self._apply_result_tolerance).grid(row=0, column=2, sticky="w")

        frame = ttk.Frame(window)
        frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.result_view_tree = ttk.Treeview(frame, show="headings")
        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.result_view_tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.result_view_tree.xview)
        self.result_view_tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.result_view_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self._refresh_static_result_table()
        self._write_status("Static results opened.")

    def _static_result_categories(self) -> list[str]:
        return [
            "Nodal Displacements",
            "Support Reactions",
            "Member End Forces",
            "DOF Map",
            "Global Stiffness Matrix K",
            "Reduced Stiffness Matrix Kff",
            "Global Force Vector F",
            "Reduced Force Vector Ff",
        ]

    def _refresh_static_result_table(self) -> None:
        if self.result_view_tree is None or self.result_view_category is None:
            return
        columns, rows = self._static_result_table_data(self.result_view_category.get())
        tree = self.result_view_tree
        tree.delete(*tree.get_children())
        tree.configure(columns=columns)
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=120, anchor="w", stretch=True)
        for row in rows:
            tree.insert("", "end", values=row)

    def _static_result_table_data(self, category: str) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        results = self.latest_static_results
        if results is None:
            return (("Message",), [("Run Static Analysis first.",)])
        units = self._result_unit_labels()
        if category == "Nodal Displacements":
            return (
                ("Node", f"UX [{units['length']}]", f"UY [{units['length']}]", f"RZ [{units['rotation']}]"),
                self._vector_rows(getattr(results, "displacements", None)),
            )
        if category == "Support Reactions":
            return (
                ("Node", f"FX [{units['force']}]", f"FY [{units['force']}]", f"MZ [{units['moment']}]"),
                self._vector_rows(getattr(results, "reactions", None)),
            )
        if category == "Member End Forces":
            return self._member_force_rows(getattr(results, "element_forces", None), units)
        if category == "DOF Map":
            return self._mapping_rows(getattr(results, "dof_map", None))
        if category == "Global Stiffness Matrix K":
            return self._matrix_table(getattr(results, "K", None), "Global stiffness matrix K is unavailable.")
        if category == "Reduced Stiffness Matrix Kff":
            return self._matrix_table(getattr(results, "Kff", None), "Reduced stiffness matrix Kff is unavailable.")
        if category == "Global Force Vector F":
            return self._matrix_table(getattr(results, "F", None), "Global force vector F is unavailable.")
        if category == "Reduced Force Vector Ff":
            return self._matrix_table(getattr(results, "Ff", None), "Reduced force vector Ff is unavailable.")
        return (("Message",), [("No result data available.",)])

    def _result_unit_labels(self) -> dict[str, str]:
        model = getattr(getattr(self, "model_canvas", None), "builder", None)
        model = getattr(model, "model", None)
        return unit_labels(getattr(model, "unit_system", None))

    def _matrix_table(self, matrix: object, missing_message: str) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        rows = matrix_rows(matrix, tolerance=self._display_tolerance())
        if not rows:
            return (("Message",), [(missing_message,)])
        return (matrix_columns(matrix), rows)

    def _display_tolerance(self) -> float:
        return getattr(self, "result_display_tolerance", DEFAULT_DISPLAY_TOLERANCE)

    def _apply_result_tolerance(self) -> None:
        if self.result_tolerance_var is None:
            return
        try:
            tolerance = float(self.result_tolerance_var.get())
        except ValueError:
            self._write_status("Result display tolerance must be numeric.")
            return
        if tolerance <= 0.0:
            self._write_status("Result display tolerance must be positive.")
            return
        self.result_display_tolerance = tolerance
        self.result_tolerance_var.set(f"{tolerance:g}")
        self._refresh_static_result_table()
        self._write_status(f"Static result display tolerance set to {tolerance:g}.")

    def _vector_rows(self, values_by_id: Mapping[object, object] | None) -> list[tuple[str, ...]]:
        if not values_by_id:
            return [("Unavailable", "-", "-", "-")]
        rows = []
        for key, values in values_by_id.items():
            vector = format_vector(values, tolerance=self._display_tolerance())
            rows.append((str(key), self._format_value_at(vector, 0), self._format_value_at(vector, 1), self._format_value_at(vector, 2)))
        return rows

    def _member_force_rows(
        self,
        element_forces: Mapping[object, object] | None,
        units: Mapping[str, str],
    ) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        columns = (
            "Element",
            "End",
            f"N [{units['force']}]",
            f"V [{units['force']}]",
            f"M [{units['moment']}]",
        )
        if not element_forces:
            return (columns, [("Unavailable", "-", "-", "-", "-")])
        rows = []
        for element_id, forces in element_forces.items():
            if isinstance(forces, Mapping):
                for label, values in forces.items():
                    vector = format_vector(values, tolerance=self._display_tolerance())
                    rows.append((str(element_id), str(label), self._format_value_at(vector, 0), self._format_value_at(vector, 1), self._format_value_at(vector, 2)))
            else:
                vector = format_vector(forces, tolerance=self._display_tolerance())
                if len(vector) >= 6:
                    rows.append((str(element_id), "i", self._format_value_at(vector, 0), self._format_value_at(vector, 1), self._format_value_at(vector, 2)))
                    rows.append((str(element_id), "j", self._format_value_at(vector, 3), self._format_value_at(vector, 4), self._format_value_at(vector, 5)))
                else:
                    rows.append((str(element_id), "end", self._format_value_at(vector, 0), self._format_value_at(vector, 1), self._format_value_at(vector, 2)))
        return (columns, rows)

    def _mapping_rows(self, mapping: Mapping[object, object] | None) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        if not mapping:
            model = getattr(getattr(self, "model_canvas", None), "builder", None)
            model = getattr(model, "model", None)
            mapping = getattr(model, "cached_dof_map", None)
        rows = dof_display_rows(mapping or {})
        return (("Node", "UX", "UY", "RZ"), rows or [("Unavailable", "-", "-", "-")])

    def _format_value_at(self, values: tuple[object, ...], index: int) -> str:
        if index >= len(values):
            return "-"
        return format_scalar(values[index], tolerance=self._display_tolerance())

    def _format_number(self, value: object) -> str:
        return format_scalar(value, tolerance=self._display_tolerance())

    def _new_model(self) -> None:
        builder = ask_new_model(self.root)
        if builder is None:
            self._write_status("New model canceled.")
            return
        self.model_canvas.load_builder(builder)
        self.property_panel.sync_from_canvas()
        self.property_panel.show_command(self.selected_command.get())
        self.latest_static_results = None
        self.static_analysis_error = None
        self._refresh_object_tree()
        self._write_status(f"New model created: {builder.model.name}.")
        for message in getattr(builder, "creation_messages", []):
            self._write_status(message)

    def _save_xml(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save Model XML",
            defaultextension=".xml",
            filetypes=(("XML files", "*.xml"), ("All files", "*.*")),
        )
        if not path:
            self._write_status("Save XML canceled.")
            return
        try:
            self.model_canvas.builder.export_xml(path)
        except Exception as exc:
            self._write_status(f"Save XML failed: {exc}")
            return
        self._write_status(f"Saved XML: {path}")

    def _show_selection(self, kind: str | None, obj: object | None) -> None:
        self.property_panel.show_selection(kind, obj)
        if not hasattr(self, "object_tree"):
            return
        if kind == "node" and obj is not None:
            self.object_tree.select_objects(("node", obj.id))
        elif kind == "element" and obj is not None:
            self.object_tree.select_objects(("element", obj.id))
        elif kind == "multi" and obj is not None:
            self.object_tree.select_objects(obj)
        elif kind is None:
            self.object_tree.select_objects(None)

    def _select_from_tree(self, kind: str, object_id: str) -> None:
        if kind == "node":
            self.model_canvas.select_node(int(object_id))
            self._write_status(f"Selected node {object_id} from object tree.")
        elif kind == "element":
            self.model_canvas.select_element(object_id)
            self._write_status(f"Selected member {object_id} from object tree.")
        elif kind == "support":
            self.model_canvas.select_node(int(object_id))
            self._write_status(f"Selected support at node {object_id} from object tree.")
        elif kind == "mass":
            self.model_canvas.select_node(int(object_id))
            self._write_status(f"Selected mass at node {object_id} from object tree.")
        elif kind == "diaphragm":
            self.property_panel.show_diaphragm_group(object_id)
            self.object_tree.select_objects(("diaphragm", object_id))
            self._write_status(f"Selected diaphragm group {object_id} from object tree.")
        else:
            self._write_status(f"Selected {kind} {object_id}. Canvas highlighting is pending for this object type.")

    def _refresh_object_tree(self) -> None:
        if hasattr(self, "object_tree") and hasattr(self, "model_canvas"):
            self.object_tree.refresh(self.model_canvas.builder.model)

    def _write_status(self, message: str) -> None:
        self.status_message.set(message)
        self.log.configure(state="normal")
        if not message.endswith("."):
            message = f"{message}."
        self.log.insert("end", f"{message}\n")
        lines = self.log.get("1.0", "end-1c").splitlines()
        if len(lines) > 12:
            self.log.delete("1.0", f"{len(lines) - 11}.0")
        self.log.see("end")
        self.log.configure(state="disabled")


DesktopMainWindow = MainWindow
