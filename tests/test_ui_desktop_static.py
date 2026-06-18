import os
import sys
from types import SimpleNamespace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from model_builder import ModelBuilder
from parser import XMLParser
from ui.static_analysis import run_static_analysis
from ui_desktop import main_window
from ui_desktop.property_panel import PropertyPanel
from ui_desktop.template_dialog import NewModelDialog
from ui_desktop.result_formatting import dof_equation_labels, format_matrix, format_scalar
from visualizer import build_member_review_profile, plot_member_review_panel, plot_static_nvm_diagrams


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyWidget:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.configured = dict(kwargs)

    def grid(self, **_kwargs):
        pass

    def columnconfigure(self, *_args, **_kwargs):
        pass

    def rowconfigure(self, *_args, **_kwargs):
        pass

    def bind(self, *_args, **_kwargs):
        pass

    def configure(self, **kwargs):
        self.configured.update(kwargs)

    def set(self, *_args, **_kwargs):
        pass

    def winfo_children(self):
        return []

    def destroy(self):
        pass

    def tkraise(self):
        pass


class DummyFrame(DummyWidget):
    pass


class DummyLabel(DummyWidget):
    pass


class DummyButton(DummyWidget):
    pass


class DummyLabelFrame(DummyWidget):
    pass


class DummyScrollbar(DummyWidget):
    pass


class DummyCombobox(DummyWidget):
    pass


