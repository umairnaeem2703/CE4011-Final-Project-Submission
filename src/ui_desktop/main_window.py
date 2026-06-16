"""Minimal Tkinter desktop shell for the structural analysis app."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections.abc import Mapping

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    from banded_solver import UnstableStructureError
    from model_builder import ModelBuilder
    from parser import XMLParser
    from structural_validator import StructuralValidator
    from ui.static_analysis import run_static_analysis
    from visualizer import build_member_review_profile, plot_static_deformed_shape, plot_static_nvm_diagram
except ImportError:  # pragma: no cover - used when launched as python -m src.ui_desktop.app
    from ..banded_solver import UnstableStructureError
    from ..model_builder import ModelBuilder
    from ..parser import XMLParser
    from ..structural_validator import StructuralValidator
    from ..ui.static_analysis import run_static_analysis
    from ..visualizer import build_member_review_profile, plot_static_deformed_shape, plot_static_nvm_diagram

from .canvas import ModelCanvas
from .object_tree import ObjectTreePanel
from .property_panel import PropertyPanel
from .result_formatting import (
    DEFAULT_DISPLAY_TOLERANCE,
    dof_equation_labels,
    dof_display_rows,
    format_scalar,
    format_vector,
    labeled_matrix_columns,
    labeled_matrix_rows,
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
        self.result_viewer_window = None
        self.result_viewer_notebook = None
        self.result_viewer_table_tab = None
        self.result_viewer_shell_tab = None
        self.result_viewer_message = None
        self.result_viewer_plot_notebook = None
        self.result_viewer_plot_frames = {}
        self.result_viewer_plot_canvases = {}
        self.result_viewer_member_tab = None
        self.result_viewer_member_selector = None
        self.result_viewer_member_message = None
        self.result_viewer_member_notebook = None
        self.result_viewer_member_frames = {}
        self.result_viewer_member_forces_tree = None
        self.result_viewer_member_nvm_container = None
        self.result_viewer_member_nvm_canvas = None
        self.result_viewer_member_var = None
        self.result_viewer_member_plot_container = None
        self.result_viewer_member_plot_canvas = None
        self.result_viewer_member_canvas = None
        self.result_viewer_member_canvas_geometry = None
        self.result_viewer_member_profile_signature = None
        self.result_viewer_member_suppress_cursor_callback = False
        self.result_viewer_member_cursor_var = None
        self.result_viewer_member_cursor_scale = None
        self.result_viewer_member_display_mode_var = None
        self.result_viewer_member_display_mode_selector = None
        self.result_viewer_member_scroll_var = None
        self.result_viewer_member_show_max_var = None
        self.result_viewer_member_profile = None
        self.result_viewer_member_review_state = None
        self.result_viewer_member_current_location_var = None
        self.result_viewer_member_current_n_var = None
        self.result_viewer_member_current_v_var = None
        self.result_viewer_member_current_m_var = None
        self.result_viewer_member_current_disp_var = None
        self.result_viewer_member_max_n_var = None
        self.result_viewer_member_max_v_var = None
        self.result_viewer_member_max_m_var = None
        self.result_viewer_member_max_disp_var = None
        self.selected_member_id = None
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
        if name == "Open XML":
            self._open_xml()
            return
        if name == "Save XML":
            self._save_xml()
            return
        if name == "Validate":
            self._validate_model()
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
        window = self._create_static_results_window()
        self._refresh_static_result_table()
        self._refresh_static_viewer()
        notebook = getattr(self, "result_viewer_notebook", None)
        table_tab = getattr(self, "result_viewer_table_tab", None)
        if notebook is not None and table_tab is not None:
            notebook.select(table_tab)
        if getattr(self, "latest_static_results", None) is None:
            self._write_status("Run Static Analysis first.")
            return
        self._write_status("Static results opened.")

    def _show_complete_model_static_viewer(self) -> None:
        window = self._create_static_results_window()
        self._refresh_static_result_table()
        self._refresh_static_viewer()
        notebook = getattr(self, "result_viewer_notebook", None)
        shell_tab = getattr(self, "result_viewer_shell_tab", None)
        if notebook is not None and shell_tab is not None:
            notebook.select(shell_tab)
        if getattr(self, "latest_static_results", None) is None:
            self._write_status("Run Static Analysis first.")
            return
        self._write_status("Complete Model Static Viewer opened.")

    def _create_static_results_window(self) -> tk.Toplevel:
        if self.result_viewer_window is not None and self.result_viewer_window.winfo_exists():
            self.result_viewer_window.lift()
            self.result_viewer_window.focus_force()
            return self.result_viewer_window

        window = tk.Toplevel(self.root)
        window.title("Static Results")
        window.geometry("980x640")
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)
        window.protocol("WM_DELETE_WINDOW", self._close_static_results_window)
        self.result_viewer_window = window

        header = ttk.Frame(window)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Static Results").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Refresh Viewer", command=self._refresh_static_viewer).grid(row=0, column=1, sticky="e")

        body = ttk.Notebook(window)
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.result_viewer_notebook = body

        table_tab = ttk.Frame(body, padding=6)
        viewer_tab = ttk.Frame(body, padding=6)
        member_tab = ttk.Frame(body, padding=6)
        body.add(table_tab, text="Tables")
        body.add(viewer_tab, text="Complete Model Static Viewer")
        body.add(member_tab, text="Individual Member Result Viewer")
        self.result_viewer_table_tab = table_tab
        self.result_viewer_shell_tab = viewer_tab
        self.result_viewer_member_tab = member_tab

        self._build_static_results_table_tab(table_tab)
        self._build_static_results_viewer_tab(viewer_tab)
        self._build_individual_member_results_viewer_tab(member_tab)
        return window

    def _close_static_results_window(self) -> None:
        if self.result_viewer_window is not None and self.result_viewer_window.winfo_exists():
            self.result_viewer_window.destroy()
        self.result_viewer_window = None
        self.result_viewer_notebook = None
        self.result_viewer_message = None
        self.result_viewer_plot_notebook = None
        self.result_viewer_plot_frames = {}
        self.result_viewer_plot_canvases = {}
        self.result_viewer_table_tab = None
        self.result_viewer_shell_tab = None
        self.result_viewer_member_tab = None
        self.result_viewer_member_selector = None
        self.result_viewer_member_message = None
        self.result_viewer_member_notebook = None
        self.result_viewer_member_frames = {}
        self.result_viewer_member_forces_tree = None
        self.result_viewer_member_nvm_container = None
        self.result_viewer_member_nvm_canvas = None
        self.result_viewer_member_var = None
        self.result_viewer_member_plot_container = None
        self.result_viewer_member_plot_canvas = None
        self.result_viewer_member_canvas = None
        self.result_viewer_member_canvas_geometry = None
        self.result_viewer_member_profile_signature = None
        self.result_viewer_member_suppress_cursor_callback = False
        self.result_viewer_member_cursor_var = None
        self.result_viewer_member_cursor_scale = None
        self.result_viewer_member_display_mode_var = None
        self.result_viewer_member_display_mode_selector = None
        self.result_viewer_member_scroll_var = None
        self.result_viewer_member_show_max_var = None
        self.result_viewer_member_profile = None
        self.result_viewer_member_review_state = None
        self.result_viewer_member_current_location_var = None
        self.result_viewer_member_current_n_var = None
        self.result_viewer_member_current_v_var = None
        self.result_viewer_member_current_m_var = None
        self.result_viewer_member_current_disp_var = None
        self.result_viewer_member_max_n_var = None
        self.result_viewer_member_max_v_var = None
        self.result_viewer_member_max_m_var = None
        self.result_viewer_member_max_disp_var = None

    def _build_static_results_table_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        categories = tuple(self._static_result_categories())
        self.result_view_category = tk.StringVar(value=categories[0])
        selector = ttk.Combobox(parent, textvariable=self.result_view_category, values=categories, state="readonly")
        selector.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_static_result_table())

        controls = ttk.Frame(parent)
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        controls.columnconfigure(2, weight=1)
        ttk.Label(controls, text="Display tolerance").grid(row=0, column=0, sticky="w")
        self.result_tolerance_var = tk.StringVar(value=f"{self._display_tolerance():g}")
        tolerance_entry = ttk.Entry(controls, textvariable=self.result_tolerance_var, width=10)
        tolerance_entry.grid(row=0, column=1, padx=(8, 4), sticky="w")
        tolerance_entry.bind("<Return>", lambda _event: self._apply_result_tolerance())
        ttk.Button(controls, text="Apply", command=self._apply_result_tolerance).grid(row=0, column=2, sticky="w")

        frame = ttk.Frame(parent)
        frame.grid(row=2, column=0, sticky="nsew")
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

    def _build_static_results_viewer_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        controls = ttk.Frame(parent)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        for column in range(4):
            controls.columnconfigure(column, weight=1)
        ttk.Button(controls, text="Deformed Shape", command=lambda: self._select_static_viewer_tab("deformed")).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(controls, text="Axial Force N", command=lambda: self._select_static_viewer_tab("axial")).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(controls, text="Shear Force V", command=lambda: self._select_static_viewer_tab("shear")).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(controls, text="Bending Moment M", command=lambda: self._select_static_viewer_tab("moment")).grid(row=0, column=3, sticky="ew", padx=(4, 0))

        self.result_viewer_message = tk.StringVar(value="Complete model viewer shell is ready for the stored Static result.")
        ttk.Label(parent, textvariable=self.result_viewer_message).grid(row=1, column=0, sticky="w", pady=(0, 6))

        notebook = ttk.Notebook(parent)
        notebook.grid(row=2, column=0, sticky="nsew")
        self.result_viewer_plot_notebook = notebook

        self.result_viewer_plot_frames = {
            "deformed": ttk.Frame(notebook, padding=6),
            "axial": ttk.Frame(notebook, padding=6),
            "shear": ttk.Frame(notebook, padding=6),
            "moment": ttk.Frame(notebook, padding=6),
        }
        notebook.add(self.result_viewer_plot_frames["deformed"], text="Deformed Shape")
        notebook.add(self.result_viewer_plot_frames["axial"], text="Axial Force N")
        notebook.add(self.result_viewer_plot_frames["shear"], text="Shear Force V")
        notebook.add(self.result_viewer_plot_frames["moment"], text="Bending Moment M")
        self._refresh_static_viewer()

    def _build_individual_member_results_viewer_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(3, weight=1)

        controls = ttk.Frame(parent)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(4, weight=1)
        ttk.Label(controls, text="Member").grid(row=0, column=0, sticky="w")
        self.result_viewer_member_var = tk.StringVar(value="")
        self.result_viewer_member_selector = ttk.Combobox(controls, textvariable=self.result_viewer_member_var, state="readonly")
        self.result_viewer_member_selector.grid(row=0, column=1, sticky="ew", padx=(8, 4))
        self.result_viewer_member_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_individual_member_viewer())
        ttk.Button(controls, text="Use Canvas Selection", command=self._sync_individual_member_from_selection).grid(row=0, column=2, sticky="w", padx=(0, 10))

        ttk.Label(controls, text="Displacement").grid(row=0, column=3, sticky="w")
        self.result_viewer_member_display_mode_var = tk.StringVar(value="Absolute")
        self.result_viewer_member_display_mode_selector = ttk.Combobox(
            controls,
            textvariable=self.result_viewer_member_display_mode_var,
            values=("Absolute", "Relative to Member Minimum", "Relative to Member Ends"),
            state="readonly",
            width=24,
        )
        self.result_viewer_member_display_mode_selector.grid(row=0, column=4, sticky="ew", padx=(8, 4))
        self.result_viewer_member_display_mode_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_individual_member_viewer())
        self.result_viewer_member_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls,
            text="Scroll for Values",
            variable=self.result_viewer_member_scroll_var,
            command=self._update_member_review_cursor_only,
        ).grid(row=0, column=5, sticky="w", padx=(0, 10))
        self.result_viewer_member_show_max_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls,
            text="Show Max",
            variable=self.result_viewer_member_show_max_var,
            command=self._refresh_individual_member_viewer,
        ).grid(row=0, column=6, sticky="w")

        self.result_viewer_member_message = tk.StringVar(value="Select a member to review static results.")
        ttk.Label(parent, textvariable=self.result_viewer_member_message).grid(row=1, column=0, sticky="w", pady=(0, 6))

        cursor_bar = ttk.Frame(parent)
        cursor_bar.grid(row=2, column=0, sticky="ew", pady=(0, 6))
        cursor_bar.columnconfigure(2, weight=1)
        ttk.Label(cursor_bar, text="Location").grid(row=0, column=0, sticky="w")
        self.result_viewer_member_cursor_var = tk.StringVar(value="0")
        cursor_entry = ttk.Entry(cursor_bar, textvariable=self.result_viewer_member_cursor_var, width=10)
        cursor_entry.grid(row=0, column=1, sticky="w", padx=(8, 8))
        cursor_entry.bind("<Return>", lambda _event: self._apply_member_review_cursor())
        self.result_viewer_member_cursor_scale = ttk.Scale(cursor_bar, from_=0.0, to=1.0, orient=tk.HORIZONTAL, command=self._on_member_review_cursor_changed)
        self.result_viewer_member_cursor_scale.grid(row=0, column=2, sticky="ew", padx=(0, 8))

        jump_buttons = ttk.Frame(cursor_bar)
        jump_buttons.grid(row=0, column=3, sticky="e")
        for column, (label, target) in enumerate(
            (
                ("I-End", "i"),
                ("J-End", "j"),
                ("Max N", "max_n"),
                ("Max V", "max_v"),
                ("Max M", "max_m"),
                ("Max Disp", "max_disp"),
            )
        ):
            ttk.Button(jump_buttons, text=label, command=lambda jump_target=target: self._jump_member_review_cursor(jump_target)).grid(row=0, column=column, padx=(0, 4))

        body = ttk.Frame(parent)
        body.grid(row=3, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        plot_frame = ttk.Frame(body)
        plot_frame.grid(row=0, column=0, sticky="nsew")
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        self.result_viewer_member_plot_container = ttk.Frame(plot_frame)
        self.result_viewer_member_plot_container.grid(row=0, column=0, sticky="nsew")

        values_frame = ttk.LabelFrame(body, text="Location / Values", padding=8)
        values_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        values_frame.columnconfigure(1, weight=1)

        current_frame = ttk.LabelFrame(values_frame, text="Current", padding=6)
        current_frame.grid(row=0, column=0, sticky="ew")
        current_frame.columnconfigure(1, weight=1)
        extrema_frame = ttk.LabelFrame(values_frame, text="Extrema", padding=6)
        extrema_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        extrema_frame.columnconfigure(1, weight=1)

        self.result_viewer_member_current_location_var = tk.StringVar(value="-")
        self.result_viewer_member_current_n_var = tk.StringVar(value="-")
        self.result_viewer_member_current_v_var = tk.StringVar(value="-")
        self.result_viewer_member_current_m_var = tk.StringVar(value="-")
        self.result_viewer_member_current_disp_var = tk.StringVar(value="-")
        self.result_viewer_member_max_n_var = tk.StringVar(value="-")
        self.result_viewer_member_max_v_var = tk.StringVar(value="-")
        self.result_viewer_member_max_m_var = tk.StringVar(value="-")
        self.result_viewer_member_max_disp_var = tk.StringVar(value="-")

        summary_rows = (
            (current_frame, "Location", self.result_viewer_member_current_location_var),
            (current_frame, "N", self.result_viewer_member_current_n_var),
            (current_frame, "V", self.result_viewer_member_current_v_var),
            (current_frame, "M", self.result_viewer_member_current_m_var),
            (current_frame, "Disp", self.result_viewer_member_current_disp_var),
            (extrema_frame, "Max N", self.result_viewer_member_max_n_var),
            (extrema_frame, "Max V", self.result_viewer_member_max_v_var),
            (extrema_frame, "Max M", self.result_viewer_member_max_m_var),
            (extrema_frame, "Max Disp", self.result_viewer_member_max_disp_var),
        )
        for row, (frame, label, value_var) in enumerate(summary_rows):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
            ttk.Label(frame, textvariable=value_var, wraplength=240, justify="left").grid(row=row, column=1, sticky="ew", pady=2)

        self.result_viewer_member_frames = {"plot": plot_frame, "values": values_frame}
        self._refresh_individual_member_viewer()

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

    def _select_static_viewer_tab(self, key: str) -> None:
        notebook = self.result_viewer_plot_notebook
        if notebook is None:
            return
        frame = self.result_viewer_plot_frames.get(key)
        if frame is not None:
            notebook.select(frame)

    def _available_member_ids(self) -> list[object]:
        results = self.latest_static_results
        if results is None:
            return []
        member_ids: list[object] = []
        for attribute in ("member_forces", "element_forces", "nvm_data"):
            data = getattr(results, attribute, None) or {}
            member_ids.extend(list(data.keys()))
        return list(dict.fromkeys(member_ids))

    def _refresh_individual_member_viewer_member_options(self) -> None:
        selector = getattr(self, "result_viewer_member_selector", None)
        member_var = getattr(self, "result_viewer_member_var", None)
        if selector is None or member_var is None:
            return

        member_ids = [str(member_id) for member_id in self._available_member_ids()]
        selector.configure(values=member_ids)
        if not member_ids:
            member_var.set("")
            return

        current_key = self._resolve_available_member_key(member_var.get())
        if current_key is not None:
            member_var.set(str(current_key))
            return

        selected_key = self._resolve_available_member_key(getattr(self, "selected_member_id", None))
        if selected_key is not None:
            member_var.set(str(selected_key))
            return

        member_var.set(member_ids[0])

    def _resolve_available_member_key(self, member_id: object) -> object | None:
        for key in self._available_member_ids():
            if str(key) == str(member_id):
                return key
        return None

    def _sync_individual_member_from_selection(self) -> None:
        selected_member_id = getattr(self, "selected_member_id", None)
        if selected_member_id is None:
            self._write_status("Select a member first.")
            return
        if getattr(self, "result_viewer_member_var", None) is None:
            return
        self.result_viewer_member_var.set(str(selected_member_id))
        self._refresh_individual_member_viewer()

    def _current_individual_member_id(self) -> object | None:
        if getattr(self, "result_viewer_member_var", None) is None:
            return self._resolve_available_member_key(getattr(self, "selected_member_id", None))
        return self._resolve_available_member_key(self.result_viewer_member_var.get())

    def _current_member_review_display_mode(self) -> str:
        var = getattr(self, "result_viewer_member_display_mode_var", None)
        if var is None:
            return "absolute"
        raw = var.get() if hasattr(var, "get") else var
        normalized = str(raw).strip().lower()
        if normalized in {"relative to member minimum", "relative minimum", "relative_min"}:
            return "relative_min"
        if normalized in {"relative to member ends", "relative ends", "relative_ends"}:
            return "relative_ends"
        return "absolute"

    def _member_review_cursor_value(self) -> float:
        cursor_var = getattr(self, "result_viewer_member_cursor_var", None)
        if cursor_var is None:
            return 0.0
        raw = cursor_var.get() if hasattr(cursor_var, "get") else cursor_var
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.0

    def _member_review_cursor_length(self) -> float:
        profile = getattr(self, "result_viewer_member_profile", None) or {}
        length = profile.get("length", 1.0) or 1.0
        try:
            return float(length)
        except (TypeError, ValueError):
            return 1.0

    def _set_member_review_cursor(self, value: float, *, refresh: bool = True) -> None:
        cursor_value = max(0.0, min(float(value), self._member_review_cursor_length()))
        if getattr(self, "result_viewer_member_cursor_var", None) is not None:
            self.result_viewer_member_cursor_var.set(f"{cursor_value:g}")
        scale = getattr(self, "result_viewer_member_cursor_scale", None)
        if scale is not None and hasattr(scale, "set"):
            self.result_viewer_member_suppress_cursor_callback = True
            try:
                scale.set(cursor_value)
            finally:
                self.result_viewer_member_suppress_cursor_callback = False
        if refresh:
            self._update_member_review_cursor_only()

    def _apply_member_review_cursor(self) -> None:
        self._set_member_review_cursor(self._member_review_cursor_value())

    def _on_member_review_cursor_changed(self, value: object) -> None:
        if getattr(self, "result_viewer_member_suppress_cursor_callback", False):
            return
        try:
            cursor_value = float(value)
        except (TypeError, ValueError):
            cursor_value = 0.0
        cursor_value = max(0.0, min(cursor_value, self._member_review_cursor_length()))
        if getattr(self, "result_viewer_member_cursor_var", None) is not None:
            self.result_viewer_member_cursor_var.set(f"{cursor_value:g}")
        self._update_member_review_cursor_only()

    def _jump_member_review_cursor(self, target: str) -> None:
        review_state = getattr(self, "result_viewer_member_review_state", None) or {}
        maxima = review_state.get("maxima", {}) or {}
        target_map = {
            "i": 0.0,
            "j": self._member_review_cursor_length(),
            "max_n": maxima.get("N", {}).get("x", 0.0),
            "max_v": maxima.get("V", {}).get("x", 0.0),
            "max_m": maxima.get("M", {}).get("x", 0.0),
            "max_disp": maxima.get("disp", {}).get("x", 0.0),
        }
        self._set_member_review_cursor(target_map.get(target, 0.0))

    def _refresh_individual_member_viewer(self) -> None:
        if getattr(self, "result_viewer_member_message", None) is None:
            return

        self._refresh_individual_member_viewer_member_options()
        if getattr(self, "latest_static_results", None) is None:
            self.result_viewer_member_message.set("Run Static Analysis first.")
            self._render_member_review_placeholder("Run Static Analysis first.")
            return

        member_id = self._current_individual_member_id()
        if member_id is None:
            self.result_viewer_member_message.set("Select a valid member.")
            self._render_member_review_placeholder("Select a valid member.")
            return

        model = getattr(getattr(self, "model_canvas", None), "builder", None)
        model = getattr(model, "model", None)
        if model is None:
            self.result_viewer_member_message.set("No model available for Static results.")
            self._render_member_review_placeholder("No model available for Static results.")
            return
        show_max = self._bool_var_value(getattr(self, "result_viewer_member_show_max_var", None), default=True)
        display_mode = self._current_member_review_display_mode()
        signature = (id(model), id(self.latest_static_results), str(member_id), display_mode, show_max)
        if signature == getattr(self, "result_viewer_member_profile_signature", None) and getattr(self, "result_viewer_member_profile", None):
            self._configure_member_review_scale()
            self._update_member_review_cursor_only()
            self.result_viewer_member_message.set(f"Member {member_id} selected for static review.")
            return
        profile = build_member_review_profile(model, self.latest_static_results, member_id)
        if profile is None:
            self.result_viewer_member_message.set("Select a valid member.")
            self._render_member_review_placeholder("Select a valid member.")
            return
        if not getattr(self.latest_static_results, "displacements", None):
            profile = dict(profile)
            profile["disp"] = []
            profile["disp_label"] = "Displacement unavailable"

        self.result_viewer_member_profile = profile
        self.result_viewer_member_profile_signature = signature
        length = self._configure_member_review_scale()

        cursor_value = self._member_review_cursor_value()
        if cursor_value > length or cursor_value < 0.0:
            cursor_value = 0.0
        self._set_member_review_cursor(cursor_value, refresh=False)

        review_state = self._render_member_review_plot(profile)
        self.result_viewer_member_review_state = review_state
        self._update_member_review_cursor_only()
        self.result_viewer_member_message.set(f"Member {member_id} selected for static review.")

    def _configure_member_review_scale(self) -> float:
        length = self._member_review_cursor_length()
        if length <= 0.0:
            length = 1.0
        scale = getattr(self, "result_viewer_member_cursor_scale", None)
        if scale is not None and hasattr(scale, "configure"):
            scale.configure(from_=0.0, to=length)
        return length

    def _render_member_review_plot(self, profile: dict) -> dict:
        container = getattr(self, "result_viewer_member_plot_container", None)
        if container is None:
            return {"cursor_x": 0.0, "current": {}, "end_forces": {}, "maxima": {}}

        self._clear_viewer_container(container)
        canvas = tk.Canvas(container, background="white", highlightthickness=0, height=520)
        canvas.grid(row=0, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        self.result_viewer_member_canvas = canvas
        self.result_viewer_member_plot_canvas = canvas
        review_state = {
            "cursor_x": self._member_review_cursor_value(),
            "current": {},
            "end_forces": profile.get("end_forces", {}) or {},
            "maxima": {},
            "series": self._member_review_display_series(profile),
        }
        review_state["maxima"] = self._member_review_series_extrema(review_state["series"])
        self.result_viewer_member_review_state = review_state
        if hasattr(canvas, "bind"):
            canvas.bind("<Configure>", lambda _event: self._redraw_member_review_canvas())
        self._redraw_member_review_canvas()
        return review_state

    def _member_review_display_series(self, profile: Mapping[str, object]) -> dict[str, object]:
        stations = list(profile.get("stations", []) or [])
        disp_values = list(profile.get("disp", []) or [])
        if self._current_member_review_display_mode() == "relative_min" and disp_values:
            min_value = min(disp_values)
            disp_values = [value - min_value for value in disp_values]
        elif self._current_member_review_display_mode() == "relative_ends" and len(disp_values) >= 2 and stations:
            start_value = disp_values[0]
            end_value = disp_values[-1]
            length = stations[-1] if stations[-1] else 1.0
            disp_values = [value - (start_value + (end_value - start_value) * (station / length)) for station, value in zip(stations, disp_values)]
        return {
            "stations": stations,
            "N": list(profile.get("N", []) or []),
            "V": list(profile.get("V", []) or []),
            "M": list(profile.get("M", []) or []),
            "disp": disp_values,
        }

    def _member_review_series_extrema(self, series: Mapping[str, object]) -> dict[str, dict[str, object]]:
        maxima: dict[str, dict[str, object]] = {}
        stations = list(series.get("stations", []) or [])
        for key in ("N", "V", "M", "disp"):
            values = list(series.get(key, []) or [])
            if not stations or not values:
                continue
            count = min(len(stations), len(values))
            max_index = max(range(count), key=lambda idx: abs(values[idx]))
            maxima[key] = {"x": stations[max_index], "value": values[max_index], "index": max_index}
        return maxima

    def _series_value_at_cursor(self, stations: list[float], values: list[float], x_value: float) -> float | None:
        if not stations or not values:
            return None
        count = min(len(stations), len(values))
        if count <= 0:
            return None
        if x_value <= stations[0]:
            return values[0]
        if x_value >= stations[count - 1]:
            return values[count - 1]
        for index in range(count - 1):
            x0 = stations[index]
            x1 = stations[index + 1]
            if x0 <= x_value <= x1:
                if x1 == x0:
                    return values[index]
                ratio = (x_value - x0) / (x1 - x0)
                return values[index] + ratio * (values[index + 1] - values[index])
        return values[count - 1]

    def _member_review_current_values(self, cursor_x: float) -> dict[str, float | None]:
        review_state = getattr(self, "result_viewer_member_review_state", None) or {}
        series = review_state.get("series", {}) or {}
        stations = list(series.get("stations", []) or [])
        return {
            key: self._series_value_at_cursor(stations, list(series.get(key, []) or []), cursor_x)
            for key in ("N", "V", "M", "disp")
        }

    def _redraw_member_review_canvas(self) -> None:
        canvas = getattr(self, "result_viewer_member_canvas", None)
        if canvas is None:
            return
        try:
            if hasattr(canvas, "winfo_exists") and not canvas.winfo_exists():
                return
            width = max(int(canvas.winfo_width()), 760) if hasattr(canvas, "winfo_width") else 760
            height = max(int(canvas.winfo_height()), 520) if hasattr(canvas, "winfo_height") else 520
        except tk.TclError:
            return

        review_state = getattr(self, "result_viewer_member_review_state", None) or {}
        profile = getattr(self, "result_viewer_member_profile", None) or {}
        series = review_state.get("series", {}) or self._member_review_display_series(profile)
        review_state["series"] = series
        review_state["maxima"] = self._member_review_series_extrema(series)
        self.result_viewer_member_review_state = review_state
        self.result_viewer_member_canvas_geometry = None

        canvas.delete("all")
        x0 = 92
        x1 = max(width - 28, x0 + 100)
        top = 22
        bottom = max(height - 26, top + 120)
        row_count = 5
        row_height = (bottom - top) / row_count
        length = max(self._member_review_cursor_length(), 1.0)
        stations = list(series.get("stations", []) or [])
        rows = [
            ("end", "Member End Forces", [], ""),
            ("N", "Axial Force N", list(series.get("N", []) or []), "N"),
            ("V", "Shear Force V", list(series.get("V", []) or []), "V"),
            ("M", "Bending Moment M", list(series.get("M", []) or []), "M"),
            ("disp", profile.get("disp_label", "Displacement"), list(series.get("disp", []) or []), "disp"),
        ]
        row_bounds = []
        for row_index, (key, title, values, state_key) in enumerate(rows):
            row_top = top + row_index * row_height
            row_bottom = row_top + row_height - 8
            row_center = (row_top + row_bottom) / 2
            row_bounds.append((key, row_top, row_bottom, row_center))
            canvas.create_text(12, row_top + 12, text=title, anchor="w", font=("Segoe UI", 9, "bold"))
            canvas.create_line(x0, row_center, x1, row_center, fill="#666666")

            if key == "end":
                end_forces = profile.get("end_forces", {}) or {}
                self._draw_member_end_force_arrows(canvas, x0, x1, row_top, row_bottom, end_forces)
                continue

            point_count = min(len(stations), len(values))
            if point_count == 0:
                placeholder = "No N/V/M data available." if state_key in {"N", "V", "M"} else "Displacement unavailable."
                canvas.create_text((x0 + x1) / 2, row_center, text=placeholder, anchor="center", fill="#666666", font=("Segoe UI", 9))
                continue
            max_abs = max((abs(value) for value in values[:point_count]), default=0.0) or 1.0
            y_scale = (row_height * 0.32) / max_abs
            self._draw_member_review_series(
                canvas,
                stations[:point_count],
                values[:point_count],
                x0,
                x1,
                row_center,
                y_scale,
                length,
                color_by_sign=state_key in {"N", "V", "M"},
            )
            if self._bool_var_value(getattr(self, "result_viewer_member_show_max_var", None), default=True):
                extrema = review_state.get("maxima", {}).get(state_key)
                if extrema:
                    px = x0 + (float(extrema.get("x", 0.0)) / length) * (x1 - x0)
                    py = row_center - float(extrema.get("value", 0.0)) * y_scale
                    canvas.create_oval(px - 4, py - 4, px + 4, py + 4, fill="#222222", outline="")
                    canvas.create_text(px + 6, py - 8, text=self._format_number(extrema.get("value", 0.0)), anchor="w", fill="#222222", font=("Segoe UI", 8))

        self.result_viewer_member_canvas_geometry = {
            "x0": x0,
            "x1": x1,
            "top": top,
            "bottom": bottom,
            "length": length,
            "row_bounds": row_bounds,
        }
        self._update_member_review_cursor_graphics()

    def _member_review_value_color(self, value: object) -> str:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = 0.0
        if numeric_value > 0.0:
            return "#2e7d32"
        if numeric_value < 0.0:
            return "#c62828"
        return "#555555"

    def _draw_member_review_series(
        self,
        canvas: tk.Canvas,
        stations: list[float],
        values: list[float],
        x0: float,
        x1: float,
        row_center: float,
        y_scale: float,
        length: float,
        *,
        color_by_sign: bool,
    ) -> None:
        if len(stations) < 2 or len(values) < 2:
            return

        def point(station: float, value: float) -> tuple[float, float]:
            return (x0 + (station / length) * (x1 - x0), row_center - value * y_scale)

        for index in range(len(stations) - 1):
            s0, s1 = stations[index], stations[index + 1]
            v0, v1 = values[index], values[index + 1]
            p0 = point(s0, v0)
            p1 = point(s1, v1)
            if color_by_sign and v0 * v1 < 0.0:
                ratio = abs(v0) / (abs(v0) + abs(v1))
                sz = s0 + ratio * (s1 - s0)
                pz = point(sz, 0.0)
                canvas.create_polygon(
                    p0[0], row_center, p0[0], p0[1], pz[0], pz[1], p0[0], row_center,
                    fill=self._member_review_value_color(v0),
                    outline="",
                    stipple="gray25",
                )
                canvas.create_polygon(
                    pz[0], row_center, pz[0], pz[1], p1[0], p1[1], p1[0], row_center,
                    fill=self._member_review_value_color(v1),
                    outline="",
                    stipple="gray25",
                )
                canvas.create_line(*p0, *pz, fill=self._member_review_value_color(v0), width=2)
                canvas.create_line(*pz, *p1, fill=self._member_review_value_color(v1), width=2)
                continue
            color = self._member_review_value_color((v0 + v1) / 2.0) if color_by_sign else "#111111"
            if color_by_sign:
                canvas.create_polygon(
                    p0[0], row_center, p0[0], p0[1], p1[0], p1[1], p1[0], row_center,
                    fill=color,
                    outline="",
                    stipple="gray25",
                )
            canvas.create_line(*p0, *p1, fill=color, width=2)

    def _draw_member_end_force_arrows(
        self,
        canvas: tk.Canvas,
        x0: float,
        x1: float,
        row_top: float,
        row_bottom: float,
        end_forces: Mapping[str, object],
    ) -> None:
        left_x = x0 + 88
        right_x = x1 - 88
        available_height = max(row_bottom - row_top, 60.0)
        y_n = row_top + available_height * 0.34
        y_v = row_top + available_height * 0.58
        y_m = row_top + available_height * 0.80
        canvas.create_text(left_x - 54, row_top + 16, text="I-End", anchor="w", font=("Segoe UI", 8, "bold"))
        canvas.create_text(right_x + 54, row_top + 16, text="J-End", anchor="e", font=("Segoe UI", 8, "bold"))
        self._draw_labeled_force_arrow(canvas, left_x, y_n, end_forces.get("Ni", 0.0), "N", "horizontal", text_side="right")
        self._draw_labeled_force_arrow(canvas, left_x, y_v, end_forces.get("Vi", 0.0), "V", "vertical", text_side="right")
        self._draw_labeled_moment_arrow(canvas, left_x, y_m, end_forces.get("Mi", 0.0), text_side="right")
        self._draw_labeled_force_arrow(canvas, right_x, y_n, end_forces.get("Nj", 0.0), "N", "horizontal", text_side="left")
        self._draw_labeled_force_arrow(canvas, right_x, y_v, end_forces.get("Vj", 0.0), "V", "vertical", text_side="left")
        self._draw_labeled_moment_arrow(canvas, right_x, y_m, end_forces.get("Mj", 0.0), text_side="left")

    def _draw_labeled_force_arrow(
        self,
        canvas: tk.Canvas,
        x: float,
        y: float,
        value: object,
        label: str,
        orientation: str,
        *,
        text_side: str,
    ) -> None:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = 0.0
        sign = 1.0 if numeric_value >= 0.0 else -1.0
        color = self._member_review_value_color(numeric_value)
        if orientation == "horizontal":
            dx, dy = sign * 30.0, 0.0
        else:
            dx, dy = 0.0, -sign * 22.0
        canvas.create_line(x, y, x + dx, y + dy, fill=color, width=2, arrow=tk.LAST)
        text_x = x + 38.0 if text_side == "right" else x - 38.0
        anchor = "w" if text_side == "right" else "e"
        canvas.create_text(text_x, y, text=f"{label}={self._format_number(numeric_value)}", anchor=anchor, fill=color, font=("Segoe UI", 8))

    def _draw_labeled_moment_arrow(self, canvas: tk.Canvas, x: float, y: float, value: object, *, text_side: str) -> None:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = 0.0
        color = self._member_review_value_color(numeric_value)
        radius = 13.0
        if numeric_value >= 0.0:
            points = (x - radius, y + 5, x - radius, y - radius, x + radius, y - radius, x + radius, y + 5)
        else:
            points = (x + radius, y + 5, x + radius, y - radius, x - radius, y - radius, x - radius, y + 5)
        canvas.create_line(*points, fill=color, width=2, smooth=True, arrow=tk.LAST)
        text_x = x + 38.0 if text_side == "right" else x - 38.0
        anchor = "w" if text_side == "right" else "e"
        canvas.create_text(text_x, y, text=f"M={self._format_number(numeric_value)}", anchor=anchor, fill=color, font=("Segoe UI", 8))

    def _update_member_review_cursor_only(self) -> None:
        if not getattr(self, "result_viewer_member_profile", None):
            return
        cursor_x = max(0.0, min(self._member_review_cursor_value(), self._member_review_cursor_length()))
        review_state = getattr(self, "result_viewer_member_review_state", None) or {}
        review_state["cursor_x"] = cursor_x
        review_state["current"] = self._member_review_current_values(cursor_x)
        self.result_viewer_member_review_state = review_state
        self._render_member_review_summary(review_state)
        self._update_member_review_cursor_graphics()

    def _update_member_review_cursor_graphics(self) -> None:
        canvas = getattr(self, "result_viewer_member_canvas", None)
        geometry = getattr(self, "result_viewer_member_canvas_geometry", None)
        if canvas is None or not geometry:
            return
        try:
            if hasattr(canvas, "winfo_exists") and not canvas.winfo_exists():
                return
        except tk.TclError:
            return
        canvas.delete("member_cursor")
        canvas.delete("member_cursor_value")
        cursor_x = max(0.0, min(self._member_review_cursor_value(), self._member_review_cursor_length()))
        length = geometry["length"] or 1.0
        px = geometry["x0"] + (cursor_x / length) * (geometry["x1"] - geometry["x0"])
        canvas.create_line(px, geometry["top"], px, geometry["bottom"], fill="#1f6feb", dash=(4, 3), width=2, tags="member_cursor")
        if not self._bool_var_value(getattr(self, "result_viewer_member_scroll_var", None), default=True):
            return
        review_state = getattr(self, "result_viewer_member_review_state", None) or {}
        current = review_state.get("current", {}) or {}
        series = review_state.get("series", {}) or {}
        stations = list(series.get("stations", []) or [])
        for key, _row_top, _row_bottom, row_center in geometry.get("row_bounds", []):
            if key == "end":
                continue
            values = list(series.get(key, []) or [])
            y_value = current.get(key)
            if y_value is None or not stations or not values:
                continue
            max_abs = max((abs(value) for value in values), default=0.0) or 1.0
            y_scale = ((geometry["bottom"] - geometry["top"]) / 5 * 0.32) / max_abs
            py = row_center - float(y_value) * y_scale
            canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#1f6feb", outline="", tags="member_cursor_value")
            canvas.create_text(px + 6, py - 6, text=self._format_number(y_value), anchor="w", fill="#1f6feb", font=("Segoe UI", 8), tags="member_cursor_value")

    def _render_member_review_summary(self, review_state: Mapping[str, object] | None) -> None:
        review_state = review_state or {}
        current = review_state.get("current", {}) or {}
        maxima = review_state.get("maxima", {}) or {}
        profile = getattr(self, "result_viewer_member_profile", None) or {}
        units = self._result_unit_labels()
        length_unit = units["length"]
        force_unit = units["force"]
        moment_unit = units["moment"]
        cursor_x = review_state.get("cursor_x", self._member_review_cursor_value())

        if getattr(self, "result_viewer_member_current_location_var", None) is not None:
            self.result_viewer_member_current_location_var.set(
                f"x = {self._format_number(cursor_x)} / {self._format_number(profile.get('length', 0.0))} {length_unit}"
            )
        if getattr(self, "result_viewer_member_current_n_var", None) is not None:
            self.result_viewer_member_current_n_var.set(self._member_review_value_label(current.get("N"), force_unit))
        if getattr(self, "result_viewer_member_current_v_var", None) is not None:
            self.result_viewer_member_current_v_var.set(self._member_review_value_label(current.get("V"), force_unit))
        if getattr(self, "result_viewer_member_current_m_var", None) is not None:
            self.result_viewer_member_current_m_var.set(self._member_review_value_label(current.get("M"), moment_unit))
        if getattr(self, "result_viewer_member_current_disp_var", None) is not None:
            self.result_viewer_member_current_disp_var.set(self._member_review_value_label(current.get("disp"), length_unit))

        self._set_member_review_extremum_vars("N", maxima.get("N"), force_unit)
        self._set_member_review_extremum_vars("V", maxima.get("V"), force_unit)
        self._set_member_review_extremum_vars("M", maxima.get("M"), moment_unit)
        self._set_member_review_extremum_vars("disp", maxima.get("disp"), length_unit)

    def _member_review_value_label(self, value: object, unit: str) -> str:
        if value is None:
            return "-"
        return f"{self._format_number(value)} {unit}"

    def _set_member_review_extremum_vars(self, key: str, value: Mapping[str, object] | None, unit: str) -> None:
        label = "-"
        if value:
            x_value = self._format_number(value.get("x", 0.0))
            y_value = self._format_number(value.get("value", 0.0))
            label = f"x = {x_value}, {y_value} {unit}"
        if key == "N" and getattr(self, "result_viewer_member_max_n_var", None) is not None:
            self.result_viewer_member_max_n_var.set(label)
        elif key == "V" and getattr(self, "result_viewer_member_max_v_var", None) is not None:
            self.result_viewer_member_max_v_var.set(label)
        elif key == "M" and getattr(self, "result_viewer_member_max_m_var", None) is not None:
            self.result_viewer_member_max_m_var.set(label)
        elif key == "disp" and getattr(self, "result_viewer_member_max_disp_var", None) is not None:
            self.result_viewer_member_max_disp_var.set(label)

    def _render_member_review_placeholder(self, message: str) -> None:
        if getattr(self, "result_viewer_member_plot_container", None) is not None:
            self._clear_viewer_container(self.result_viewer_member_plot_container)
            ttk.Label(self.result_viewer_member_plot_container, text=message).grid(row=0, column=0, sticky="nw")
        self.result_viewer_member_plot_canvas = None
        self.result_viewer_member_canvas = None
        self.result_viewer_member_canvas_geometry = None
        self.result_viewer_member_profile = None
        self.result_viewer_member_profile_signature = None
        self.result_viewer_member_review_state = None
        for var in (
            getattr(self, "result_viewer_member_current_location_var", None),
            getattr(self, "result_viewer_member_current_n_var", None),
            getattr(self, "result_viewer_member_current_v_var", None),
            getattr(self, "result_viewer_member_current_m_var", None),
            getattr(self, "result_viewer_member_current_disp_var", None),
            getattr(self, "result_viewer_member_max_n_var", None),
            getattr(self, "result_viewer_member_max_v_var", None),
            getattr(self, "result_viewer_member_max_m_var", None),
            getattr(self, "result_viewer_member_max_disp_var", None),
        ):
            if var is not None:
                var.set("-")

    def _bool_var_value(self, var: object, *, default: bool) -> bool:
        if var is None:
            return default
        if hasattr(var, "get"):
            return bool(var.get())
        return bool(var)

    def _refresh_static_viewer(self) -> None:
        if getattr(self, "result_viewer_message", None) is None:
            return
        if getattr(self, "latest_static_results", None) is None:
            self.result_viewer_message.set("Run Static Analysis first.")
            self._render_static_viewer_placeholder("Run Static Analysis first.")
            return
        model = getattr(getattr(self, "model_canvas", None), "builder", None)
        model = getattr(model, "model", None)
        if model is None:
            self.result_viewer_message.set("No model available for Static results.")
            self._render_static_viewer_placeholder("No model available for Static results.")
            return
        self.result_viewer_message.set("Complete model viewer shows the stored Static result.")
        self._render_static_viewer_plots()

    def _render_static_viewer_plots(self) -> None:
        frames = self.result_viewer_plot_frames or {}
        if not frames:
            return

        self.result_viewer_plot_canvases = {}
        results = self.latest_static_results
        model = getattr(getattr(self, "model_canvas", None), "builder", None)
        model = getattr(model, "model", None)
        if results is None:
            self._render_static_viewer_placeholder("Run Static Analysis first.")
            return
        if model is None:
            self._render_static_viewer_placeholder("No model available for Static results.")
            return

        if getattr(results, "displacements", None):
            self._render_figure_tab(frames.get("deformed"), "No displacement data available.", self._plot_deformed_shape, model, results)
        else:
            self._render_placeholder_frame(frames.get("deformed"), "No displacement data available.")

        if getattr(results, "nvm_data", None):
            self._render_figure_tab(frames.get("axial"), "No N/V/M data available.", self._plot_static_diagram, model, results, "N")
            self._render_figure_tab(frames.get("shear"), "No N/V/M data available.", self._plot_static_diagram, model, results, "V")
            self._render_figure_tab(frames.get("moment"), "No N/V/M data available.", self._plot_static_diagram, model, results, "M")
        else:
            for key in ("axial", "shear", "moment"):
                self._render_placeholder_frame(frames.get(key), "No N/V/M data available.")

    def _render_static_viewer_placeholder(self, placeholder: str) -> None:
        frames = self.result_viewer_plot_frames or {}
        for key in ("deformed", "axial", "shear", "moment"):
            message = "Run Static Analysis first." if key == "deformed" else placeholder
            self._render_placeholder_frame(frames.get(key), message)

    def _render_placeholder_frame(self, parent: ttk.Frame | None, message: str) -> None:
        if parent is None:
            return
        self._clear_viewer_container(parent)
        ttk.Label(parent, text=message).grid(row=0, column=0, sticky="nw")

    def _render_figure_tab(self, parent: ttk.Frame | None, placeholder: str, builder, *args) -> None:
        if parent is None:
            return
        self._clear_viewer_container(parent)
        try:
            fig, _ = builder(*args)
        except Exception as exc:
            ttk.Label(parent, text=f"{placeholder} ({exc})").grid(row=0, column=0, sticky="nw")
            return
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        canvas.draw()
        self.result_viewer_plot_canvases[parent] = canvas

    def _plot_deformed_shape(self, model, results):
        return plot_static_deformed_shape(model, results)

    def _plot_static_diagram(self, model, results, key: str):
        return plot_static_nvm_diagram(model, results, diagram_key=key, show_extrema=True)

    def _clear_viewer_container(self, parent: ttk.Frame) -> None:
        for child in parent.winfo_children():
            child.destroy()

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
        labels = dof_equation_labels(getattr(self.latest_static_results, "dof_map", None))
        rows = labeled_matrix_rows(matrix, dof_labels=labels, tolerance=self._display_tolerance())
        if not rows:
            return (("Message",), [(missing_message,)])
        return (labeled_matrix_columns(matrix, labels), rows)

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
        self._replace_desktop_model(builder, fit_view=False)
        self._write_status(f"New model created: {builder.model.name}.")
        for message in getattr(builder, "creation_messages", []):
            self._write_status(message)

    def _open_xml(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Open Model XML",
            filetypes=(("XML files", "*.xml"), ("All files", "*.*")),
        )
        if not path:
            self._write_status("Open XML canceled.")
            return
        try:
            model = XMLParser(path).parse()
            builder = ModelBuilder(model=model)
        except Exception as exc:
            messagebox.showerror("Open XML Failed", f"Could not load XML model:\n{exc}", parent=self.root)
            self._write_status(f"Open XML failed: {exc}")
            return

        self._replace_desktop_model(builder, fit_view=True)
        self._write_status(f"Opened XML: {path}")

    def _replace_desktop_model(self, builder, *, fit_view: bool) -> None:
        self.model_canvas.load_builder(builder)
        if fit_view and hasattr(self.model_canvas, "restore_full_view"):
            self.model_canvas.restore_full_view(notify=False)
        elif hasattr(self.model_canvas, "refresh_canvas"):
            self.model_canvas.refresh_canvas()
        self._refresh_object_tree()
        self._show_selection(None, None)
        self.property_panel.sync_from_canvas()
        self.property_panel.show_command(self.selected_command.get())
        self._reset_analysis_state()

    def _reset_analysis_state(self) -> None:
        self.latest_static_results = None
        self.static_analysis_error = None
        self.result_view_category = None
        self.result_view_tree = None
        self.selected_member_id = None

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

    def _validate_model(self) -> None:
        try:
            StructuralValidator(self.model_canvas.builder.model).validate()
        except UnstableStructureError as exc:
            message = str(exc) or "Model validation failed."
            messagebox.showerror("Model Validation Failed", message, parent=self.root)
            self._write_status(message)
            return
        except Exception as exc:
            message = str(exc) or "Model validation failed."
            messagebox.showerror("Model Validation Failed", message, parent=self.root)
            self._write_status(message)
            return
        self._write_status("Model validation passed.")

    def _show_selection(self, kind: str | None, obj: object | None) -> None:
        self.property_panel.show_selection(kind, obj)
        if kind == "element" and obj is not None:
            self.selected_member_id = obj.id
        elif kind is None:
            self.selected_member_id = None
        if getattr(self, "result_viewer_member_message", None) is not None:
            self._refresh_individual_member_viewer()
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
