"""Minimal Tkinter desktop shell for the structural analysis app."""

from __future__ import annotations

import csv
import math
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections.abc import Mapping

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    from banded_solver import UnstableStructureError
    from model_builder import ModelBuilder
    from parser import XMLParser
    from structural_validator import StructuralValidator
    from ui.dynamic_analysis import run_modal_analysis
    from ui.static_analysis import run_static_analysis
    from visualizer import build_member_review_profile, plot_modal_mode_shape, plot_static_deformed_shape, plot_static_nvm_diagram
except ImportError:  # pragma: no cover - used when launched as python -m src.ui_desktop.app
    from ..banded_solver import UnstableStructureError
    from ..model_builder import ModelBuilder
    from ..parser import XMLParser
    from ..structural_validator import StructuralValidator
    from ..ui.dynamic_analysis import run_modal_analysis
    from ..ui.static_analysis import run_static_analysis
    from ..visualizer import build_member_review_profile, plot_modal_mode_shape, plot_static_deformed_shape, plot_static_nvm_diagram

from .canvas import ModelCanvas
from .object_tree import ObjectTreePanel
from .property_panel import PropertyPanel
from .result_formatting import (
    DEFAULT_DISPLAY_TOLERANCE,
    dof_equation_labels,
    dof_display_rows,
    format_matrix,
    format_scalar,
    format_vector,
    labeled_matrix_columns,
    labeled_matrix_rows,
    unit_labels,
    unwrap_scalar,
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
            ("local_axes_toggle", "Local Axes"),
            ("view_action", "Full View"),
        ),
    ),
    ("Analyze", (("action", "Run Static Analysis"), ("action", "Run Modal Analysis"))),
    ("Results", (("action", "Static Results"), ("action", "Modal Results"))),
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
        self.modal_num_modes_var = tk.StringVar(value="3")
        self.modal_rayleigh_mode_i_var = tk.StringVar(value="1")
        self.modal_rayleigh_zeta_i_var = tk.StringVar(value="0.05")
        self.modal_rayleigh_mode_j_var = tk.StringVar(value="2")
        self.modal_rayleigh_zeta_j_var = tk.StringVar(value="0.05")
        self.latest_static_results = None
        self.latest_static_result = None
        self.static_analysis_error = None
        self.latest_modal_results = None
        self.latest_modal_result = None
        self.modal_analysis_error = None
        self._analysis_results_cleared = False
        self._analysis_results_clear_message = "Results were cleared because the model changed. Run analysis again."
        self.result_view_category = None
        self.result_view_tree = None
        self.result_viewer_window = None
        self.result_viewer_mode = None
        self.result_viewer_notebook = None
        self.result_viewer_section_var = None
        self.result_viewer_section_selector = None
        self.result_viewer_content_frame = None
        self.result_viewer_table_tab = None
        self.result_viewer_shell_tab = None
        self.result_viewer_message = None
        self.result_viewer_dynamic_category = None
        self.result_viewer_dynamic_message = None
        self.result_viewer_dynamic_tree = None
        self.result_viewer_dynamic_view_var = None
        self.result_viewer_dynamic_view_selector = None
        self.result_viewer_dynamic_summary_vars = {}
        self.result_viewer_dynamic_notebook = None
        self.result_viewer_dynamic_top_controls = None
        self.result_viewer_dynamic_summary_tab = None
        self.result_viewer_dynamic_mode_shapes_tab = None
        self.result_viewer_dynamic_matrices_tab = None
        self.result_viewer_dynamic_summary_tree = None
        self.result_viewer_dynamic_mode_var = None
        self.result_viewer_dynamic_mode_selector = None
        self.result_viewer_dynamic_mode_normalization_var = None
        self.result_viewer_dynamic_mode_normalization_selector = None
        self.result_viewer_dynamic_reference_dof_var = None
        self.result_viewer_dynamic_reference_dof_selector = None
        self.result_viewer_dynamic_matrix_selector = None
        self.result_viewer_dynamic_matrix_tree = None
        self.result_viewer_dynamic_mode_info_frame = None
        self.result_viewer_dynamic_mode_info_vars = {}
        self.result_viewer_dynamic_plot_frame = None
        self.result_viewer_dynamic_plot_canvas = None
        self.result_viewer_dynamic_phi_tree = None
        self.result_viewer_plot_notebook = None
        self.result_viewer_plot_view_var = None
        self.result_viewer_plot_view_selector = None
        self.result_viewer_plot_content_frame = None
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
        self.workspace_panedwindow = None
        self.workspace_left_frame = None
        self.workspace_canvas_frame = None

        self._configure_grid()
        self._build_command_area()
        self._build_workspace_area()
        self._build_right_panel()
        self._build_status_panel()
        self._refresh_object_tree()

    def _make_string_var(self, master, value: str):
        try:
            return tk.StringVar(master=master, value=value)
        except Exception:
            class _FallbackVar:
                def __init__(self, initial: str):
                    self.value = initial

                def get(self):
                    return self.value

                def set(self, value):
                    self.value = value

            return _FallbackVar(value)

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
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        for menu_name, items in COMMAND_TABS:
            menu = tk.Menu(self.menu_bar, tearoff=False)
            self.menu_bar.add_cascade(label=menu_name, menu=menu)
            self._build_command_menu(menu_name, menu, items)

    def _build_command_menu(self, menu_name: str, menu: tk.Menu, items: tuple[tuple[str, str], ...]) -> None:
        if menu_name == "View":
            menu.add_checkbutton(label="Grid", variable=self.grid_visible, command=self._toggle_grid_visible)
            menu.add_checkbutton(label="Snap to Grid", variable=self.snap_to_grid, command=self._toggle_snap_to_grid)
            menu.add_checkbutton(label="Local Axes", variable=self.local_axes_visible, command=self._toggle_local_axes_visible)
            menu.add_separator()
            menu.add_command(label="Grid Spacing...", command=self._open_grid_spacing_dialog)
            menu.add_separator()
            menu.add_command(label="Zoom In", command=lambda: self._view_action("Zoom In"))
            menu.add_command(label="Zoom Out", command=lambda: self._view_action("Zoom Out"))
            menu.add_command(label="Full View", command=lambda: self._view_action("Full View"))
            return
        if menu_name == "Analyze":
            menu.add_command(label="Modal Settings...", command=self._open_modal_settings_dialog)
        for kind, label in items:
            if kind == "command":
                menu.add_command(label=label, command=lambda name=label: self._select_command(name))
            elif kind == "action":
                menu.add_command(label=label, command=lambda name=label: self._toolbar_action(name))
            elif kind == "view_action":
                menu.add_command(label=label, command=lambda name=label: self._view_action(name))
            elif kind == "placeholder":
                menu.add_command(label=label, state=tk.DISABLED)

    def _open_grid_spacing_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Grid Spacing")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame, text="Grid spacing").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(frame, textvariable=self.grid_spacing, width=12)
        entry.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        entry.focus_set()
        actions = ttk.Frame(frame)
        actions.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(actions, text="Apply", command=lambda: (self._apply_grid_spacing(), dialog.destroy())).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(actions, text="Cancel", command=dialog.destroy).grid(row=0, column=1)

    def _open_modal_settings_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Modal Analysis Settings")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(frame, text="Number of Modes").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(frame, from_=1, to=20, width=6, textvariable=self.modal_num_modes_var).grid(row=0, column=1, padx=(8, 0), sticky="w")
        damping = ttk.LabelFrame(frame, text="Rayleigh Damping", padding=(8, 6))
        damping.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Label(damping, text="Mode i").grid(row=0, column=0, sticky="w")
        ttk.Entry(damping, width=6, textvariable=self.modal_rayleigh_mode_i_var).grid(row=0, column=1, padx=(6, 12), sticky="w")
        ttk.Label(damping, text="ζi").grid(row=0, column=2, sticky="w")
        ttk.Entry(damping, width=8, textvariable=self.modal_rayleigh_zeta_i_var).grid(row=0, column=3, padx=(6, 12), sticky="w")
        ttk.Label(damping, text="Mode j").grid(row=0, column=4, sticky="w")
        ttk.Entry(damping, width=6, textvariable=self.modal_rayleigh_mode_j_var).grid(row=0, column=5, padx=(6, 12), sticky="w")
        ttk.Label(damping, text="ζj").grid(row=0, column=6, sticky="w")
        ttk.Entry(damping, width=8, textvariable=self.modal_rayleigh_zeta_j_var).grid(row=0, column=7, padx=(6, 0), sticky="w")
        ttk.Label(frame, text="Modal analysis uses the current stiffness and mass model. Static analysis is not required.", wraplength=480).grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 0))
        actions = ttk.Frame(frame)
        actions.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky="e")
        ttk.Button(actions, text="Close", command=dialog.destroy).grid(row=0, column=0)

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

    def _build_workspace_area(self) -> None:
        workspace = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        workspace.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.workspace_panedwindow = workspace

        left_frame = ttk.Frame(workspace, padding=(8, 4))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        self.workspace_left_frame = left_frame
        self.object_tree = ObjectTreePanel(left_frame, selection_callback=self._select_from_tree)
        self.object_tree.grid(row=0, column=0, sticky="nsew")
        workspace.add(left_frame, weight=0)

        canvas_frame = ttk.Frame(workspace, padding=4)
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        self.workspace_canvas_frame = canvas_frame
        self.model_canvas = ModelCanvas(
            canvas_frame,
            status_callback=self._write_status,
            selection_callback=self._show_selection,
            change_callback=self._on_model_changed,
        )
        self.model_canvas.grid(row=0, column=0, sticky="nsew")
        self.canvas = self.model_canvas.canvas
        workspace.add(canvas_frame, weight=1)

    def _build_model_canvas(self) -> None:
        return

    def _build_left_panel(self) -> None:
        return

    def _build_workspace_area_old(self) -> None:
        self.model_canvas = ModelCanvas(
            self.root,
            status_callback=self._write_status,
            selection_callback=self._show_selection,
            change_callback=self._on_model_changed,
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
        if name == "Run Modal Analysis":
            self._run_modal_analysis()
            return
        if name == "Static Results":
            self._show_static_results()
            return
        if name == "Modal Results":
            self._show_modal_results()
            return
        self._write_status(f"{name}: not wired yet.")

    def _run_static_analysis(self) -> None:
        result = run_static_analysis(self.model_canvas.builder.model)
        if not result.ok:
            self.latest_static_results = None
            self.latest_static_result = None
            self.static_analysis_error = result.error
            self._write_status(result.error or "Static analysis failed.")
            return

        self.latest_static_results = result.results
        self.latest_static_result = result.results
        self.static_analysis_error = None
        self._analysis_results_cleared = False
        load_case = getattr(result.results, "load_case_id", "selected load case")
        displacement_count = len(getattr(result.results, "displacements", {}))
        reaction_count = len(getattr(result.results, "reactions", {}))
        self._write_status(
            f"Static analysis complete for {load_case}: "
            f"{displacement_count} displacement rows, {reaction_count} reaction rows."
        )

    def _run_modal_analysis(self) -> None:
        try:
            requested_modes = int(self.modal_num_modes_var.get())
        except ValueError:
            self.latest_modal_results = None
            self.latest_modal_result = None
            self.modal_analysis_error = "Number of modes must be an integer."
            self._write_status(self.modal_analysis_error)
            return

        if requested_modes < 1:
            self.latest_modal_results = None
            self.latest_modal_result = None
            self.modal_analysis_error = "Number of modes must be at least 1."
            self._write_status(self.modal_analysis_error)
            return

        try:
            target_mode_i = int(self._modal_var_value("modal_rayleigh_mode_i_var", "1"))
            target_mode_j = int(self._modal_var_value("modal_rayleigh_mode_j_var", "2"))
        except ValueError:
            self.latest_modal_results = None
            self.latest_modal_result = None
            self.modal_analysis_error = "Rayleigh target modes must be integers."
            self._write_status(self.modal_analysis_error)
            return

        try:
            zeta_i = float(self._modal_var_value("modal_rayleigh_zeta_i_var", "0.05"))
            zeta_j = float(self._modal_var_value("modal_rayleigh_zeta_j_var", "0.05"))
        except ValueError:
            self.latest_modal_results = None
            self.latest_modal_result = None
            self.modal_analysis_error = "Rayleigh damping ratios must be numeric."
            self._write_status(self.modal_analysis_error)
            return

        result = run_modal_analysis(
            self.model_canvas.builder.model,
            num_modes=requested_modes,
            rayleigh_target_mode_i=target_mode_i,
            rayleigh_zeta_i=zeta_i,
            rayleigh_target_mode_j=target_mode_j,
            rayleigh_zeta_j=zeta_j,
        )
        if not result.ok:
            message = self._modal_error_message(result.error)
            self.latest_modal_results = None
            self.latest_modal_result = None
            self.modal_analysis_error = message
            self._write_status(message)
            return

        self.latest_modal_results = result.results
        self.latest_modal_result = result.results
        self.modal_analysis_error = None
        self._analysis_results_cleared = False
        mode_count = getattr(result.results, "num_modes_extracted", None)
        requested = getattr(result.results, "num_modes_requested", requested_modes)
        if mode_count is None:
            modes = getattr(result.results, "mode_shapes", None) or getattr(result.results, "frequencies", None)
            mode_count = len(modes) if modes is not None else None
        if mode_count is None:
            self._write_status("Modal analysis complete.")
        elif requested is not None and mode_count < requested:
            self._write_status(
                f"Modal analysis complete: requested {requested}, extracted {mode_count} mode(s)."
            )
        else:
            self._write_status(f"Modal analysis complete: {mode_count} mode(s) extracted.")

    def _modal_var_value(self, attribute_name: str, default: str) -> str:
        var = getattr(self, attribute_name, None)
        if var is not None and hasattr(var, "get"):
            value = var.get()
            if value not in (None, ""):
                return str(value)
        return default

    def _modal_error_message(self, error: str | None) -> str:
        if not error:
            return "Modal analysis failed."
        normalized = error.lower()
        if (
            "add mass" in normalized
            or "positive-mass dynamic dofs" in normalized
            or "active dynamic dofs" in normalized
        ):
            return "Assign masses before running Modal Analysis."
        return error

    def _show_static_results(self) -> None:
        window = self._create_results_window("static")
        self._refresh_static_result_table()
        section_var = getattr(self, "result_viewer_section_var", None)
        if section_var is not None:
            section_var.set("Static Results")
        self._show_results_section("Static Results")
        if getattr(self, "latest_static_result", None) is None:
            self._write_status(self._result_window_message("static"))
            return
        self._write_status("Static results opened.")

    def _show_complete_model_static_viewer(self) -> None:
        window = self._create_results_window("static")
        self._refresh_static_result_table()
        self._refresh_static_viewer()
        section_var = getattr(self, "result_viewer_section_var", None)
        if section_var is not None:
            section_var.set("Complete Model Static Viewer")
        self._show_results_section("Complete Model Static Viewer")
        if getattr(self, "latest_static_result", None) is None:
            self._write_status(self._result_window_message("static"))
            return
        self._write_status("Complete Model Static Viewer opened.")

    def _show_modal_results(self) -> None:
        window = self._create_results_window("modal")
        self._refresh_modal_viewer()
        section_var = getattr(self, "result_viewer_section_var", None)
        if section_var is not None:
            section_var.set("Modal Results")
        self._show_results_section("Modal Results")
        dynamic_view_var = getattr(self, "result_viewer_dynamic_view_var", None)
        if dynamic_view_var is not None:
            dynamic_view_var.set("Modal Summary")
        self._show_modal_result_view("summary")
        if getattr(self, "latest_modal_result", None) is None:
            self._write_status(self._result_window_message("modal"))
            return
        self._write_status("Modal Results opened.")

    def _create_results_window(self, mode: str = "static") -> tk.Toplevel:
        current_window = getattr(self, "result_viewer_window", None)
        if (
            current_window is not None
            and current_window.winfo_exists()
            and self.result_viewer_mode == mode
        ):
            current_window.lift()
            current_window.focus_force()
            return current_window
        if current_window is not None and current_window.winfo_exists():
            self._close_static_results_window()

        window = tk.Toplevel(self.root)
        window.title("Results")
        window.geometry("980x640")
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)
        window.protocol("WM_DELETE_WINDOW", self._close_static_results_window)
        self.result_viewer_window = window
        self.result_viewer_mode = mode

        header = ttk.Frame(window)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="Results").grid(row=0, column=0, sticky="w")
        ttk.Button(header, text="Refresh Viewer", command=self._refresh_results_viewer).grid(row=0, column=1, sticky="e", padx=(0, 6))
        ttk.Button(header, text="Export Table TXT", command=self._export_current_results_table_txt).grid(row=0, column=2, sticky="e", padx=(0, 6))
        ttk.Button(header, text="Export Table CSV", command=self._export_current_results_table_csv).grid(row=0, column=3, sticky="e", padx=(0, 6))
        ttk.Button(header, text="Export Plot PNG", command=self._export_current_results_plot_png).grid(row=0, column=4, sticky="e")
        body = ttk.Frame(window)
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)
        self.result_viewer_notebook = None
        self.result_viewer_content_frame = body
        if mode == "modal":
            self.result_viewer_section_var = self._make_string_var(self.root, "Modal Results")
            options = ("Modal Results",)
        else:
            self.result_viewer_section_var = self._make_string_var(self.root, "Static Results")
            options = ("Static Results", "Complete Model Static Viewer", "Individual Member Result Viewer")
        self.result_viewer_section_selector = ttk.Combobox(
            body,
            textvariable=self.result_viewer_section_var,
            values=options,
            state="readonly",
            width=34,
        )
        self.result_viewer_section_selector.grid(row=0, column=0, sticky="w")
        self.result_viewer_section_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_results_viewer())
        content = ttk.Frame(body)
        content.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        if mode == "modal":
            dynamic_tab = ttk.Frame(content, padding=6)
            dynamic_tab.grid(row=0, column=0, sticky="nsew")
            self.result_viewer_dynamic_tab = dynamic_tab
            self.result_viewer_table_tab = None
            self.result_viewer_shell_tab = None
            self.result_viewer_member_tab = None
            self._build_modal_results_tab(dynamic_tab)
        else:
            table_tab = ttk.Frame(content, padding=6)
            viewer_tab = ttk.Frame(content, padding=6)
            member_tab = ttk.Frame(content, padding=6)
            for tab in (table_tab, viewer_tab, member_tab):
                tab.grid(row=0, column=0, sticky="nsew")
            self.result_viewer_table_tab = table_tab
            self.result_viewer_dynamic_tab = None
            self.result_viewer_shell_tab = viewer_tab
            self.result_viewer_member_tab = member_tab

            self._build_static_results_table_tab(table_tab)
            self._build_static_results_viewer_tab(viewer_tab)
            self._build_individual_member_results_viewer_tab(member_tab)
        return window

    def _result_window_message(self, mode: str) -> str:
        if self._analysis_results_cleared:
            return self._analysis_results_clear_message
        return "Run Modal Analysis first." if mode == "modal" else "Run Static Analysis first."

    def _show_results_section(self, section: str) -> None:
        section_var = getattr(self, "result_viewer_section_var", None)
        if section_var is None:
            return
        content = getattr(self, "result_viewer_content_frame", None)
        if content is None:
            return
        if section == "Static Results":
            self._show_static_results_section("table")
        elif section == "Complete Model Static Viewer":
            self._show_static_results_section("viewer")
        elif section == "Individual Member Result Viewer":
            self._show_static_results_section("member")
        elif section == "Modal Results":
            self._show_modal_result_view("summary")

    def _show_static_results_section(self, key: str) -> None:
        mapping = {
            "table": self.result_viewer_table_tab,
            "viewer": self.result_viewer_shell_tab,
            "member": self.result_viewer_member_tab,
        }
        frame = mapping.get(key)
        notebook = getattr(self, "result_viewer_notebook", None)
        if notebook is not None and frame is not None and hasattr(notebook, "select"):
            notebook.select(frame)
        if frame is not None and hasattr(frame, "tkraise"):
            frame.tkraise()

    def _refresh_results_viewer(self) -> None:
        self._refresh_static_result_table()
        self._refresh_static_viewer()
        self._refresh_modal_viewer()
        section_var = getattr(self, "result_viewer_section_var", None)
        if section_var is not None:
            self._show_results_section(section_var.get())

    def _close_static_results_window(self) -> None:
        if self.result_viewer_window is not None and self.result_viewer_window.winfo_exists():
            self.result_viewer_window.destroy()
        self.result_viewer_window = None
        self.result_viewer_mode = None
        self.result_viewer_notebook = None
        self.result_viewer_section_var = None
        self.result_viewer_section_selector = None
        self.result_viewer_content_frame = None
        self.result_viewer_message = None
        self.result_viewer_dynamic_notebook = None
        self.result_viewer_dynamic_top_controls = None
        self.result_viewer_dynamic_summary_tab = None
        self.result_viewer_dynamic_mode_shapes_tab = None
        self.result_viewer_dynamic_matrices_tab = None
        self.result_viewer_dynamic_view_var = None
        self.result_viewer_dynamic_view_selector = None
        self.result_viewer_dynamic_summary_tree = None
        self.result_viewer_dynamic_mode_selector = None
        self.result_viewer_dynamic_matrix_selector = None
        self.result_viewer_dynamic_matrix_tree = None
        self.result_viewer_dynamic_mode_info_frame = None
        self.result_viewer_dynamic_mode_info_vars = {}
        self.result_viewer_dynamic_plot_frame = None
        self.result_viewer_dynamic_plot_canvas = None
        self.result_viewer_plot_notebook = None
        self.result_viewer_plot_view_var = None
        self.result_viewer_plot_view_selector = None
        self.result_viewer_plot_content_frame = None
        self.result_viewer_plot_frames = {}
        self.result_viewer_plot_canvases = {}
        self.result_viewer_table_tab = None
        self.result_viewer_shell_tab = None
        self.result_viewer_member_tab = None
        self.result_viewer_dynamic_tab = None
        self.result_viewer_dynamic_category = None
        self.result_viewer_dynamic_message = None
        self.result_viewer_dynamic_tree = None
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
        ttk.Label(controls, text="Diagram").grid(row=0, column=0, sticky="w")
        self.result_viewer_plot_view_var = self._make_string_var(parent, "Deformed Shape")
        self.result_viewer_plot_view_selector = ttk.Combobox(
            controls,
            textvariable=self.result_viewer_plot_view_var,
            values=("Deformed Shape", "Axial Force N", "Shear Force V", "Bending Moment M"),
            state="readonly",
            width=22,
        )
        self.result_viewer_plot_view_selector.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.result_viewer_plot_view_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_static_viewer())

        self.result_viewer_message = tk.StringVar(value="Complete model viewer shell is ready for the stored Static result.")
        ttk.Label(parent, textvariable=self.result_viewer_message).grid(row=1, column=0, sticky="w", pady=(0, 6))
        content = ttk.Frame(parent)
        content.grid(row=2, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        self.result_viewer_plot_notebook = None
        self.result_viewer_plot_content_frame = content
        self.result_viewer_plot_frames = {
            "deformed": ttk.Frame(content, padding=6),
            "axial": ttk.Frame(content, padding=6),
            "shear": ttk.Frame(content, padding=6),
            "moment": ttk.Frame(content, padding=6),
        }
        for frame in self.result_viewer_plot_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
        self._refresh_static_viewer()

    def _build_modal_results_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        self.result_viewer_dynamic_top_controls = ttk.Frame(parent)
        self.result_viewer_dynamic_top_controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.result_viewer_dynamic_top_controls.columnconfigure(4, weight=1)
        ttk.Label(self.result_viewer_dynamic_top_controls, text="Modal Results").grid(row=0, column=0, sticky="w")

        mode_controls = ttk.Frame(self.result_viewer_dynamic_top_controls)
        mode_controls.grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Label(mode_controls, text="Mode").grid(row=0, column=0, sticky="w")
        self.result_viewer_dynamic_mode_var = self._make_string_var(parent, "1")
        self.result_viewer_dynamic_mode_selector = ttk.Combobox(
            mode_controls,
            textvariable=self.result_viewer_dynamic_mode_var,
            values=(),
            state="readonly",
            width=8,
        )
        self.result_viewer_dynamic_mode_selector.grid(row=0, column=1, padx=(8, 0), sticky="w")
        self.result_viewer_dynamic_mode_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_modal_mode_shape_view())

        normalization_controls = ttk.Frame(self.result_viewer_dynamic_top_controls)
        normalization_controls.grid(row=0, column=2, sticky="w", padx=(12, 0))
        ttk.Label(normalization_controls, text="Display").grid(row=0, column=0, sticky="w")
        self.result_viewer_dynamic_mode_normalization_var = self._make_string_var(parent, "Mass normalized")
        self.result_viewer_dynamic_mode_normalization_selector = ttk.Combobox(
            normalization_controls,
            textvariable=self.result_viewer_dynamic_mode_normalization_var,
            values=("Mass normalized", "Magnitude normalized", "Specific DOF normalized"),
            state="readonly",
            width=22,
        )
        self.result_viewer_dynamic_mode_normalization_selector.grid(row=0, column=1, padx=(8, 12), sticky="w")
        self.result_viewer_dynamic_mode_normalization_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_modal_mode_shape_view())
        ttk.Label(normalization_controls, text="Reference DOF").grid(row=0, column=2, sticky="w")
        self.result_viewer_dynamic_reference_dof_var = self._make_string_var(parent, "1")
        self.result_viewer_dynamic_reference_dof_selector = ttk.Combobox(
            normalization_controls,
            textvariable=self.result_viewer_dynamic_reference_dof_var,
            values=(),
            state="disabled",
            width=10,
        )
        self.result_viewer_dynamic_reference_dof_selector.grid(row=0, column=3, padx=(8, 0), sticky="w")
        self.result_viewer_dynamic_reference_dof_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_modal_mode_shape_view())
        ttk.Label(self.result_viewer_dynamic_top_controls, text="View").grid(row=0, column=3, sticky="w", padx=(12, 0))
        self.result_viewer_dynamic_view_var = self._make_string_var(parent, "Modal Summary")
        self.result_viewer_dynamic_view_selector = ttk.Combobox(
            self.result_viewer_dynamic_top_controls,
            textvariable=self.result_viewer_dynamic_view_var,
            values=("Modal Summary", "Mode Shapes", "Matrices"),
            state="readonly",
            width=18,
        )
        self.result_viewer_dynamic_view_selector.grid(row=0, column=4, sticky="w")
        self.result_viewer_dynamic_view_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_modal_viewer())
        ttk.Button(self.result_viewer_dynamic_top_controls, text="Refresh Viewer", command=self._refresh_results_viewer).grid(row=0, column=5, sticky="e", padx=(12, 0))

        content = ttk.Frame(parent)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)
        self.result_viewer_dynamic_notebook = None

        summary_tab = ttk.Frame(content, padding=6)
        mode_tab = ttk.Frame(content, padding=6)
        matrices_tab = ttk.Frame(content, padding=6)
        for tab in (summary_tab, mode_tab, matrices_tab):
            tab.grid(row=0, column=0, sticky="nsew")
        self.result_viewer_dynamic_summary_tab = summary_tab
        self.result_viewer_dynamic_mode_shapes_tab = mode_tab
        self.result_viewer_dynamic_matrices_tab = matrices_tab

        self._build_modal_summary_tab(summary_tab)
        self._build_modal_mode_shapes_tab(mode_tab)
        self._build_modal_matrices_tab(matrices_tab)

        self.result_viewer_dynamic_message = self._make_string_var(parent, "Run Modal Analysis first.")
        ttk.Label(parent, textvariable=self.result_viewer_dynamic_message).grid(row=2, column=0, sticky="ew", pady=(6, 0))
        self._refresh_modal_viewer()
        if self.result_viewer_dynamic_notebook is not None and self.result_viewer_dynamic_summary_tab is not None:
            self.result_viewer_dynamic_notebook.select(self.result_viewer_dynamic_summary_tab)

    def _build_modal_summary_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(frame, show="headings")
        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.result_viewer_dynamic_summary_tree = tree

    def _build_modal_mode_shapes_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        info = ttk.LabelFrame(parent, text="Selected Mode", padding=8)
        info.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        info.columnconfigure(1, weight=1)
        self.result_viewer_dynamic_mode_info_frame = info
        self.result_viewer_dynamic_mode_info_vars = {
            "Mode": tk.StringVar(value="—"),
            "Eigenvalue (ω²)": tk.StringVar(value="—"),
            "Frequency": tk.StringVar(value="—"),
            "Period": tk.StringVar(value="—"),
            "Modal Mass": tk.StringVar(value="—"),
            "Participation Factor": tk.StringVar(value="—"),
            "Effective Mass": tk.StringVar(value="—"),
            "Participation Ratio": tk.StringVar(value="—"),
            "Modal Damping Ratio": tk.StringVar(value="—"),
        }
        for row, (label, value_var) in enumerate(self.result_viewer_dynamic_mode_info_vars.items()):
            ttk.Label(info, text=label).grid(row=row, column=0, sticky="w", pady=2)
            ttk.Label(info, textvariable=value_var, wraplength=280, justify="left").grid(row=row, column=1, sticky="ew", pady=2)

        content = ttk.Frame(parent)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=0)
        content.rowconfigure(0, weight=1)

        plot_frame = ttk.Frame(content)
        plot_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        self.result_viewer_dynamic_plot_frame = plot_frame
        self.result_viewer_dynamic_plot_canvas = None

        phi_frame = ttk.LabelFrame(content, text="Phi Values", padding=6)
        phi_frame.grid(row=0, column=1, sticky="ns")
        phi_frame.columnconfigure(0, weight=1)
        phi_frame.rowconfigure(0, weight=1)
        phi_tree = ttk.Treeview(phi_frame, show="headings")
        phi_scroll = ttk.Scrollbar(phi_frame, orient=tk.VERTICAL, command=phi_tree.yview)
        phi_tree.configure(yscrollcommand=phi_scroll.set)
        phi_tree.grid(row=0, column=0, sticky="nsew")
        phi_scroll.grid(row=0, column=1, sticky="ns")
        self.result_viewer_dynamic_phi_tree = phi_tree

    def _build_modal_matrices_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        controls = ttk.Frame(parent)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Matrix").grid(row=0, column=0, sticky="w")
        initial_matrix_values = tuple(self._modal_result_categories())
        self.result_viewer_dynamic_category = tk.StringVar(value=initial_matrix_values[0] if initial_matrix_values else "Kff")
        self.result_viewer_dynamic_matrix_selector = ttk.Combobox(
            controls,
            textvariable=self.result_viewer_dynamic_category,
            values=initial_matrix_values,
            state="readonly" if initial_matrix_values else "disabled",
            width=8,
        )
        self.result_viewer_dynamic_matrix_selector.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.result_viewer_dynamic_matrix_selector.bind("<<ComboboxSelected>>", lambda _event: self._refresh_modal_matrix_table())
        ttk.Label(
            parent,
            text="Kff, Mff, and Cff are the reduced/condensed dynamic matrices used for modal analysis.",
            wraplength=760,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        frame = ttk.Frame(parent)
        frame.grid(row=2, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        tree = ttk.Treeview(frame, show="headings")
        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.result_viewer_dynamic_tree = tree
        self.result_viewer_dynamic_matrix_tree = tree

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

    def _modal_summary_table_data(self) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        results = self._current_modal_results()
        if results is None:
            return (("Message",), [(self._result_window_message("modal"),)])
        mode_count = self._modal_mode_count(results)
        if mode_count < 1:
            return (("Message",), [("No modal modes available.",)])
        columns = (
            "Mode",
            "Eigenvalue (ω²)",
            "Omega (ω)",
            "Frequency",
            "Period",
            "Modal Mass",
            "Participation Factor",
            "Effective Modal Mass",
            "Mass Participation Ratio",
            "Modal Damping Ratio",
        )
        rows = [self._modal_summary_row(results, index) for index in range(mode_count)]
        return columns, rows

    def _modal_mode_count(self, results: object) -> int:
        extracted = getattr(results, "num_modes_extracted", None)
        if isinstance(extracted, int) and extracted > 0:
            return extracted
        lengths = []
        for attribute_name in (
            "eigenvalues",
            "frequencies",
            "periods",
            "mode_shapes",
            "modal_masses",
            "participation_factors",
            "effective_masses",
            "effective_modal_masses",
            "mass_participation_ratios",
            "mass_participation_ratio",
            "modal_damping_ratios",
        ):
            values = getattr(results, attribute_name, None)
            if isinstance(values, (list, tuple)) and values:
                lengths.append(len(values))
        if lengths:
            return max(lengths)
        requested = getattr(results, "num_modes_requested", None)
        if isinstance(requested, int) and requested > 0:
            return requested
        return 0

    def _modal_sequence_value(self, results: object, attribute_names: tuple[str, ...], index: int) -> object | None:
        for attribute_name in attribute_names:
            values = getattr(results, attribute_name, None)
            if values is None:
                continue
            if isinstance(values, (list, tuple)):
                if 0 <= index < len(values):
                    return values[index]
            elif index == 0:
                return values
        return None

    def _modal_format_value(self, value: object | None, *, as_percent: bool = False) -> str:
        if value is None:
            return "—"
        if as_percent:
            try:
                value = float(value) * 100.0
            except (TypeError, ValueError):
                return str(value)
            return f"{format_scalar(value, tolerance=self._display_tolerance())}%"
        formatted = format_scalar(value, tolerance=self._display_tolerance())
        return "—" if formatted == "-" else formatted

    def _modal_derived_omega(self, eigenvalue: object | None) -> object | None:
        if eigenvalue is not None:
            try:
                numeric_eigenvalue = float(eigenvalue)
            except (TypeError, ValueError):
                return None
            if numeric_eigenvalue >= 0.0:
                return math.sqrt(numeric_eigenvalue)
        return None

    def _modal_summary_row(self, results: object, index: int) -> tuple[str, ...]:
        eigenvalue = self._modal_sequence_value(results, ("eigenvalues", "omega_squared", "omega2"), index)
        frequency = self._modal_sequence_value(results, ("frequencies",), index)
        omega = self._modal_sequence_value(results, ("omegas", "omega", "angular_frequencies"), index)
        if omega is None:
            omega = self._modal_derived_omega(eigenvalue)
        return (
            str(index + 1),
            self._modal_format_value(eigenvalue),
            self._modal_format_value(omega),
            self._modal_format_value(frequency),
            self._modal_format_value(self._modal_sequence_value(results, ("periods",), index)),
            self._modal_format_value(self._modal_sequence_value(results, ("modal_masses",), index)),
            self._modal_format_value(self._modal_sequence_value(results, ("participation_factors",), index)),
            self._modal_format_value(self._modal_sequence_value(results, ("effective_masses", "effective_modal_masses", "effective_mass"), index)),
            self._modal_format_value(self._modal_sequence_value(results, ("mass_participation_ratios", "mass_participation_ratio"), index), as_percent=True),
            self._modal_format_value(self._modal_sequence_value(results, ("modal_damping_ratios",), index), as_percent=True),
        )

    def _modal_mode_info_values(self, results: object, index: int) -> dict[str, str]:
        row = self._modal_summary_row(results, index)
        return {
            "Mode": row[0],
            "Eigenvalue (ω²)": row[1],
            "Frequency": row[3],
            "Period": row[4],
            "Modal Mass": row[5],
            "Participation Factor": row[6],
            "Effective Mass": row[7],
            "Participation Ratio": row[8],
            "Modal Damping Ratio": row[9],
        }

    def _modal_scalar_value(self, results: object, attribute_names: tuple[str, ...]) -> object | None:
        for attribute_name in attribute_names:
            value = getattr(results, attribute_name, None)
            if value is not None:
                return value
        return None

    def _modal_global_damping_message(self, results: object) -> str:
        alpha = self._modal_scalar_value(results, ("rayleigh_alpha",))
        beta = self._modal_scalar_value(results, ("rayleigh_beta",))
        target_modes = self._modal_scalar_value(results, ("rayleigh_target_modes",))
        if target_modes is None:
            mode_i = self._modal_scalar_value(results, ("rayleigh_target_mode_i",))
            mode_j = self._modal_scalar_value(results, ("rayleigh_target_mode_j",))
            if mode_i is not None and mode_j is not None:
                target_modes = (mode_i, mode_j)
        target_zetas = self._modal_scalar_value(results, ("rayleigh_target_damping_ratios",))
        if target_zetas is None:
            zeta_i = self._modal_scalar_value(results, ("rayleigh_zeta_i",))
            zeta_j = self._modal_scalar_value(results, ("rayleigh_zeta_j",))
            if zeta_i is not None and zeta_j is not None:
                target_zetas = (zeta_i, zeta_j)

        if alpha is None and beta is None and target_modes is None and target_zetas is None:
            return ""

        mode_text = "—"
        if isinstance(target_modes, (list, tuple)) and len(target_modes) >= 2:
            mode_text = f"mode {target_modes[0]} and mode {target_modes[1]}"
        zeta_text = "—"
        if isinstance(target_zetas, (list, tuple)) and len(target_zetas) >= 2:
            zeta_text = f"{self._modal_format_value(target_zetas[0], as_percent=True)} / {self._modal_format_value(target_zetas[1], as_percent=True)}"

        return (
            "Rayleigh damping: "
            f"alpha = {self._modal_format_value(alpha)}, "
            f"beta = {self._modal_format_value(beta)}, "
            f"targets = {mode_text}, "
            f"zetas = {zeta_text}."
        )

    def _modal_result_containers(self, result: object) -> list[object]:
        containers = [result]
        for attribute_name in ("dynamic_assembly", "assembly_data", "dynamic_data"):
            nested = self._modal_container_value(result, attribute_name)
            if nested is not None:
                containers.append(nested)
        return containers

    def _modal_container_value(self, container: object, key: str) -> object | None:
        if container is None:
            return None
        if isinstance(container, Mapping):
            return container.get(key)
        return getattr(container, key, None)

    def _get_modal_matrix(self, result: object, key: str) -> object | None:
        if key == "Cff":
            return self._modal_container_value(result, "Cff")
        aliases = {
            "Kff": ("Kff", "K"),
            "Mff": ("Mff", "M"),
        }
        for container in self._modal_result_containers(result):
            for alias in aliases.get(key, (key,)):
                value = self._modal_container_value(container, alias)
                if value is not None:
                    return value
        return None

    def _get_modal_dof_map(self, result: object) -> object | None:
        for container in self._modal_result_containers(result):
            value = self._modal_container_value(container, "dof_map")
            if value is not None:
                return value
        return None

    def _modal_matrix_table_data(self, matrix: object) -> tuple[tuple[str, ...], list[tuple[str, ...]]] | tuple[None, None]:
        rows = format_matrix(matrix, tolerance=self._display_tolerance())
        if not rows:
            return (None, None)

        width = max(len(row) for row in rows)
        padded_rows = [row + tuple("-" for _ in range(width - len(row))) for row in rows]
        columns = ("DOF",) + tuple(f"DOF{index + 1}" for index in range(width))
        table_rows = [
            (f"DOF{index + 1}", *padded_rows[index])
            for index in range(len(padded_rows))
        ]
        return columns, table_rows

    def _modal_result_rows(self) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        results = self._current_modal_results()
        if results is None:
            return (("Message",), [(self._result_window_message("modal"),)])
        category = self._current_modal_result_category()
        available_categories = self._modal_result_categories(results)
        if category not in available_categories:
            return (("Message",), [("Selected modal matrix is not available in this result.",)])
        matrix = self._get_modal_matrix(results, category)
        if matrix is None or not matrix:
            return (("Message",), [("Selected modal matrix is not available in this result.",)])
        columns, rows = self._modal_matrix_table_data(matrix)
        if columns is None or rows is None:
            return (("Message",), [("Selected modal matrix is not available in this result.",)])
        return columns, rows

    def _modal_result_categories(self, result: object | None = None) -> list[str]:
        results = self._current_modal_results() if result is None else result
        if results is None:
            return []
        categories = []
        for key in ("Kff", "Mff", "Cff"):
            if self._get_modal_matrix(results, key) is not None:
                categories.append(key)
        return categories

    def _current_modal_result_category(self) -> str:
        var = getattr(self, "result_viewer_dynamic_category", None)
        if var is None:
            available = self._modal_result_categories()
            return available[0] if available else "Kff"
        value = var.get() if hasattr(var, "get") else str(var)
        return value or "Kff"

    def _render_result_table(
        self,
        tree: object | None,
        columns: tuple[str, ...],
        rows: list[tuple[str, ...]],
        *,
        column_width: int = 140,
    ) -> None:
        if tree is None:
            return
        tree.delete(*tree.get_children())
        tree.configure(columns=columns)
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=column_width, anchor="w", stretch=True)
        for row in rows:
            tree.insert("", "end", values=row)

    def _refresh_modal_summary_table(self) -> None:
        tree = getattr(self, "result_viewer_dynamic_summary_tree", None)
        columns, rows = self._modal_summary_table_data()
        self._render_result_table(tree, columns, rows, column_width=130)

    def _refresh_modal_matrix_table(self) -> None:
        tree = getattr(self, "result_viewer_dynamic_tree", None)
        columns, rows = self._modal_result_rows()
        self._render_result_table(tree, columns, rows, column_width=140)

    def _update_modal_mode_info_panel(self) -> None:
        vars_map = getattr(self, "result_viewer_dynamic_mode_info_vars", {}) or {}
        if not vars_map:
            return
        for value_var in vars_map.values():
            value_var.set("—")
        results = self._current_modal_results()
        if results is None:
            return
        mode_index = self._current_modal_mode_index()
        if mode_index is None:
            return
        for label, value in self._modal_mode_info_values(results, mode_index).items():
            value_var = vars_map.get(label)
            if value_var is not None:
                value_var.set(value)

    def _select_static_viewer_tab(self, key: str) -> None:
        mapping = {
            "deformed": "Deformed Shape",
            "axial": "Axial Force N",
            "shear": "Shear Force V",
            "moment": "Bending Moment M",
        }
        selector = getattr(self, "result_viewer_plot_view_selector", None)
        if selector is not None and key in mapping and getattr(self, "result_viewer_plot_view_var", None) is not None:
            self.result_viewer_plot_view_var.set(mapping[key])
        self._refresh_static_viewer()

    def _available_member_ids(self) -> list[object]:
        results = self._current_static_results()
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
        if getattr(self, "latest_static_result", None) is None:
            message = self._result_window_message("static")
            self.result_viewer_member_message.set(message)
            self._render_member_review_placeholder(message)
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
        signature = (id(model), id(self._current_static_results()), str(member_id), display_mode, show_max)
        if signature == getattr(self, "result_viewer_member_profile_signature", None) and getattr(self, "result_viewer_member_profile", None):
            self._configure_member_review_scale()
            self._update_member_review_cursor_only()
            self.result_viewer_member_message.set(f"Member {member_id} selected for static review.")
            return
        profile = build_member_review_profile(model, self._current_static_results(), member_id)
        if profile is None:
            self.result_viewer_member_message.set("Select a valid member.")
            self._render_member_review_placeholder("Select a valid member.")
            return
        if not getattr(self._current_static_results(), "displacements", None):
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
            "member_end_forces": profile.get("member_end_forces", {}) or {},
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
                end_forces = profile.get("member_end_forces", {}) or profile.get("end_forces", {}) or {}
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
        self._draw_labeled_force_arrow(canvas, left_x, y_n, end_forces.get("FXi", end_forces.get("Ni", 0.0)), "FX", "horizontal", text_side="right")
        self._draw_labeled_force_arrow(canvas, left_x, y_v, end_forces.get("FYi", end_forces.get("Vi", 0.0)), "FY", "vertical", text_side="right")
        self._draw_labeled_moment_arrow(canvas, left_x, y_m, end_forces.get("MZi", end_forces.get("Mi", 0.0)), label="MZ", text_side="right")
        self._draw_labeled_force_arrow(canvas, right_x, y_n, end_forces.get("FXj", end_forces.get("Nj", 0.0)), "FX", "horizontal", text_side="left")
        self._draw_labeled_force_arrow(canvas, right_x, y_v, end_forces.get("FYj", end_forces.get("Vj", 0.0)), "FY", "vertical", text_side="left")
        self._draw_labeled_moment_arrow(canvas, right_x, y_m, end_forces.get("MZj", end_forces.get("Mj", 0.0)), label="MZ", text_side="left")

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
        positive_vertical_down: bool = False,
    ) -> None:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            numeric_value = 0.0
        sign = 1.0 if numeric_value >= 0.0 else -1.0
        color = self._member_review_value_color(numeric_value)
        if orientation == "horizontal":
            dx, dy = sign * 30.0, 0.0
        elif positive_vertical_down:
            dx, dy = 0.0, sign * 22.0
        else:
            dx, dy = 0.0, -sign * 22.0
        canvas.create_line(x, y, x + dx, y + dy, fill=color, width=2, arrow=tk.LAST)
        text_x = x + 38.0 if text_side == "right" else x - 38.0
        anchor = "w" if text_side == "right" else "e"
        canvas.create_text(text_x, y, text=f"{label}={self._format_number(numeric_value)}", anchor=anchor, fill=color, font=("Segoe UI", 8))

    def _draw_labeled_moment_arrow(self, canvas: tk.Canvas, x: float, y: float, value: object, *, text_side: str, label: str = "M") -> None:
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
        canvas.create_text(text_x, y, text=f"{label}={self._format_number(numeric_value)}", anchor=anchor, fill=color, font=("Segoe UI", 8))

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
        selected = getattr(self, "result_viewer_plot_view_var", None)
        if selected is not None:
            key = {
                "Deformed Shape": "deformed",
                "Axial Force N": "axial",
                "Shear Force V": "shear",
                "Bending Moment M": "moment",
            }.get(selected.get(), "deformed")
            self._show_static_result_view(key)
        if getattr(self, "latest_static_result", None) is None:
            message = self._result_window_message("static")
            self.result_viewer_message.set(message)
            self._render_static_viewer_placeholder(message)
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
        results = self._current_static_results()
        model = getattr(getattr(self, "model_canvas", None), "builder", None)
        model = getattr(model, "model", None)
        if results is None:
            self._render_static_viewer_placeholder(self._result_window_message("static"))
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
            message = placeholder if self._analysis_results_cleared else ("Run Static Analysis first." if key == "deformed" else placeholder)
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

    def _export_current_results_table_txt(self) -> None:
        self._export_current_results_table("txt")

    def _export_current_results_table_csv(self) -> None:
        self._export_current_results_table("csv")

    def _export_current_results_plot_png(self) -> None:
        if getattr(self, "result_viewer_mode", None) == "modal":
            canvas = getattr(self, "result_viewer_dynamic_plot_canvas", None)
            if canvas is None:
                self._write_status("No modal plot is visible to export.")
                return
            default_name = "modal_results_plot.png"
        else:
            section = getattr(self, "result_viewer_section_var", None)
            section_name = section.get() if section is not None and hasattr(section, "get") else "Static Results"
            if section_name == "Individual Member Result Viewer":
                canvas = getattr(self, "result_viewer_member_plot_canvas", None)
                default_name = "member_review_plot.png"
            else:
                canvas = self._current_static_plot_canvas()
                default_name = "static_results_plot.png"
            if canvas is None:
                self._write_status("No static plot is visible to export.")
                return

        filepath = filedialog.asksaveasfilename(
            parent=getattr(self, "root", None),
            title="Export Plot PNG",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=(("PNG files", "*.png"), ("All files", "*.*")),
        )
        if not filepath:
            self._write_status("Plot export canceled.")
            return
        try:
            canvas.figure.savefig(filepath, dpi=150, bbox_inches="tight")
        except Exception as exc:
            self._write_status(f"Plot export failed: {exc}")
            return
        self._write_status(f"Exported plot PNG: {filepath}")

    def _export_current_results_table(self, file_format: str) -> None:
        mode = getattr(self, "result_viewer_mode", None)
        if mode == "modal":
            columns, rows = self._current_modal_export_table_data()
            default_name = "modal_results_table"
        else:
            columns, rows = self._current_static_export_table_data()
            default_name = "static_results_table"

        extension = "csv" if file_format == "csv" else "txt"
        filepath = filedialog.asksaveasfilename(
            parent=getattr(self, "root", None),
            title="Export Results Table",
            defaultextension=f".{extension}",
            initialfile=f"{default_name}.{extension}",
            filetypes=((f"{extension.upper()} files", f"*.{extension}"), ("All files", "*.*")),
        )
        if not filepath:
            self._write_status("Table export canceled.")
            return
        try:
            self._write_table_file(filepath, columns, rows, file_format)
        except Exception as exc:
            self._write_status(f"Table export failed: {exc}")
            return
        self._write_status(f"Exported results table: {filepath}")

    def _write_table_file(self, filepath: str, columns: tuple[str, ...], rows: list[tuple[str, ...]], file_format: str) -> None:
        if file_format == "csv":
            with open(filepath, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(columns)
                writer.writerows(rows)
            return
        lines = ["\t".join(columns)]
        lines.extend("\t".join(str(value) for value in row) for row in rows)
        Path(filepath).write_text("\n".join(lines) + "\n", encoding="utf-8")

    def _current_static_plot_canvas(self):
        section_var = getattr(self, "result_viewer_section_var", None)
        section_name = section_var.get() if section_var is not None and hasattr(section_var, "get") else "Static Results"
        if section_name == "Complete Model Static Viewer":
            selected = getattr(self, "result_viewer_plot_view_var", None)
            if selected is None:
                return None
            key = {
                "Deformed Shape": "deformed",
                "Axial Force N": "axial",
                "Shear Force V": "shear",
                "Bending Moment M": "moment",
            }.get(selected.get(), "deformed")
            return self.result_viewer_plot_canvases.get(self.result_viewer_plot_frames.get(key))
        if section_name == "Individual Member Result Viewer":
            return getattr(self, "result_viewer_member_plot_canvas", None)
        return self.result_viewer_plot_canvases.get(self.result_viewer_plot_frames.get("deformed"))

    def _current_static_export_table_data(self) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        category = getattr(self, "result_view_category", None)
        category_name = category.get() if category is not None and hasattr(category, "get") else "Nodal Displacements"
        return self._static_result_table_data(category_name)

    def _current_modal_export_table_data(self) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        view_var = getattr(self, "result_viewer_dynamic_view_var", None)
        view_name = view_var.get() if view_var is not None and hasattr(view_var, "get") else "Modal Summary"
        if view_name == "Mode Shapes":
            return self._modal_mode_shape_export_table_data()
        if view_name == "Matrices":
            return self._modal_result_rows()
        return self._modal_summary_table_data()

    def _modal_mode_shape_export_table_data(self) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        results = self._current_modal_results()
        if results is None:
            return (("Message",), [(self._result_window_message("modal"),)])
        message = self._modal_mode_shape_message(results)
        if message is not None:
            return (("Message",), [(message,)])
        mode_index = self._current_modal_mode_index()
        if mode_index is None:
            return (("Message",), [("Invalid mode index.",)])
        mode_shapes = getattr(results, "mode_shapes", None) or []
        mode_shape = mode_shapes[mode_index] if 0 <= mode_index < len(mode_shapes) else None
        normalization = self._current_modal_mode_normalization()
        reference_dof = self._current_modal_reference_dof()
        normalized_shape, normalization_message = self._normalize_modal_mode_shape(mode_shape, normalization, reference_dof)
        return self._modal_phi_table_data(normalized_shape, normalization_message)

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

    def _refresh_modal_result_table(self) -> None:
        self._refresh_modal_matrix_table()

    def _refresh_modal_summary(self) -> None:
        message_var = getattr(self, "result_viewer_dynamic_message", None)
        results = self._current_modal_results()
        if results is None:
            matrix_values = tuple(self._modal_result_categories(None))
            self._render_result_table(
                getattr(self, "result_viewer_dynamic_summary_tree", None),
                ("Message",),
                [(self._result_window_message("modal"),)],
                column_width=130,
            )
            mode_selector = getattr(self, "result_viewer_dynamic_mode_selector", None)
            if mode_selector is not None:
                mode_selector.configure(values=(), state="disabled")
            matrix_selector = getattr(self, "result_viewer_dynamic_matrix_selector", None)
            if matrix_selector is not None:
                matrix_selector.configure(values=matrix_values, state="disabled")
            mode_var = getattr(self, "result_viewer_dynamic_mode_var", None)
            if mode_var is not None:
                mode_var.set("1")
            matrix_var = getattr(self, "result_viewer_dynamic_category", None)
            if matrix_var is not None:
                matrix_var.set(matrix_values[0] if matrix_values else "Kff")
            if message_var is not None:
                message_var.set(self._result_window_message("modal"))
            self._refresh_modal_mode_shape_controls()
            return

        columns, rows = self._modal_summary_table_data()
        self._render_result_table(getattr(self, "result_viewer_dynamic_summary_tree", None), columns, rows, column_width=130)

        mode_values = tuple(str(index) for index in range(1, self._modal_mode_count(results) + 1))
        mode_selector = getattr(self, "result_viewer_dynamic_mode_selector", None)
        if mode_selector is not None:
            mode_selector.configure(values=mode_values, state="readonly" if mode_values else "disabled")
        mode_var = getattr(self, "result_viewer_dynamic_mode_var", None)
        if mode_var is not None:
            current_mode = 1
            try:
                current_mode = int(mode_var.get())
            except (TypeError, ValueError):
                pass
            if mode_values:
                mode_var.set(str(min(max(current_mode, 1), len(mode_values))))
            else:
                mode_var.set("1")

        matrix_values = tuple(self._modal_result_categories())
        matrix_selector = getattr(self, "result_viewer_dynamic_matrix_selector", None)
        if matrix_selector is not None:
            matrix_selector.configure(values=matrix_values, state="readonly" if matrix_values else "disabled")
        matrix_var = getattr(self, "result_viewer_dynamic_category", None)
        if matrix_var is not None:
            current_matrix = matrix_var.get() if hasattr(matrix_var, "get") else str(matrix_var)
            if current_matrix not in matrix_values:
                matrix_var.set(matrix_values[0] if matrix_values else "Kff")

        self._refresh_modal_mode_shape_controls()

        if message_var is not None:
            message = "Modal results ready." if mode_values else "No modal modes available."
            damping_message = self._modal_global_damping_message(results)
            message_var.set(f"{message} {damping_message}" if damping_message else message)

    def _static_result_table_data(self, category: str) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        results = self._current_static_results()
        if results is None:
            return (("Message",), [(self._result_window_message("static"),)])
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
            member_end_forces = getattr(results, "member_end_forces", None)
            if member_end_forces is None:
                member_end_forces = getattr(results, "element_forces", None)
            return self._member_force_rows(member_end_forces, units)
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

    def _refresh_modal_viewer(self) -> None:
        self._refresh_modal_summary()
        self._refresh_modal_mode_shape_view()
        self._refresh_modal_matrix_table()
        view_var = getattr(self, "result_viewer_dynamic_view_var", None)
        if view_var is not None:
            selected = view_var.get()
            if selected == "Modal Summary":
                self._show_modal_result_view("summary")
            elif selected == "Mode Shapes":
                self._show_modal_result_view("mode_shapes")
            elif selected == "Matrices":
                self._show_modal_result_view("matrices")

    def _show_static_result_view(self, key: str) -> None:
        frame = self.result_viewer_plot_frames.get(key)
        if frame is not None and hasattr(frame, "tkraise"):
            frame.tkraise()

    def _show_modal_result_view(self, key: str) -> None:
        frames = {
            "summary": getattr(self, "result_viewer_dynamic_summary_tab", None),
            "mode_shapes": getattr(self, "result_viewer_dynamic_mode_shapes_tab", None),
            "matrices": getattr(self, "result_viewer_dynamic_matrices_tab", None),
        }
        frame = frames.get(key)
        notebook = getattr(self, "result_viewer_dynamic_notebook", None)
        if notebook is not None and frame is not None and hasattr(notebook, "select"):
            notebook.select(frame)
        if frame is not None and hasattr(frame, "tkraise"):
            frame.tkraise()

    def _modal_mode_shape_message(self, results: object) -> str | None:
        mode_shapes = getattr(results, "mode_shapes", None) or []
        if not mode_shapes:
            return "Modal result does not contain mode shapes."
        return None

    def _modal_mode_limit(self, results: object) -> int:
        mode_shapes = getattr(results, "mode_shapes", None) or []
        extracted = getattr(results, "num_modes_extracted", None)
        limit = len(mode_shapes)
        if isinstance(extracted, int) and extracted > 0:
            limit = min(limit, extracted)
        return max(limit, 0)

    def _current_modal_mode_index(self) -> int | None:
        results = self._current_modal_results()
        if results is None:
            return None
        limit = self._modal_mode_count(results)
        if limit < 1:
            return None
        var = getattr(self, "result_viewer_dynamic_mode_var", None)
        try:
            mode_index = int(var.get()) - 1 if var is not None and hasattr(var, "get") else 0
        except (TypeError, ValueError):
            return None
        if mode_index < 0 or mode_index >= limit:
            return None
        return mode_index

    def _current_modal_mode_normalization(self) -> str:
        var = getattr(self, "result_viewer_dynamic_mode_normalization_var", None)
        if var is None or not hasattr(var, "get"):
            return "Mass normalized"
        value = var.get()
        return value or "Mass normalized"

    def _current_modal_reference_dof(self) -> int | None:
        var = getattr(self, "result_viewer_dynamic_reference_dof_var", None)
        if var is None or not hasattr(var, "get"):
            return 1
        value = var.get()
        if value in (None, ""):
            return 1
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _modal_mode_shape_vector(self, mode_shape: object) -> list[float] | None:
        if isinstance(mode_shape, Mapping):
            if not mode_shape or not all(isinstance(key, int) for key in mode_shape):
                return None
            max_index = max(mode_shape, default=-1)
            return [float(mode_shape.get(index, 0.0)) for index in range(max_index + 1)]
        if isinstance(mode_shape, (list, tuple)):
            values = []
            for value in mode_shape:
                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    return None
            return values
        return None

    def _normalize_modal_mode_shape(
        self,
        mode_shape: object,
        normalization: str,
        reference_dof: int | None,
    ) -> tuple[list[float] | None, str | None]:
        vector = self._modal_mode_shape_vector(mode_shape)
        if vector is None:
            return None, "Phi values are unavailable for this mode shape format."
        if normalization == "Magnitude normalized":
            magnitude = max((abs(value) for value in vector), default=0.0)
            if magnitude <= self._display_tolerance():
                return vector[:], None
            return [value / magnitude for value in vector], None
        if normalization == "Specific DOF normalized":
            if reference_dof is None:
                return None, "Reference DOF must be an integer."
            if reference_dof < 1 or reference_dof > len(vector):
                return None, f"Reference DOF must be between 1 and {len(vector)}."
            reference_value = vector[reference_dof - 1]
            if abs(reference_value) <= self._display_tolerance():
                return None, f"Cannot normalize by DOF{reference_dof} because its phi value is zero."
            return [value / reference_value for value in vector], None
        return vector[:], None

    def _modal_results_with_display_shape(self, results: object, mode_index: int, mode_shape: list[float]) -> object:
        proxy = type("ModalResultsDisplayProxy", (), {})()
        proxy.__dict__.update(getattr(results, "__dict__", {}))
        shapes = list(getattr(results, "mode_shapes", []) or [])
        if 0 <= mode_index < len(shapes):
            shapes[mode_index] = mode_shape[:]
        proxy.mode_shapes = shapes
        return proxy

    def _modal_phi_table_data(self, mode_shape: list[float] | None, message: str | None = None) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        if message:
            return (("Message",), [(message,)])
        if mode_shape is None:
            return (("Message",), [("Phi values are unavailable.",)])
        return (
            ("DOF", "Phi"),
            [
                (f"DOF{index + 1}", self._format_number(value))
                for index, value in enumerate(mode_shape)
            ],
        )

    def _refresh_modal_mode_shape_controls(self) -> None:
        normalization_selector = getattr(self, "result_viewer_dynamic_mode_normalization_selector", None)
        if normalization_selector is not None:
            normalization_selector.configure(
                values=("Mass normalized", "Magnitude normalized", "Specific DOF normalized"),
                state="readonly",
            )

        reference_selector = getattr(self, "result_viewer_dynamic_reference_dof_selector", None)
        reference_var = getattr(self, "result_viewer_dynamic_reference_dof_var", None)
        results = self._current_modal_results()
        mode_index = self._current_modal_mode_index()
        dof_values: tuple[str, ...] = ()
        if results is not None and mode_index is not None:
            mode_shapes = getattr(results, "mode_shapes", None) or []
            if 0 <= mode_index < len(mode_shapes):
                vector = self._modal_mode_shape_vector(mode_shapes[mode_index])
                if vector is not None:
                    dof_values = tuple(str(index) for index in range(1, len(vector) + 1))

        if reference_selector is not None:
            normalization = self._current_modal_mode_normalization()
            state = "readonly" if normalization == "Specific DOF normalized" and dof_values else "disabled"
            reference_selector.configure(values=dof_values, state=state)
        if reference_var is not None:
            current_value = reference_var.get() if hasattr(reference_var, "get") else ""
            if dof_values:
                if current_value not in dof_values:
                    reference_var.set(dof_values[0])
            else:
                reference_var.set("1")

    def _refresh_modal_mode_shape_view(self) -> None:
        frame = getattr(self, "result_viewer_dynamic_plot_frame", None)
        if frame is None:
            return
        self._update_modal_mode_info_panel()
        self._clear_viewer_container(frame)
        self._refresh_modal_mode_shape_controls()
        canvas = getattr(self, "result_viewer_dynamic_plot_canvas", None)
        if canvas is not None:
            self.result_viewer_dynamic_plot_canvas = None
        phi_tree = getattr(self, "result_viewer_dynamic_phi_tree", None)
        results = self._current_modal_results()
        if results is None:
            message = self._result_window_message("modal")
            self._render_result_table(phi_tree, ("Message",), [(message,)], column_width=120)
            ttk.Label(frame, text=message).grid(row=0, column=0, sticky="nw")
            return
        message = self._modal_mode_shape_message(results)
        if message is not None:
            self._render_result_table(phi_tree, ("Message",), [(message,)], column_width=120)
            ttk.Label(frame, text=message).grid(row=0, column=0, sticky="nw")
            return
        mode_index = self._current_modal_mode_index()
        if mode_index is None:
            self._render_result_table(phi_tree, ("Message",), [("Invalid mode index.",)], column_width=120)
            ttk.Label(frame, text="Invalid mode index.").grid(row=0, column=0, sticky="nw")
            return
        model = getattr(getattr(self, "model_canvas", None), "builder", None)
        model = getattr(model, "model", None)
        if model is None:
            self._render_result_table(phi_tree, ("Message",), [("No model available for Modal results.",)], column_width=120)
            ttk.Label(frame, text="No model available for Modal results.").grid(row=0, column=0, sticky="nw")
            return
        mode_shapes = getattr(results, "mode_shapes", None) or []
        mode_shape = mode_shapes[mode_index] if 0 <= mode_index < len(mode_shapes) else None
        normalization = self._current_modal_mode_normalization()
        reference_dof = self._current_modal_reference_dof()
        normalized_shape, normalization_message = self._normalize_modal_mode_shape(mode_shape, normalization, reference_dof)
        phi_columns, phi_rows = self._modal_phi_table_data(normalized_shape, normalization_message)
        self._render_result_table(phi_tree, phi_columns, phi_rows, column_width=120)
        if normalization_message is not None:
            ttk.Label(frame, text=normalization_message).grid(row=0, column=0, sticky="nw")
            return
        try:
            display_results = self._modal_results_with_display_shape(results, mode_index, normalized_shape)
            fig, _ = plot_modal_mode_shape(model, display_results, mode_index=mode_index)
        except Exception as exc:
            self._render_result_table(phi_tree, ("Message",), [(str(exc),)], column_width=120)
            ttk.Label(frame, text=str(exc)).grid(row=0, column=0, sticky="nw")
            return
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        canvas.draw()
        self.result_viewer_dynamic_plot_canvas = canvas

    def _current_static_results(self):
        return getattr(self, "latest_static_result", None)

    def _current_modal_results(self):
        return getattr(self, "latest_modal_result", None)

    def _format_modal_summary_sequence(
        self,
        results: object,
        attribute_names: tuple[str, ...],
        limit: int | None,
        *,
        as_percent: bool = False,
    ) -> str:
        values = None
        for attribute_name in attribute_names:
            values = getattr(results, attribute_name, None)
            if values is not None:
                break
        if values is None:
            return "—"
        if not isinstance(values, (list, tuple)):
            values = [values]
        if isinstance(limit, int) and limit > 0:
            values = list(values)[:limit]
        formatted = []
        for value in values:
            if as_percent:
                formatted.append(f"{format_scalar(value * 100.0, tolerance=self._display_tolerance())}%")
            else:
                formatted.append(format_scalar(value, tolerance=self._display_tolerance()))
        return ", ".join(formatted) or "—"

    def _matrix_table(self, matrix: object, missing_message: str) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
        labels = dof_equation_labels(getattr(self._current_static_results(), "dof_map", None))
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
            f"FX [{units['force']}]",
            f"FY [{units['force']}]",
            f"MZ [{units['moment']}]",
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

    def _on_model_changed(self) -> None:
        self._refresh_object_tree()
        self._invalidate_analysis_results()

    def _invalidate_analysis_results(self, *, force_message: bool = False) -> None:
        had_results = self.latest_static_result is not None or self.latest_modal_result is not None
        if not had_results and not force_message:
            return
        self.latest_static_results = None
        self.latest_static_result = None
        self.static_analysis_error = None
        self.latest_modal_results = None
        self.latest_modal_result = None
        self.modal_analysis_error = None
        self._analysis_results_cleared = had_results or force_message
        results_window = getattr(self, "result_viewer_window", None)
        if results_window is not None and hasattr(results_window, "winfo_exists"):
            try:
                if results_window.winfo_exists():
                    self._refresh_results_viewer()
            except tk.TclError:
                pass

    def _reset_analysis_state(self) -> None:
        self._invalidate_analysis_results(force_message=False)
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
        if self._validate_current_model(show_dialog=True) is None:
            self._write_status("Model validation passed.")

    def _validate_current_model(self, *, show_dialog: bool) -> str | None:
        try:
            StructuralValidator(self.model_canvas.builder.model).validate()
        except UnstableStructureError as exc:
            message = str(exc) or "Model validation failed."
            if show_dialog:
                messagebox.showerror("Model Validation Failed", message, parent=self.root)
            self._write_status(message)
            return message
        except Exception as exc:
            message = str(exc) or "Model validation failed."
            if show_dialog:
                messagebox.showerror("Model Validation Failed", message, parent=self.root)
            self._write_status(message)
            return message
        return None

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