class DummyNotebook(DummyWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tabs = []
        self.selected = None

    def add(self, frame, text=""):
        self.tabs.append((frame, text))

    def select(self, frame):
        self.selected = frame


class DummyPanedwindow(DummyWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.added = []

    def add(self, child, **kwargs):
        self.added.append((child, kwargs))


class DummyMenu(DummyWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entries = []

    def add_cascade(self, **kwargs):
        self.entries.append(("cascade", kwargs))

    def add_command(self, **kwargs):
        self.entries.append(("command", kwargs))

    def add_checkbutton(self, **kwargs):
        self.entries.append(("checkbutton", kwargs))

    def add_separator(self):
        self.entries.append(("separator", {}))


class DummyTreeview(DummyWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.columns = ()
        self.rows = []
        self.headings = []
        self.column_options = {}

    def configure(self, **kwargs):
        super().configure(**kwargs)
        if "columns" in kwargs:
            self.columns = tuple(kwargs["columns"])

    def heading(self, column, text=""):
        self.headings.append((column, text))

    def column(self, column, **kwargs):
        self.column_options[column] = kwargs

    def get_children(self):
        return list(range(len(self.rows)))

    def delete(self, *_items):
        self.rows = []

    def insert(self, *_args, **kwargs):
        self.rows.append(tuple(kwargs.get("values", ())))

    def yview(self, *_args, **_kwargs):
        pass

    def xview(self, *_args, **_kwargs):
        pass


def _window_with_model(model=object()):
    window = main_window.MainWindow.__new__(main_window.MainWindow)
    window.model_canvas = SimpleNamespace(builder=SimpleNamespace(model=model))
    window.messages = []
    window._write_status = window.messages.append
    window.latest_static_results = None
    window.latest_static_result = None
    window.static_analysis_error = None
    window.latest_modal_results = None
    window.latest_modal_result = None
    window.modal_analysis_error = None
    window._analysis_results_cleared = False
    window._analysis_results_clear_message = "Results were cleared because the model changed. Run analysis again."
    window.modal_num_modes_var = DummyVar("3")
    window.modal_rayleigh_mode_i_var = DummyVar("1")
    window.modal_rayleigh_zeta_i_var = DummyVar("0.05")
    window.modal_rayleigh_mode_j_var = DummyVar("2")
    window.modal_rayleigh_zeta_j_var = DummyVar("0.05")
    window.result_view_category = None
    window.result_view_tree = None
    window.result_viewer_notebook = None
    window.result_viewer_table_tab = None
    window.result_viewer_dynamic_tab = None
    window.result_viewer_shell_tab = None
    window.result_viewer_dynamic_message = None
    window.result_viewer_dynamic_tree = None
    window.result_viewer_member_tab = None
    window.result_viewer_member_selector = None
    window.result_viewer_member_message = None
    window.result_viewer_member_notebook = None
    window.result_viewer_member_frames = {}
    window.result_viewer_member_forces_tree = None
    window.result_viewer_member_nvm_container = None
    window.result_viewer_member_nvm_canvas = None
    window.result_viewer_member_var = None
    window.result_viewer_member_plot_container = None
    window.result_viewer_member_plot_canvas = None
    window.result_viewer_member_canvas = None
    window.result_viewer_member_canvas_geometry = None
    window.result_viewer_member_profile_signature = None
    window.result_viewer_member_suppress_cursor_callback = False
    window.result_viewer_member_cursor_var = DummyVar("0")
    window.result_viewer_member_cursor_scale = None
    window.result_viewer_member_display_mode_var = DummyVar("Absolute")
    window.result_viewer_member_display_mode_selector = None
    window.result_viewer_member_scroll_var = DummyVar(True)
    window.result_viewer_member_show_max_var = DummyVar(True)
    window.result_viewer_member_profile = None
    window.result_viewer_member_review_state = None
    window.result_viewer_member_current_location_var = DummyVar("-")
    window.result_viewer_member_current_n_var = DummyVar("-")
    window.result_viewer_member_current_v_var = DummyVar("-")
    window.result_viewer_member_current_m_var = DummyVar("-")
    window.result_viewer_member_current_disp_var = DummyVar("-")
    window.result_viewer_member_max_n_var = DummyVar("-")
    window.result_viewer_member_max_v_var = DummyVar("-")
    window.result_viewer_member_max_m_var = DummyVar("-")
    window.result_viewer_member_max_disp_var = DummyVar("-")
    window.result_display_tolerance = 0.001
    window.result_tolerance_var = None
    window.result_viewer_dynamic_notebook = None
    window.result_viewer_dynamic_top_controls = None
    window.result_viewer_dynamic_summary_tab = None
    window.result_viewer_dynamic_mode_shapes_tab = None
    window.result_viewer_dynamic_matrices_tab = None
    window.result_viewer_dynamic_summary_tree = None
    window.result_viewer_dynamic_summary_vars = {}
    window.result_viewer_dynamic_mode_var = None
    window.result_viewer_dynamic_mode_selector = None
    window.result_viewer_dynamic_mode_normalization_var = DummyVar("Mass normalized")
    window.result_viewer_dynamic_mode_normalization_selector = None
    window.result_viewer_dynamic_reference_dof_var = DummyVar("1")
    window.result_viewer_dynamic_reference_dof_selector = None
    window.result_viewer_dynamic_matrix_selector = None
    window.result_viewer_dynamic_matrix_tree = None
    window.result_viewer_dynamic_mode_info_frame = None
    window.result_viewer_dynamic_mode_info_vars = {}
    window.result_viewer_dynamic_plot_frame = None
    window.result_viewer_dynamic_plot_canvas = None
    window.result_viewer_dynamic_phi_tree = None
    return window


def _sap_element_joint_forces(filepath):
    forces = {}
    in_table = False
    for line in Path(filepath).read_text().splitlines():
        stripped = line.strip()
        if stripped == "Table:  Element Joint Forces - Frames":
            in_table = True
            continue
        if in_table and stripped.startswith("Table:"):
            break
        if not in_table or not stripped or stripped.startswith("Frame") or stripped.startswith("KN"):
            continue
        parts = stripped.split()
        if len(parts) < 11:
            continue
        try:
            forces.setdefault(parts[0], []).append((float(parts[4]), float(parts[6]), -float(parts[8])))
        except ValueError:
            continue
    return forces


def _property_panel_for_builder(builder, selected_element_ids=None):
    panel = PropertyPanel.__new__(PropertyPanel)
    panel.messages = []
    panel.status_callback = panel.messages.append
    panel.current_command = "Materials / Sections"
    panel.material_id_var = DummyVar("m1")
    panel.assign_material_var = DummyVar("m1")
    panel.material_var = DummyVar("m1")
    panel.section_id_var = DummyVar("s1")
    panel.assign_section_var = DummyVar("s1")
    panel.section_var = DummyVar("s1")
    panel.show_calls = []
    panel.show_command = lambda command: panel.show_calls.append(command)
    panel.model_canvas = SimpleNamespace(
        builder=builder,
        selected_element_ids=set(selected_element_ids or []),
        redraws=0,
        changes=0,
        selected=None,
        redraw_model=lambda: setattr(panel.model_canvas, "redraws", panel.model_canvas.redraws + 1),
        change_callback=lambda: setattr(panel.model_canvas, "changes", panel.model_canvas.changes + 1),
        select_element=lambda element_id: setattr(panel.model_canvas, "selected", element_id),
        _set_multi_selection=lambda node_ids, element_ids: setattr(panel.model_canvas, "selected", sorted(element_ids)),
    )
    return panel


def test_materials_sections_assign_existing_definitions_to_selected_members():
    builder = ModelBuilder(name="Panel Model")
    builder.add_material("m1", E=1.0)
    builder.add_material("m2", E=2.0)
    builder.add_section("s1", A=1.0, I=1.0)
    builder.add_section("s2", A=2.0, I=2.0)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 1.0, 0.0)
    builder.add_node(3, 2.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    builder.add_element("e2", "frame", 2, 3, "m1", "s1")
    panel = _property_panel_for_builder(builder, {"e1", "e2"})
    panel.assign_material_var.set("m2")
    panel.assign_section_var.set("s2")

    panel._assign_material_section_to_selected_members()

    assert {element.material.id for element in builder.model.elements.values()} == {"m2"}
    assert {element.section.id for element in builder.model.elements.values()} == {"s2"}
    assert panel.messages[-1] == "Assigned material m2 and section s2 to 2 member(s)."
    assert panel.model_canvas.redraws == 1
    assert panel.model_canvas.changes == 1


def test_materials_sections_assignment_requires_selected_members():
    builder = ModelBuilder(name="Panel Model")
    builder.add_material("m1", E=1.0)
    builder.add_section("s1", A=1.0, I=1.0)
    panel = _property_panel_for_builder(builder)

    panel._assign_material_to_selected_members()

    assert panel.messages[-1] == "Select one or more members first."


def test_materials_sections_delete_blocks_used_definition_and_deletes_unused():
    builder = ModelBuilder(name="Panel Model")
    builder.add_material("m1", E=1.0)
    builder.add_material("m2", E=2.0)
    builder.add_section("s1", A=1.0, I=1.0)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 1.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    panel = _property_panel_for_builder(builder)

    panel.material_id_var.set("m1")
    panel._delete_material()
    assert panel.messages[-1] == "Material m1 is used by 1 member(s); reassign them before deleting."
    assert "m1" in builder.model.materials

    panel.material_id_var.set("m2")
    panel._delete_material()
    assert "m2" not in builder.model.materials
    assert panel.messages[-1] == "Deleted material m2."


def test_desktop_run_static_analysis_stores_result_and_status(monkeypatch):
    expected_results = SimpleNamespace(load_case_id="LC1", displacements={1: [0.0]}, reactions={1: [10.0]})

    def fake_run_static_analysis(model):
        return SimpleNamespace(ok=True, results=expected_results, error=None)

    monkeypatch.setattr(main_window, "run_static_analysis", fake_run_static_analysis)
    window = _window_with_model()

    window._toolbar_action("Run Static Analysis")

    assert window.latest_static_results is expected_results
    assert window.static_analysis_error is None
    assert "Static analysis complete for LC1" in window.messages[-1]


def test_desktop_run_static_analysis_reports_failure_without_crashing(monkeypatch):
    def fake_run_static_analysis(model):
        return SimpleNamespace(ok=False, results=None, error="Static analysis failed: unstable")

    monkeypatch.setattr(main_window, "run_static_analysis", fake_run_static_analysis)
    window = _window_with_model()
    window.latest_static_result = object()
    window.latest_static_results = object()

    window._toolbar_action("Run Static Analysis")

    assert window.latest_static_results is None
    assert window.static_analysis_error == "Static analysis failed: unstable"
    assert window.messages[-1] == "Static analysis failed: unstable"


def test_desktop_run_modal_analysis_stores_result_and_status(monkeypatch):
    expected_results = SimpleNamespace(num_modes_extracted=2)
    modal_calls = []

    monkeypatch.setattr(
        main_window,
        "run_modal_analysis",
        lambda model, num_modes=3, mass_matrix_type="lumped", rayleigh_target_mode_i=1, rayleigh_zeta_i=0.05, rayleigh_target_mode_j=2, rayleigh_zeta_j=0.05: modal_calls.append(
            (model, num_modes, rayleigh_target_mode_i, rayleigh_zeta_i, rayleigh_target_mode_j, rayleigh_zeta_j)
        ) or SimpleNamespace(ok=True, results=expected_results, error=None),
    )
    window = _window_with_model()
    window.modal_num_modes_var.set("4")

    window._toolbar_action("Run Modal Analysis")

    assert modal_calls == [(window.model_canvas.builder.model, 4, 1, 0.05, 2, 0.05)]
    assert window.latest_modal_results is expected_results
    assert window.latest_modal_result is expected_results
    assert window.modal_analysis_error is None
    assert window.messages[-1] == "Modal analysis complete: requested 4, extracted 2 mode(s)."


def test_desktop_run_modal_analysis_reports_mass_message(monkeypatch):
    monkeypatch.setattr(
        main_window,
        "run_modal_analysis",
        lambda model, num_modes=3, mass_matrix_type="lumped", rayleigh_target_mode_i=1, rayleigh_zeta_i=0.05, rayleigh_target_mode_j=2, rayleigh_zeta_j=0.05: SimpleNamespace(ok=False, results=None, error="Add mass before running modal analysis."),
    )
    window = _window_with_model()
    window.latest_static_result = object()
    window.latest_static_results = object()
    window.latest_static_result = object()
    window.latest_modal_results = object()
    window.latest_modal_result = object()

    window._toolbar_action("Run Modal Analysis")

    assert window.latest_modal_results is None
    assert window.latest_modal_result is None
    assert window.modal_analysis_error == "Assign masses before running Modal Analysis."
    assert window.messages[-1] == "Assign masses before running Modal Analysis."


def test_desktop_run_modal_analysis_stops_on_backend_error(monkeypatch):
    modal_calls = []
    monkeypatch.setattr(
        main_window,
        "run_modal_analysis",
        lambda model, num_modes=3, mass_matrix_type="lumped", rayleigh_target_mode_i=1, rayleigh_zeta_i=0.05, rayleigh_target_mode_j=2, rayleigh_zeta_j=0.05: modal_calls.append(
            (model, num_modes, rayleigh_target_mode_i, rayleigh_zeta_i, rayleigh_target_mode_j, rayleigh_zeta_j)
        ) or SimpleNamespace(ok=True, results=object(), error=None),
    )
    window = _window_with_model()
    window.modal_num_modes_var.set("2")
    window.latest_static_result = object()
    window.latest_static_results = object()

    window._toolbar_action("Run Modal Analysis")

    assert modal_calls == [(window.model_canvas.builder.model, 2, 1, 0.05, 2, 0.05)]
    assert window.latest_modal_results is not None
    assert window.modal_analysis_error is None


def test_desktop_modal_analysis_rejects_invalid_mode_count(monkeypatch):
    modal_calls = []
    monkeypatch.setattr(
        main_window,
        "run_modal_analysis",
        lambda model, num_modes=3, mass_matrix_type="lumped", rayleigh_target_mode_i=1, rayleigh_zeta_i=0.05, rayleigh_target_mode_j=2, rayleigh_zeta_j=0.05: modal_calls.append(
            (model, num_modes, rayleigh_target_mode_i, rayleigh_zeta_i, rayleigh_target_mode_j, rayleigh_zeta_j)
        ) or SimpleNamespace(ok=True, results=object(), error=None),
    )
    window = _window_with_model()
    window.modal_num_modes_var.set("0")

    window._toolbar_action("Run Modal Analysis")

    assert modal_calls == []
    assert window.latest_modal_results is None
    assert window.modal_analysis_error == "Number of modes must be at least 1."
    assert window.messages[-1] == "Number of modes must be at least 1."


def test_desktop_modal_results_builds_dropdown_layout(monkeypatch):
    window = _window_with_model()
    parent = DummyFrame()
    monkeypatch.setattr(main_window.tk, "StringVar", DummyVar)
    monkeypatch.setattr(main_window.ttk, "Frame", DummyFrame)
    monkeypatch.setattr(main_window.ttk, "Label", DummyLabel)
    monkeypatch.setattr(main_window.ttk, "Button", DummyButton)
    monkeypatch.setattr(main_window.ttk, "Combobox", DummyCombobox)
    monkeypatch.setattr(main_window.ttk, "LabelFrame", DummyLabelFrame)
    monkeypatch.setattr(main_window.ttk, "Treeview", DummyTreeview)
    monkeypatch.setattr(main_window.ttk, "Scrollbar", DummyScrollbar)

    window._build_modal_results_tab(parent)

    assert window.result_viewer_dynamic_view_selector.configured["values"] == ("Modal Summary", "Mode Shapes", "Matrices")
    assert window.result_viewer_dynamic_notebook is None
    assert window.result_viewer_dynamic_message.get() == "Run Modal Analysis first."
    assert window.result_viewer_dynamic_summary_tree.rows == [("Run Modal Analysis first.",)]
    assert window.result_viewer_dynamic_mode_selector.configured["state"] == "disabled"
    assert window.result_viewer_dynamic_matrix_selector.configured["state"] == "disabled"
    assert window.result_viewer_dynamic_reference_dof_selector.configured["state"] == "disabled"


def test_desktop_static_viewer_builds_dropdown_selector(monkeypatch):
    window = _window_with_model()
    parent = DummyFrame()
    monkeypatch.setattr(main_window.tk, "StringVar", DummyVar)
    monkeypatch.setattr(main_window.ttk, "Frame", DummyFrame)
    monkeypatch.setattr(main_window.ttk, "Label", DummyLabel)
    monkeypatch.setattr(main_window.ttk, "Button", DummyButton)
    monkeypatch.setattr(main_window.ttk, "Combobox", DummyCombobox)
    monkeypatch.setattr(main_window.ttk, "Treeview", DummyTreeview)
    monkeypatch.setattr(main_window.ttk, "Scrollbar", DummyScrollbar)

    window._build_static_results_viewer_tab(parent)

    assert window.result_viewer_plot_view_selector.configured["values"] == ("Deformed Shape", "Axial Force N", "Shear Force V", "Bending Moment M")
    assert window.result_viewer_plot_notebook is None


def test_desktop_command_area_builds_dropdown_menus(monkeypatch):
    window = _window_with_model()
    window.root = SimpleNamespace(config=lambda **kwargs: setattr(window, "configured_menu", kwargs.get("menu")))
    window.grid_visible = DummyVar(True)
    window.snap_to_grid = DummyVar(False)
    window.local_axes_visible = DummyVar(False)
    window.grid_spacing = DummyVar("1.0")
    window.modal_num_modes_var = DummyVar("3")
    window.modal_rayleigh_mode_i_var = DummyVar("1")
    window.modal_rayleigh_zeta_i_var = DummyVar("0.05")
    window.modal_rayleigh_mode_j_var = DummyVar("2")
    window.modal_rayleigh_zeta_j_var = DummyVar("0.05")
    created = []

    def fake_menu(*args, **kwargs):
        menu = DummyMenu(*args, **kwargs)
        created.append(menu)
        return menu

    monkeypatch.setattr(main_window.tk, "Menu", fake_menu)

    window._build_command_area()

    assert window.configured_menu is created[0]
    assert len(created) == len(main_window.COMMAND_TABS) + 1
    assert [entry[1]["label"] for entry in created[0].entries if entry[0] == "cascade"] == [name for name, _items in main_window.COMMAND_TABS]
    edit_entries = next(entry[1]["menu"].entries for entry in created[0].entries if entry[0] == "cascade" and entry[1]["label"] == "Edit")
    view_entries = next(entry[1]["menu"].entries for entry in created[0].entries if entry[0] == "cascade" and entry[1]["label"] == "View")
    assert not any(item[1].get("label") == "Move Selection" for item in edit_entries if item[0] == "command")
    assert not any(item[1].get("label") == "Window Select" for item in view_entries if item[0] == "command")


def test_desktop_new_model_dialog_exposes_revised_template_options():
    assert NewModelDialog.TEMPLATE_OPTIONS == ("Blank Model", "2D Shear Frame Template")


def test_desktop_workspace_uses_horizontal_panedwindow(monkeypatch):
    window = _window_with_model()
    window.root = DummyFrame()
    window._refresh_object_tree = lambda: None
    window._select_from_tree = lambda *_args: None
    window._show_selection = lambda *_args: None
    window._write_status = lambda *_args: None
    monkeypatch.setattr(main_window.ttk, "Panedwindow", DummyPanedwindow)
    monkeypatch.setattr(main_window.ttk, "Frame", DummyFrame)
    monkeypatch.setattr(main_window, "ObjectTreePanel", lambda parent, selection_callback=None: SimpleNamespace(grid=lambda **_kw: None))
    monkeypatch.setattr(main_window, "ModelCanvas", lambda *args, **kwargs: SimpleNamespace(grid=lambda **_kw: None, canvas=object()))

    window._build_workspace_area()

    assert window.workspace_panedwindow.kwargs["orient"] == main_window.tk.HORIZONTAL
    assert len(window.workspace_panedwindow.added) == 2


def test_desktop_move_selection_translates_selected_objects_and_elements():
    builder = ModelBuilder(name="Move Model")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    canvas = main_window.ModelCanvas.__new__(main_window.ModelCanvas)
    canvas.builder = builder
    canvas.selected_node_ids = {1}
    canvas.selected_element_ids = {"e1"}
    canvas._selection_count = lambda: 2
    canvas._mark_model_dirty = lambda: None
    canvas.redraw_model = lambda *args, **kwargs: None
    canvas.change_callback = lambda: None
    canvas.status_callback = lambda *_args: None
    canvas._set_multi_selection = lambda node_ids, element_ids: setattr(canvas, "selection_snapshot", (set(node_ids), set(element_ids)))

    result = canvas.move_selection(1.5, -0.5)

    assert result == (2, 1)
    assert builder.model.nodes[1].x == 1.5
    assert builder.model.nodes[1].y == -0.5
    assert builder.model.nodes[2].x == 4.5
    assert builder.model.nodes[2].y == -0.5


def test_desktop_modal_summary_shows_one_row_per_mode():
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(
        num_modes_requested=3,
        num_modes_extracted=2,
        eigenvalues=[4.0, 9.0],
        frequencies=[1.0, 2.0],
        periods=[1.0, 0.5],
        modal_masses=[0.8, 0.2],
        participation_factors=[0.9, 0.1],
        effective_masses=[0.7, 0.2],
        mass_participation_ratios=[0.7, 0.9],
        modal_damping_ratios=[0.05, 0.04],
        rayleigh_alpha=0.5959,
        rayleigh_beta=0.003557,
        rayleigh_target_modes=(1, 2),
        rayleigh_target_damping_ratios=(0.05, 0.05),
    )
    window.result_viewer_dynamic_summary_tree = DummyTreeview()
    window.result_viewer_dynamic_mode_selector = DummyCombobox()
    window.result_viewer_dynamic_mode_normalization_selector = DummyCombobox()
    window.result_viewer_dynamic_reference_dof_selector = DummyCombobox()
    window.result_viewer_dynamic_matrix_selector = DummyCombobox()
    window.result_viewer_dynamic_mode_var = DummyVar("1")
    window.result_viewer_dynamic_category = DummyVar("Kff")
    window.result_viewer_dynamic_message = DummyVar("-")

    window._refresh_modal_summary()

    assert window.result_viewer_dynamic_summary_tree.columns == (
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
    assert len(window.result_viewer_dynamic_summary_tree.rows) == 2
    assert window.result_viewer_dynamic_summary_tree.rows[0] == ("1", "4", "2", "1", "1", "0.8", "0.9", "0.7", "70%", "5%")
    assert window.result_viewer_dynamic_summary_tree.rows[1] == ("2", "9", "3", "2", "0.5", "0.2", "0.1", "0.2", "90%", "4%")
    assert window.result_viewer_dynamic_mode_selector.configured["values"] == ("1", "2")
    assert "Modal results ready." in window.result_viewer_dynamic_message.get()
    assert "alpha = 0.596" in window.result_viewer_dynamic_message.get()
    assert "beta = 0.004" in window.result_viewer_dynamic_message.get()


def test_desktop_modal_summary_handles_missing_optional_fields():
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(
        num_modes_requested=2,
        num_modes_extracted=1,
        frequencies=[3.0],
    )
    window.result_viewer_dynamic_summary_tree = DummyTreeview()
    window.result_viewer_dynamic_mode_selector = DummyCombobox()
    window.result_viewer_dynamic_mode_normalization_selector = DummyCombobox()
    window.result_viewer_dynamic_reference_dof_selector = DummyCombobox()
    window.result_viewer_dynamic_matrix_selector = DummyCombobox()
    window.result_viewer_dynamic_mode_var = DummyVar("1")
    window.result_viewer_dynamic_category = DummyVar("Kff")
    window.result_viewer_dynamic_message = DummyVar("-")

    window._refresh_modal_summary()

    assert window.result_viewer_dynamic_summary_tree.rows == [("1", "—", "—", "3", "—", "—", "—", "—", "—", "—")]
    assert window.result_viewer_dynamic_mode_selector.configured["values"] == ("1",)
    assert window.result_viewer_dynamic_message.get() == "Modal results ready."


def test_desktop_modal_mode_shape_view_renders_selected_mode(monkeypatch):
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(
        mode_shapes=[[0.0, 0.2, 0.0], [0.0, 0.4, 0.0]],
        eigenvalues=[4.0, 9.0],
        frequencies=[2.0, 4.0],
        periods=[0.5, 0.25],
        modal_masses=[0.8, 0.2],
        participation_factors=[0.9, 0.1],
        effective_masses=[0.7, 0.2],
        mass_participation_ratios=[0.7, 0.9],
        num_modes_extracted=2,
    )
    window.result_viewer_dynamic_mode_var = DummyVar("2")
    window.result_viewer_dynamic_mode_normalization_var = DummyVar("Specific DOF normalized")
    window.result_viewer_dynamic_reference_dof_var = DummyVar("2")
    window.result_viewer_dynamic_mode_normalization_selector = DummyCombobox()
    window.result_viewer_dynamic_reference_dof_selector = DummyCombobox()
    window.result_viewer_dynamic_mode_info_vars = {
        "Mode": DummyVar("—"),
        "Eigenvalue (ω²)": DummyVar("—"),
        "Frequency": DummyVar("—"),
        "Period": DummyVar("—"),
        "Modal Mass": DummyVar("—"),
        "Participation Factor": DummyVar("—"),
        "Effective Mass": DummyVar("—"),
        "Participation Ratio": DummyVar("—"),
        "Modal Damping Ratio": DummyVar("—"),
    }
    window.result_viewer_dynamic_plot_frame = DummyFrame()
    window.result_viewer_dynamic_phi_tree = DummyTreeview()
    window.result_viewer_dynamic_plot_canvas = None
    calls = []

    class DummyCanvas:
        def __init__(self, fig, master=None):
            calls.append(("canvas", master))
            self._widget = SimpleNamespace(grid=lambda **_kw: None)

        def get_tk_widget(self):
            return self._widget

        def draw(self):
            calls.append(("draw", None))

    monkeypatch.setattr(main_window, "FigureCanvasTkAgg", DummyCanvas)
    monkeypatch.setattr(
        main_window,
        "plot_modal_mode_shape",
        lambda model, results, mode_index=0, scale_factor=None, ax=None: calls.append(("shape", results.mode_shapes[mode_index])) or (SimpleNamespace(), None),
    )

    window._refresh_modal_mode_shape_view()

    assert ("shape", [0.0, 1.0, 0.0]) in calls
    assert ("canvas", window.result_viewer_dynamic_plot_frame) in calls
    assert window.result_viewer_dynamic_mode_info_vars["Mode"].get() == "2"
    assert window.result_viewer_dynamic_mode_info_vars["Eigenvalue (ω²)"].get() == "9"
    assert window.result_viewer_dynamic_mode_info_vars["Frequency"].get() == "4"
    assert window.result_viewer_dynamic_mode_info_vars["Effective Mass"].get() == "0.2"
    assert window.result_viewer_dynamic_mode_info_vars["Participation Ratio"].get() == "90%"
    assert window.result_viewer_dynamic_phi_tree.rows == [("DOF1", "0"), ("DOF2", "1"), ("DOF3", "0")]


def test_desktop_modal_mode_shape_view_reports_missing_shapes(monkeypatch):
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(mode_shapes=[], num_modes_extracted=0)
    window.result_viewer_dynamic_mode_var = DummyVar("1")
    window.result_viewer_dynamic_mode_normalization_selector = DummyCombobox()
    window.result_viewer_dynamic_reference_dof_selector = DummyCombobox()
    window.result_viewer_dynamic_mode_info_vars = {
        "Mode": DummyVar("—"),
        "Eigenvalue (ω²)": DummyVar("—"),
        "Frequency": DummyVar("—"),
        "Period": DummyVar("—"),
        "Modal Mass": DummyVar("—"),
        "Participation Factor": DummyVar("—"),
        "Effective Mass": DummyVar("—"),
        "Participation Ratio": DummyVar("—"),
        "Modal Damping Ratio": DummyVar("—"),
    }
    window.result_viewer_dynamic_plot_frame = DummyFrame()
    window.result_viewer_dynamic_phi_tree = DummyTreeview()
    labels = []
    monkeypatch.setattr(main_window.ttk, "Label", lambda *args, **kwargs: SimpleNamespace(grid=lambda **_kw: labels.append(kwargs.get("text"))))

    window._refresh_modal_mode_shape_view()

    assert "Modal result does not contain mode shapes." in labels


def test_desktop_modal_mode_shape_view_rejects_invalid_index(monkeypatch):
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(mode_shapes=[[0.0, 0.2, 0.0]], periods=[0.5], frequencies=[2.0], num_modes_extracted=1)
    window.result_viewer_dynamic_mode_var = DummyVar("9")
    window.result_viewer_dynamic_mode_normalization_selector = DummyCombobox()
    window.result_viewer_dynamic_reference_dof_selector = DummyCombobox()
    window.result_viewer_dynamic_mode_info_vars = {
        "Mode": DummyVar("—"),
        "Eigenvalue (ω²)": DummyVar("—"),
        "Frequency": DummyVar("—"),
        "Period": DummyVar("—"),
        "Modal Mass": DummyVar("—"),
        "Participation Factor": DummyVar("—"),
        "Effective Mass": DummyVar("—"),
        "Participation Ratio": DummyVar("—"),
        "Modal Damping Ratio": DummyVar("—"),
    }
    window.result_viewer_dynamic_plot_frame = DummyFrame()
    window.result_viewer_dynamic_phi_tree = DummyTreeview()
    labels = []
    monkeypatch.setattr(main_window.ttk, "Label", lambda *args, **kwargs: SimpleNamespace(grid=lambda **_kw: labels.append(kwargs.get("text"))))

    window._refresh_modal_mode_shape_view()

    assert "Invalid mode index." in labels


def test_desktop_modal_mode_shape_magnitude_normalization_sets_unit_peak():
    window = _window_with_model()

    normalized, message = window._normalize_modal_mode_shape([0.25, -2.0, 0.5], "Magnitude normalized", None)

    assert message is None
    assert max(abs(value) for value in normalized) == 1.0


def test_desktop_modal_mode_shape_specific_dof_normalization_sets_selected_dof_to_one():
    window = _window_with_model()

    normalized, message = window._normalize_modal_mode_shape([0.5, -2.0, 1.0], "Specific DOF normalized", 2)

    assert message is None
    assert normalized[1] == 1.0


def test_desktop_modal_mode_shape_specific_dof_zero_value_reports_clear_message():
    window = _window_with_model()

    normalized, message = window._normalize_modal_mode_shape([0.0, 1.0, 2.0], "Specific DOF normalized", 1)

    assert normalized is None
    assert message == "Cannot normalize by DOF1 because its phi value is zero."


def test_desktop_modal_mode_shape_specific_dof_near_zero_value_reports_clear_message():
    window = _window_with_model()

    normalized, message = window._normalize_modal_mode_shape([1.0e-13, 1.0, 2.0], "Specific DOF normalized", 1)

    assert normalized is None
    assert message == "Cannot normalize by DOF1 because its phi value is zero."


def test_desktop_modal_results_empty_state_uses_singular_cache():
    window = _window_with_model()

    window.latest_modal_result = None
    window.latest_modal_results = object()

    columns, rows = window._modal_result_rows()

    assert columns == ("Message",)
    assert rows == [("Run Modal Analysis first.",)]


def test_desktop_modal_matrix_selector_exposes_optional_damping_matrices():
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(
        Kff=[[10.0, 0.0], [0.0, 5.0]],
        Mff=[[2.0, 0.0], [0.0, 1.0]],
        Cff=[[0.5, 0.0], [0.0, 0.25]],
    )
    window.latest_static_result = None

    assert window._modal_result_categories() == ["Kff", "Mff", "Cff"]

    window.result_viewer_dynamic_category = DummyVar("Kff")
    columns, rows = window._modal_result_rows()
    assert columns == ("DOF", "DOF1", "DOF2")
    assert rows == [("DOF1", "10", "0"), ("DOF2", "0", "5")]

    window.result_viewer_dynamic_category = DummyVar("Mff")
    columns, rows = window._modal_result_rows()
    assert columns == ("DOF", "DOF1", "DOF2")
    assert rows == [("DOF1", "2", "0"), ("DOF2", "0", "1")]

    window.result_viewer_dynamic_category = DummyVar("Cff")
    columns, rows = window._modal_result_rows()
    assert columns == ("DOF", "DOF1", "DOF2")
    assert rows == [("DOF1", "0.5", "0"), ("DOF2", "0", "0.25")]


def test_desktop_modal_matrix_tab_falls_back_to_indices_without_dof_labels():
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(
        K=[[1.0, 2.0], [3.0, 4.0]],
        num_modes_extracted=1,
    )
    window.latest_static_result = None
    window.result_viewer_dynamic_category = DummyVar("Kff")

    columns, rows = window._modal_result_rows()

    assert columns == ("DOF", "DOF1", "DOF2")
    assert rows == [("DOF1", "1", "2"), ("DOF2", "3", "4")]


def test_desktop_modal_matrix_selector_hides_cff_without_computed_rayleigh_damping():
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(
        Kff=[[1.0]],
        Mff=[[2.0]],
        Cff=None,
        dynamic_assembly=SimpleNamespace(Cff=[[0.0]]),
    )

    assert window._modal_result_categories() == ["Kff", "Mff"]


def test_desktop_modal_matrix_tab_uses_modal_result_without_static_result():
    window = _window_with_model()
    window.latest_modal_result = SimpleNamespace(
        Kff=[[1.0]],
        Mff=[[2.0]],
        dynamic_assembly=SimpleNamespace(dof_map={1: [0]}),
        num_modes_extracted=1,
    )
    window.latest_static_result = None
    window.result_viewer_dynamic_tree = DummyTreeview()
    window.result_viewer_dynamic_category = DummyVar("Mff")

    window._refresh_modal_matrix_table()

    assert window.result_viewer_dynamic_tree.rows == [("DOF1", "2")]


def test_desktop_static_results_empty_state_uses_singular_cache():
    window = _window_with_model()

    window.latest_static_result = None
    window.latest_static_results = object()

    columns, rows = window._static_result_table_data("Nodal Displacements")

    assert columns == ("Message",)
    assert rows == [("Run Static Analysis first.",)]


def test_desktop_static_result_tables_use_cached_result_fields():
    results = SimpleNamespace(
        displacements={1: [0.001, 0.0, 0.0]},
        reactions={1: [10.0, -2.5, 1.0e-12]},
        element_forces={"e1": {"i": [[10.0], [0.0], [0.0]], "j": [[-10.0], [0.0], [0.0]]}},
        member_end_forces={"e1": {"i": [[-10.0], [0.0], [0.0]], "j": [[10.0], [0.0], [0.0]]}},
        dof_map={1: [0, 1, 2]},
        K=[[1.0, 0.0], [0.0, 1.0]],
        Kff=[[1.0]],
        F=[10.0, 0.0],
        Ff=[10.0],
    )
    window = _window_with_model()
    window.latest_static_result = results
    window.latest_static_result = results
    window.latest_static_results = results

    columns, rows = window._static_result_table_data("Nodal Displacements")
    assert columns == ("Node", "UX [m]", "UY [m]", "RZ [rad]")
    assert rows == [("1", "0.001", "0", "0")]

    columns, rows = window._static_result_table_data("Support Reactions")
    assert columns == ("Node", "FX [kN]", "FY [kN]", "MZ [kN-m]")
    assert rows == [("1", "10", "-2.5", "0")]

    columns, rows = window._static_result_table_data("Member End Forces")
    assert columns == ("Element", "End", "FX [kN]", "FY [kN]", "MZ [kN-m]")
    assert ("e1", "i", "-10", "0", "0") in rows

    columns, rows = window._static_result_table_data("DOF Map")
    assert columns == ("Node", "UX", "UY", "RZ")
    assert rows == [("1", "Eq 0", "Eq 1", "Eq 2")]

    columns, rows = window._static_result_table_data("Global Stiffness Matrix K")
    assert columns == ("DOF", "N1 UX", "N1 UY")
    assert rows == [("N1 UX", "1", "0"), ("N1 UY", "0", "1")]

    columns, rows = window._static_result_table_data("Global Force Vector F")
    assert columns == ("DOF", "N1 UX")
    assert rows == [("N1 UX", "10"), ("N1 UY", "0")]


def test_desktop_static_displacements_are_visible_at_default_tolerance():
    results = SimpleNamespace(
        displacements={
            1: [0.0, 0.0, -6.607477511e-4],
            2: [3.590705577e-6, -1.993742507e-3, -1.738113785e-4],
        },
        reactions={},
        element_forces={},
        dof_map={},
        K=None,
        Kff=None,
        F=None,
        Ff=None,
    )
    window = _window_with_model()
    window.result_display_tolerance = main_window.DEFAULT_DISPLAY_TOLERANCE
    window.latest_static_result = results
    window.latest_static_results = results

    columns, rows = window._static_result_table_data("Nodal Displacements")

    assert columns == ("Node", "UX [m]", "UY [m]", "RZ [rad]")
    assert rows[0] == ("1", "0", "0", "-0.000660748")
    assert rows[1] == ("2", "0.000003591", "-0.001993743", "-0.000173811")


def test_desktop_matrix_labels_use_node_dof_names_from_dof_map():
    labels = dof_equation_labels({1: [-1, -1, 3], 2: [0, 1, 2]})

    assert labels == ("N2 UX", "N2 UY", "N2 RZ", "N1 RZ")


def test_desktop_result_formatting_handles_near_zero_and_missing_intermediate_data():
    raw_matrix = [[1.0e-12, 2.5]]

    assert format_scalar(1.0e-12, tolerance=0.001) == "0"
    assert format_scalar(1.23456, tolerance=0.001) == "1.235"
    assert format_matrix(raw_matrix, tolerance=0.001) == [("0", "2.5")]
    assert raw_matrix == [[1.0e-12, 2.5]]
    assert format_matrix([10.0, 0.0], tolerance=0.001) == [("10",), ("0",)]

    results = SimpleNamespace(
        displacements={},
        reactions={},
        element_forces={},
        dof_map={},
        K=None,
        Kff=None,
        F=None,
        Ff=None,
    )
    window = _window_with_model()
    window.latest_static_result = results
    window.latest_static_result = results
    window.latest_static_results = results

    columns, rows = window._static_result_table_data("Reduced Force Vector Ff")
    assert columns == ("Message",)
    assert rows == [("Reduced force vector Ff is unavailable.",)]


def test_desktop_dof_map_uses_cached_model_mapping_when_result_field_missing():
    model = SimpleNamespace(unit_system="kN_m_tonne", cached_dof_map={2: [-1, 4, -1]})
    window = _window_with_model(model=model)
    window.latest_static_result = SimpleNamespace(
        displacements={},
        reactions={},
        element_forces={},
        dof_map=None,
        K=None,
        Kff=None,
        F=None,
        Ff=None,
    )
    window.latest_static_results = window.latest_static_result

    columns, rows = window._static_result_table_data("DOF Map")

    assert columns == ("Node", "UX", "UY", "RZ")
    assert rows == [("2", "Fixed", "Eq 4", "Fixed")]


def test_desktop_member_force_rows_unwrap_nested_scalar_lists():
    model = SimpleNamespace(unit_system="kN_m_tonne")
    window = _window_with_model(model=model)

    columns, rows = window._member_force_rows({"e2": [[3.2], [0.0004], [-1.2], [-3.2], [0.0], [1.2]]}, {"force": "kN", "moment": "kN-m"})

    assert columns == ("Element", "End", "FX [kN]", "FY [kN]", "MZ [kN-m]")
    assert ("e2", "i", "3.2", "0", "-1.2") in rows
    assert ("e2", "j", "-3.2", "0", "1.2") in rows


def test_desktop_member_force_rows_do_not_use_diagram_endpoint_signs():
    model = SimpleNamespace(unit_system="kN_m_tonne")
    window = _window_with_model(model=model)
    element_forces = {"F2": [[1.667], [-2.222], [17.779], [1.667], [-2.222], [0.0]]}
    nvm_data = {"F2": {"N": [1.667, 1.667], "V": [2.222, 2.222], "M": [17.779, 0.0]}}

    columns, rows = window._member_force_rows(element_forces, {"force": "kN", "moment": "kN-m"})

    assert columns == ("Element", "End", "FX [kN]", "FY [kN]", "MZ [kN-m]")
    assert ("F2", "i", "1.667", "-2.222", "17.779") in rows
    assert ("F2", "j", "1.667", "-2.222", "0") in rows
    assert nvm_data["F2"]["V"][0] == 2.222


def test_settlement_member_end_forces_match_sap2000_sign_convention():
    repo_root = Path(__file__).resolve().parents[1]
    model = XMLParser(str(repo_root / "data" / "test-settlement.xml")).parse()
    result = run_static_analysis(model)
    assert result.ok

    expected = _sap_element_joint_forces(repo_root / "sap2000" / "test-settlement-results.txt")
    for element_id in ("F1", "F2", "F4", "T1"):
        computed = result.results.member_end_forces[element_id]
        for end_label, joint_index in (("i", 0), ("j", 1)):
            sap_fx, sap_fy, sap_mz = expected[element_id][joint_index]
            for computed_value, expected_value in zip(computed[end_label], (sap_fx, sap_fy, sap_mz)):
                assert abs(computed_value - expected_value) <= max(0.15, 0.03 * abs(expected_value))


def test_cantilever_member_end_forces_match_support_equilibrium():
    builder = ModelBuilder(name="cantilever")
    builder.add_material("m", E=200000000.0)
    builder.add_section("s", A=1.0, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m", "s")
    builder.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)
    builder.add_nodal_load("LC1", 2, fy=-10.0, load_case_name="tip")

    result = run_static_analysis(builder.model, "LC1")

    assert result.ok
    assert all(abs(actual - expected) < 1.0e-9 for actual, expected in zip(result.results.member_end_forces["e1"]["i"], [0.0, 10.0, 30.0]))
    assert abs(result.results.member_end_forces["e1"]["j"][1] - (-10.0)) < 1.0e-9


def test_desktop_static_result_table_empty_state():
    window = _window_with_model()

    columns, rows = window._static_result_table_data("Nodal Displacements")

    assert columns == ("Message",)
    assert rows == [("Run Static Analysis first.",)]


def test_desktop_results_button_callback_handles_partial_viewer_state(monkeypatch):
    window = _window_with_model()
    selected_tabs = []
    refreshes = []
    window.result_viewer_notebook = SimpleNamespace(select=lambda tab: selected_tabs.append(tab))
    delattr(window, "result_viewer_table_tab")
    window._create_results_window = lambda mode="static": object()
    window._refresh_static_result_table = lambda: refreshes.append("table")
    window._refresh_static_viewer = lambda: refreshes.append("viewer")

    window._toolbar_action("Modal Results")

    assert refreshes == []
    assert selected_tabs == []
    assert window.messages[-1] == "Run Modal Analysis first."


def test_desktop_results_window_switches_between_static_and_dynamic_modes(monkeypatch):
    window = _window_with_model()
    window.root = object()
    window.result_viewer_mode = None
    calls = []

    class DummyWindow:
        def __init__(self, mode):
            self.mode = mode

        def winfo_exists(self):
            return True

        def title(self, _text):
            pass

        def geometry(self, _text):
            pass

        def columnconfigure(self, *_args, **_kwargs):
            pass

        def rowconfigure(self, *_args, **_kwargs):
            pass

        def protocol(self, *_args, **_kwargs):
            pass

        def lift(self):
            calls.append(("lift", self.mode))

        def focus_force(self):
            calls.append(("focus", self.mode))

        def destroy(self):
            calls.append(("destroy", self.mode))

    class DummyFrame:
        def __init__(self, *args, **kwargs):
            pass

        def grid(self, **_kwargs):
            pass

        def columnconfigure(self, *_args, **_kwargs):
            pass

        def rowconfigure(self, *_args, **_kwargs):
            pass

    class DummyNotebook(DummyFrame):
        def add(self, *_args, **_kwargs):
            pass

    class DummyLabel(DummyFrame):
        pass

    class DummyButton(DummyFrame):
        pass

    def fake_close():
        calls.append(("close", window.result_viewer_mode))
        window.result_viewer_window = None
        window.result_viewer_mode = None

    def fake_toplevel(_root):
        mode = window.result_viewer_mode or "static"
        win = DummyWindow(mode)
        calls.append(("create", mode))
        return win

    monkeypatch.setattr(main_window.tk, "Toplevel", fake_toplevel)
    monkeypatch.setattr(main_window.ttk, "Frame", DummyFrame)
    monkeypatch.setattr(main_window.ttk, "Notebook", DummyNotebook)
    monkeypatch.setattr(main_window.ttk, "Combobox", DummyCombobox)
    monkeypatch.setattr(main_window.ttk, "Label", DummyLabel)
    monkeypatch.setattr(main_window.ttk, "Button", DummyButton)
    monkeypatch.setattr(window, "_build_static_results_table_tab", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(window, "_build_static_results_viewer_tab", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(window, "_build_individual_member_results_viewer_tab", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(window, "_build_modal_results_tab", lambda *_args, **_kwargs: None)
    window._close_static_results_window = fake_close

    static_win = window._create_results_window("static")
    assert static_win.mode == "static"
    dynamic_win = window._create_results_window("modal")

    assert dynamic_win.mode == "static"
    assert ("close", "static") in calls
    assert calls.count(("create", "static")) == 2


def test_desktop_results_workflow_initializes_individual_member_tab(monkeypatch):
    builder = ModelBuilder(name="Viewer Model")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    window = _window_with_model(model=builder.model)
    window.latest_static_result = SimpleNamespace(
        load_case_id="LC1",
        displacements={1: [0.0, 0.0, 0.0], 2: [0.01, 0.02, 0.03]},
        element_forces={"e1": {"i": [1.0, 2.0, 3.0], "j": [-4.0, -5.0, -6.0]}},
        nvm_data={"e1": {"x": [0.0, 1.5, 3.0], "N": [5.0, -8.0, 2.0], "V": [1.0, -3.0, 4.0], "M": [0.5, 2.5, -1.0]}},
    )

    class DummyFrame:
        def winfo_children(self):
            return []

        def columnconfigure(self, *_args, **_kwargs):
            pass

        def rowconfigure(self, *_args, **_kwargs):
            pass

    class DummySelector:
        def configure(self, **_kwargs):
            pass

    class DummyScale:
        def configure(self, **_kwargs):
            pass

        def set(self, _value):
            pass

    class DummyCanvas:
        def __init__(self, *args, **kwargs):
            pass

        def grid(self, **_kwargs):
            pass

        def bind(self, *_args, **_kwargs):
            pass

        def winfo_exists(self):
            return True

        def winfo_width(self):
            return 800

        def winfo_height(self):
            return 520

        def delete(self, *_args):
            pass

        def create_text(self, *_args, **_kwargs):
            pass

        def create_line(self, *_args, **_kwargs):
            pass

        def create_oval(self, *_args, **_kwargs):
            pass

        def create_polygon(self, *_args, **_kwargs):
            pass

    selected_tabs = []
    table_tab = object()
    monkeypatch.setattr(main_window.tk, "Canvas", DummyCanvas)

    def fake_create_results_window(mode="static"):
        window.result_viewer_notebook = SimpleNamespace(select=lambda tab: selected_tabs.append(tab))
        window.result_viewer_content_frame = DummyFrame()
        if mode == "static":
            window.result_viewer_section_var = DummyVar("Static Results")
            window.result_viewer_table_tab = table_tab
            window.result_viewer_member_var = DummyVar("e1")
            window.result_viewer_member_selector = DummySelector()
            window.result_viewer_member_message = DummyVar("Select a member to review static results.")
            window.result_viewer_member_display_mode_var = DummyVar("Absolute")
            window.result_viewer_member_scroll_var = DummyVar(True)
            window.result_viewer_member_show_max_var = DummyVar(True)
            window.result_viewer_member_cursor_var = DummyVar("1.5")
            window.result_viewer_member_cursor_scale = DummyScale()
            window.result_viewer_member_plot_container = DummyFrame()
            window._refresh_individual_member_viewer()
        else:
            window.result_viewer_section_var = DummyVar("Modal Results")
            window.result_viewer_dynamic_tab = table_tab
        return object()

    window._create_results_window = fake_create_results_window
    window._refresh_static_result_table = lambda: None
    window._refresh_static_viewer = lambda: None

    window._toolbar_action("Static Results")

    assert selected_tabs == [table_tab]
    assert window.result_viewer_member_message.get() == "Member e1 selected for static review."
    assert window.messages[-1] == "Static results opened."


def test_desktop_static_complete_model_viewer_renders_plots(monkeypatch):
    assert main_window.COMMAND_TABS[-1][1] == (("action", "Static Results"), ("action", "Modal Results"))
    window = _window_with_model()

    class DummyFrame:
        def winfo_children(self):
            return []

        def columnconfigure(self, *_args, **_kwargs):
            pass

        def rowconfigure(self, *_args, **_kwargs):
            pass

        def grid(self, **_kwargs):
            pass

        def grid(self, **_kwargs):
            pass

        def grid(self, **_kwargs):
            pass

        def grid(self, **_kwargs):
            pass

    messages = []
    window.result_viewer_message = SimpleNamespace(set=messages.append)
    window.result_viewer_plot_frames = {
        "deformed": DummyFrame(),
        "axial": DummyFrame(),
        "shear": DummyFrame(),
        "moment": DummyFrame(),
    }
    window.result_viewer_plot_canvases = {}
    window.model_canvas = SimpleNamespace(builder=SimpleNamespace(model=SimpleNamespace(name="Viewer Model")))
    calls = []

    class DummyCanvas:
        def __init__(self, fig, master=None):
            calls.append(("canvas", master))
            self._widget = SimpleNamespace(grid=lambda **_kw: None)

        def get_tk_widget(self):
            return self._widget

        def draw(self):
            calls.append(("draw", None))

    monkeypatch.setattr(main_window, "FigureCanvasTkAgg", DummyCanvas)
    monkeypatch.setattr(main_window, "plot_static_deformed_shape", lambda model, results: calls.append(("deformed", model, results)) or (SimpleNamespace(), None))
    monkeypatch.setattr(
        main_window,
        "plot_static_nvm_diagram",
        lambda model, results, diagram_key, show_extrema=False: calls.append((diagram_key, show_extrema)) or (SimpleNamespace(), None),
    )

    window.latest_static_result = SimpleNamespace(
        displacements={1: [0.0, 0.0, 0.0]},
        nvm_data={"e1": {"x": [0.0, 1.5, 3.0], "N": [5.0, -8.0, 2.0], "V": [1.0, -3.0, 4.0], "M": [0.5, 2.5, -1.0]}},
    )
    window._refresh_static_viewer()

    assert messages[-1] == "Complete model viewer shows the stored Static result."
    assert ("deformed", window.model_canvas.builder.model, window.latest_static_result) in calls
    assert ("N", True) in calls
    assert ("V", True) in calls
    assert ("M", True) in calls
    assert window.result_viewer_plot_canvases


def test_desktop_final_scope_exposes_static_and_modal_only():
    analyze_actions = main_window.COMMAND_TABS[-2][1]
    result_actions = main_window.COMMAND_TABS[-1][1]

    assert analyze_actions == (("action", "Run Static Analysis"), ("action", "Run Modal Analysis"))
    assert result_actions == (("action", "Static Results"), ("action", "Modal Results"))
    exposed_labels = " ".join(label for _kind, label in analyze_actions + result_actions)
    assert "RSA" not in exposed_labels
    assert "THA" not in exposed_labels
    assert "Response Spectrum" not in exposed_labels
    assert "Time History" not in exposed_labels


def test_desktop_static_complete_model_viewer_empty_states(monkeypatch):
    window = _window_with_model()

    class DummyFrame:
        def winfo_children(self):
            return []

        def columnconfigure(self, *_args, **_kwargs):
            pass

        def rowconfigure(self, *_args, **_kwargs):
            pass

        def grid(self, **_kwargs):
            pass

    messages = []
    labels = []
    monkeypatch.setattr(main_window.ttk, "Label", lambda *args, **kwargs: SimpleNamespace(grid=lambda **_kw: labels.append(kwargs.get("text"))))
    monkeypatch.setattr(main_window, "FigureCanvasTkAgg", lambda fig, master=None: SimpleNamespace(get_tk_widget=lambda: SimpleNamespace(grid=lambda **_kw: None), draw=lambda: None))
    monkeypatch.setattr(main_window, "plot_static_deformed_shape", lambda model, results: (SimpleNamespace(), None))
    window.result_viewer_message = SimpleNamespace(set=messages.append)
    window.result_viewer_plot_frames = {
        "deformed": DummyFrame(),
        "axial": DummyFrame(),
        "shear": DummyFrame(),
        "moment": DummyFrame(),
    }
    window.result_viewer_plot_canvases = {}

    window._refresh_static_viewer()
    assert messages[-1] == "Run Static Analysis first."
    assert "Run Static Analysis first." in labels

    window.latest_static_result = SimpleNamespace(displacements={1: [0.0, 0.0, 0.0]}, nvm_data={})
    window._refresh_static_viewer()
    assert messages[-1] == "Complete model viewer shows the stored Static result."
    assert labels.count("No N/V/M data available.") >= 3


def test_desktop_member_review_viewer_renders_cursor_summary(monkeypatch):
    builder = ModelBuilder(name="Viewer Model")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")

    window = _window_with_model(model=builder.model)

    class DummyFrame:
        def __init__(self):
            self.configured = []

        def winfo_children(self):
            return []

        def columnconfigure(self, *_args, **_kwargs):
            pass

        def rowconfigure(self, *_args, **_kwargs):
            pass

        def grid(self, **_kwargs):
            pass

    class DummySelector:
        def __init__(self):
            self.values = []

        def configure(self, **kwargs):
            self.values = list(kwargs.get("values", []))

    class DummyScale:
        def __init__(self):
            self.configured = {}
            self.value = None
            self.command = None

        def configure(self, **kwargs):
            self.configured.update(kwargs)

        def set(self, value):
            self.value = value
            if self.command is not None:
                self.command(value)

    class DummyCanvas:
        instances = []

        def __init__(self, *args, **kwargs):
            self.operations = []
            self.bindings = {}
            DummyCanvas.instances.append(self)

        def grid(self, **_kwargs):
            pass

        def bind(self, event, callback):
            self.bindings[event] = callback

        def winfo_exists(self):
            return True

        def winfo_width(self):
            return 800

        def winfo_height(self):
            return 520

        def delete(self, *args):
            self.operations.append(("delete", args))

        def create_text(self, *args, **kwargs):
            self.operations.append(("text", args, kwargs))

        def create_line(self, *args, **kwargs):
            self.operations.append(("line", args, kwargs))

        def create_oval(self, *args, **kwargs):
            self.operations.append(("oval", args, kwargs))

        def create_polygon(self, *args, **kwargs):
            self.operations.append(("polygon", args, kwargs))

    monkeypatch.setattr(main_window.tk, "Canvas", DummyCanvas)
    profile_builds = []
    real_build_member_review_profile = main_window.build_member_review_profile

    def counted_build_member_review_profile(*args, **kwargs):
        profile_builds.append(args[2])
        return real_build_member_review_profile(*args, **kwargs)

    monkeypatch.setattr(main_window, "build_member_review_profile", counted_build_member_review_profile)

    window.latest_static_result = SimpleNamespace(
        load_case_id="LC1",
        displacements={1: [0.0, 0.0, 0.0], 2: [0.01, 0.02, 0.03]},
        element_forces={"e1": {"i": [1.0, 2.0, 3.0], "j": [4.0, 5.0, 6.0]}},
        member_end_forces={"e1": {"i": [-1.0, 2.0, -3.0], "j": [4.0, -5.0, 6.0]}},
        nvm_data={"e1": {"x": [0.0, 1.5, 3.0], "N": [5.0, -8.0, 2.0], "V": [1.0, -3.0, 4.0], "M": [0.5, 2.5, -1.0]}},
    )
    window.selected_member_id = "e1"
    window.result_viewer_member_var = DummyVar("e1")
    window.result_viewer_member_selector = DummySelector()
    window.result_viewer_member_message = DummyVar("Select a member to review static results.")
    window.result_viewer_member_display_mode_var = DummyVar("Absolute")
    window.result_viewer_member_scroll_var = DummyVar(True)
    window.result_viewer_member_show_max_var = DummyVar(True)
    window.result_viewer_member_cursor_var = DummyVar("1.5")
    window.result_viewer_member_cursor_scale = DummyScale()
    window.result_viewer_member_cursor_scale.command = window._on_member_review_cursor_changed
    window.result_viewer_member_plot_container = DummyFrame()
    window.result_viewer_member_plot_canvas = None
    window.result_viewer_member_current_location_var = DummyVar("-")
    window.result_viewer_member_current_n_var = DummyVar("-")
    window.result_viewer_member_current_v_var = DummyVar("-")
    window.result_viewer_member_current_m_var = DummyVar("-")
    window.result_viewer_member_current_disp_var = DummyVar("-")
    window.result_viewer_member_max_n_var = DummyVar("-")
    window.result_viewer_member_max_v_var = DummyVar("-")
    window.result_viewer_member_max_m_var = DummyVar("-")
    window.result_viewer_member_max_disp_var = DummyVar("-")

    window._refresh_individual_member_viewer()

    assert window.result_viewer_member_message.get() == "Member e1 selected for static review."
    assert window.result_viewer_member_selector.values == ["e1"]
    assert profile_builds == ["e1"]
    assert len(DummyCanvas.instances) == 1
    assert window.result_viewer_member_current_location_var.get() == "x = 1.5 / 3 m"
    assert window.result_viewer_member_current_n_var.get() == "-8 kN"
    assert window.result_viewer_member_max_n_var.get() == "x = 1.5, -8 kN"
    assert window.result_viewer_member_cursor_scale.configured["to"] == 3.0

    first_canvas = DummyCanvas.instances[0]
    line_styles = [operation[2] for operation in first_canvas.operations if operation[0] == "line"]
    polygon_styles = [operation[2] for operation in first_canvas.operations if operation[0] == "polygon"]
    text_labels = [operation[2].get("text") for operation in first_canvas.operations if operation[0] == "text"]
    assert any(style.get("fill") == "#2e7d32" for style in line_styles)
    assert any(style.get("fill") == "#c62828" for style in line_styles)
    assert any(style.get("fill") == "#2e7d32" for style in polygon_styles)
    assert any(style.get("fill") == "#c62828" for style in polygon_styles)
    assert any(style.get("arrow") == main_window.tk.LAST for style in line_styles)
    assert "FX=-1" in text_labels
    assert "FY=2" in text_labels
    assert "MZ=-3" in text_labels
    assert "FX=4" in text_labels
    assert "FY=-5" in text_labels
    assert "MZ=6" in text_labels
    redraw_deletes = [operation for operation in first_canvas.operations if operation == ("delete", ("all",))]
    window._on_member_review_cursor_changed("0.75")

    assert profile_builds == ["e1"]
    assert len(DummyCanvas.instances) == 1
    assert [operation for operation in first_canvas.operations if operation == ("delete", ("all",))] == redraw_deletes
    assert window.result_viewer_member_current_location_var.get() == "x = 0.75 / 3 m"
    assert window.result_viewer_member_current_n_var.get() == "-1.5 kN"


def test_desktop_member_review_viewer_empty_states(monkeypatch):
    window = _window_with_model()

    class DummyFrame:
        def winfo_children(self):
            return []

        def columnconfigure(self, *_args, **_kwargs):
            pass

        def rowconfigure(self, *_args, **_kwargs):
            pass

    messages = []
    labels = []
    monkeypatch.setattr(main_window.ttk, "Label", lambda *args, **kwargs: SimpleNamespace(grid=lambda **_kw: labels.append(kwargs.get("text"))))
    window.result_viewer_member_message = SimpleNamespace(set=messages.append)
    window.result_viewer_member_var = DummyVar("")
    window.result_viewer_member_selector = SimpleNamespace(configure=lambda **_kwargs: None)
    window.result_viewer_member_display_mode_var = DummyVar("Absolute")
    window.result_viewer_member_scroll_var = DummyVar(True)
    window.result_viewer_member_show_max_var = DummyVar(True)
    window.result_viewer_member_cursor_var = DummyVar("0")
    window.result_viewer_member_cursor_scale = SimpleNamespace(configure=lambda **_kwargs: None)
    window.result_viewer_member_plot_container = DummyFrame()
    window.result_viewer_member_current_location_var = DummyVar("-")
    window.result_viewer_member_current_n_var = DummyVar("-")
    window.result_viewer_member_current_v_var = DummyVar("-")
    window.result_viewer_member_current_m_var = DummyVar("-")
    window.result_viewer_member_current_disp_var = DummyVar("-")
    window.result_viewer_member_max_n_var = DummyVar("-")
    window.result_viewer_member_max_v_var = DummyVar("-")
    window.result_viewer_member_max_m_var = DummyVar("-")
    window.result_viewer_member_max_disp_var = DummyVar("-")

    window._refresh_individual_member_viewer()
    assert messages[-1] == "Run Static Analysis first."
    assert "Run Static Analysis first." in labels
    assert window.result_viewer_member_current_location_var.get() == "-"

    window.latest_static_result = SimpleNamespace(element_forces={}, nvm_data={})
    window._refresh_individual_member_viewer()
    assert messages[-1] == "Select a valid member."
    assert "Select a valid member." in labels


def test_member_review_profile_and_panel_labels():
    builder = ModelBuilder(name="Viewer Model")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    results = SimpleNamespace(
        load_case_id="LC1",
        displacements={1: [0.0, 0.0, 0.0], 2: [0.01, 0.02, 0.03]},
        element_forces={"e1": {"i": [1.0, 2.0, 3.0], "j": [4.0, 5.0, 6.0]}},
        member_end_forces={"e1": {"i": [-1.0, 2.0, -3.0], "j": [4.0, -5.0, 6.0]}},
        nvm_data={"e1": {"x": [0.0, 1.5, 3.0], "N": [5.0, -8.0, 2.0], "V": [1.0, -3.0, 4.0], "M": [0.5, 2.5, -1.0]}},
    )

    profile = build_member_review_profile(builder.model, results, "e1")
    assert profile is not None
    assert profile["member_id"] == "e1"
    assert profile["end_forces"]["Ni"] == 5.0
    assert profile["end_forces"]["Vi"] == 1.0
    assert profile["end_forces"]["Mj"] == -1.0
    assert profile["member_end_forces"]["FXi"] == -1.0
    assert profile["member_end_forces"]["FYi"] == 2.0
    assert profile["member_end_forces"]["MZj"] == 6.0

    fig, axes, state = plot_member_review_panel(profile, 1.5, show_max=True)
    assert state["current"]["N"] == -8.0
    assert any(text.get_text() for text in axes[1].texts)
    assert any(text.get_text() for text in axes[4].texts)
    plt.close(fig)

    empty_results = SimpleNamespace(
        load_case_id="LC1",
        displacements={1: [0.0, 0.0, 0.0], 2: [0.01, 0.02, 0.03]},
        element_forces={"e1": {"i": [1.0, 2.0, 3.0], "j": [4.0, 5.0, 6.0]}},
        nvm_data={},
    )
    empty_profile = build_member_review_profile(builder.model, empty_results, "e1")
    fig2, axes2, _ = plot_member_review_panel(empty_profile, 0.0, show_max=True)
    empty_texts = list(axes2[1].texts) + list(axes2[2].texts) + list(axes2[3].texts)
    assert any("No N/V/M data available." in text.get_text() for text in empty_texts)
    plt.close(fig2)


def test_desktop_static_nvm_diagrams_label_extrema():
    builder = ModelBuilder(name="Viewer Model")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    results = SimpleNamespace(
        load_case_id="LC1",
        nvm_data={
            "e1": {
                "x": [0.0, 1.5, 3.0],
                "N": [5.0, -8.0, 2.0],
                "V": [1.0, -3.0, 4.0],
                "M": [0.5, 2.5, -1.0],
            }
        },
    )

    fig, axes = plot_static_nvm_diagrams(builder.model, results, show_extrema=True)

    labels_n = [text.get_text() for text in axes[0].texts if text.get_text()]
    labels_m = [text.get_text() for text in axes[2].texts if text.get_text()]
    assert labels_n
    assert labels_m
    plt.close(fig)


def test_desktop_open_xml_replaces_builder_refreshes_ui_and_clears_results(tmp_path, monkeypatch):
    builder = ModelBuilder(name="Imported Desktop Model")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0, is_hinged=True)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    xml_path = tmp_path / "desktop_import.xml"
    builder.export_xml(xml_path)

    window = _window_with_model()
    window.root = object()
    window.selected_command = SimpleNamespace(get=lambda: "Assign Load")
    events = []
    window.model_canvas = SimpleNamespace(
        builder=SimpleNamespace(model=SimpleNamespace(name="Old Model")),
        load_builder=lambda loaded_builder: events.append(("load_builder", loaded_builder.model.name)) or setattr(window.model_canvas, "builder", loaded_builder),
        restore_full_view=lambda notify=False: events.append(("restore_full_view", notify)),
    )
    window.object_tree = SimpleNamespace(select_objects=lambda selection: events.append(("tree_select", selection)))
    window.property_panel = SimpleNamespace(
        show_selection=lambda kind, obj: events.append(("panel_selection", kind, obj)),
        sync_from_canvas=lambda: events.append(("sync_from_canvas", None)),
        show_command=lambda command: events.append(("show_command", command)),
    )
    window._refresh_object_tree = lambda: events.append(("refresh_object_tree", None))
    monkeypatch.setattr(main_window.filedialog, "askopenfilename", lambda **_kwargs: str(xml_path))
    errors = []
    monkeypatch.setattr(main_window.messagebox, "showerror", lambda *args, **kwargs: errors.append((args, kwargs)))

    window.latest_static_result = object()
    window.latest_static_results = object()
    window.static_analysis_error = "old error"
    window.latest_modal_results = object()
    window.modal_analysis_error = "old modal error"
    window.result_view_category = "Nodal Displacements"
    window.result_view_tree = object()

    window._toolbar_action("Open XML")

    assert window.model_canvas.builder.model.name == "Imported Desktop Model"
    assert window.latest_static_results is None
    assert window.static_analysis_error is None
    assert window.latest_modal_results is None
    assert window.modal_analysis_error is None
    assert window._analysis_results_cleared is True
    assert ("refresh_object_tree", None) in events
    assert ("tree_select", None) in events
    assert ("panel_selection", None, None) in events
    assert ("sync_from_canvas", None) in events
    assert ("show_command", "Assign Load") in events
    assert ("restore_full_view", False) in events
    assert errors == []
    assert window.messages[-1] == f"Opened XML: {xml_path}"


def test_desktop_model_change_clears_stale_results_and_refreshes_open_viewer():
    window = _window_with_model(model=SimpleNamespace(name="Current Model"))
    window.latest_static_result = object()
    window.latest_static_results = object()
    window.latest_modal_result = object()
    window.latest_modal_results = object()
    window.result_viewer_window = SimpleNamespace(winfo_exists=lambda: True)
    refreshed = []
    window._refresh_results_viewer = lambda: refreshed.append("refreshed")

    window._on_model_changed()

    assert window.latest_static_result is None
    assert window.latest_modal_result is None
    assert window._analysis_results_cleared is True
    assert refreshed == ["refreshed"]


def test_desktop_static_table_export_writes_csv(tmp_path, monkeypatch):
    window = _window_with_model()
    window.result_view_category = DummyVar("Nodal Displacements")
    window.latest_static_result = SimpleNamespace(displacements={1: [0.001, 0.0, 0.0]})
    window.result_viewer_mode = "static"
    output = tmp_path / "static_results.csv"
    monkeypatch.setattr(main_window.filedialog, "asksaveasfilename", lambda **_kwargs: str(output))

    window._export_current_results_table_csv()

    assert output.read_text().splitlines()[0] == "Node,UX [m],UY [m],RZ [rad]"


def test_desktop_open_xml_reports_failure_and_keeps_current_model(monkeypatch):
    window = _window_with_model(model=SimpleNamespace(name="Current Model"))
    window.root = object()
    window.selected_command = SimpleNamespace(get=lambda: "Select / Inspect")
    window.property_panel = SimpleNamespace(show_selection=lambda kind, obj: None, sync_from_canvas=lambda: None, show_command=lambda command: None)
    window.object_tree = SimpleNamespace(select_objects=lambda selection: None)
    monkeypatch.setattr(main_window.filedialog, "askopenfilename", lambda **_kwargs: str(Path("broken.xml")))
    monkeypatch.setattr(main_window, "XMLParser", lambda _path: SimpleNamespace(parse=lambda: (_ for _ in ()).throw(ValueError("bad xml"))))
    errors = []
    monkeypatch.setattr(main_window.messagebox, "showerror", lambda *args, **kwargs: errors.append((args, kwargs)))

    window._toolbar_action("Open XML")

    assert window.model_canvas.builder.model.name == "Current Model"
    assert window.messages[-1] == "Open XML failed: bad xml"
    assert len(errors) == 1


def test_desktop_validate_model_reports_success_without_dialog(monkeypatch):
    window = _window_with_model(model=SimpleNamespace(name="Current Model"))
    window.root = object()
    errors = []
    monkeypatch.setattr(main_window.messagebox, "showerror", lambda *args, **kwargs: errors.append((args, kwargs)))
    validator_calls = []
    monkeypatch.setattr(
        main_window,
        "StructuralValidator",
        lambda model: SimpleNamespace(validate=lambda: validator_calls.append(model)),
    )

    window._toolbar_action("Validate")

    assert validator_calls == [window.model_canvas.builder.model]
    assert window.messages[-1] == "Model validation passed."
    assert errors == []


def test_desktop_validate_model_reports_validator_failure(monkeypatch):
    window = _window_with_model(model=SimpleNamespace(name="Current Model"))
    window.root = object()
    errors = []
    monkeypatch.setattr(main_window.messagebox, "showerror", lambda *args, **kwargs: errors.append((args, kwargs)))
    monkeypatch.setattr(
        main_window,
        "StructuralValidator",
        lambda model: SimpleNamespace(
            validate=lambda: (_ for _ in ()).throw(main_window.UnstableStructureError("No boundary conditions defined. Structure is entirely unsupported."))
        ),
    )

    window._toolbar_action("Validate")

    assert window.messages[-1] == "No boundary conditions defined. Structure is entirely unsupported."
    assert len(errors) == 1
