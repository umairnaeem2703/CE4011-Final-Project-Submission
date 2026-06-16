import os
import sys
from types import SimpleNamespace
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from model_builder import ModelBuilder
from ui_desktop import main_window
from ui_desktop.result_formatting import format_matrix, format_scalar
from visualizer import build_member_review_profile, plot_member_review_panel, plot_static_nvm_diagrams


class DummyVar:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def _window_with_model(model=object()):
    window = main_window.MainWindow.__new__(main_window.MainWindow)
    window.model_canvas = SimpleNamespace(builder=SimpleNamespace(model=model))
    window.messages = []
    window._write_status = window.messages.append
    window.latest_static_results = None
    window.static_analysis_error = None
    window.result_view_category = None
    window.result_view_tree = None
    window.result_viewer_notebook = None
    window.result_viewer_table_tab = None
    window.result_viewer_shell_tab = None
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
    return window


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
    window.latest_static_results = object()

    window._toolbar_action("Run Static Analysis")

    assert window.latest_static_results is None
    assert window.static_analysis_error == "Static analysis failed: unstable"
    assert window.messages[-1] == "Static analysis failed: unstable"


def test_desktop_static_result_tables_use_cached_result_fields():
    results = SimpleNamespace(
        displacements={1: [0.001, 0.0, 0.0]},
        reactions={1: [10.0, -2.5, 1.0e-12]},
        element_forces={"e1": {"i": [[10.0], [0.0], [0.0]], "j": [[-10.0], [0.0], [0.0]]}},
        dof_map={1: [-1, 0, 3]},
        K=[[1.0, 0.0], [0.0, 1.0]],
        Kff=[[1.0]],
        F=[10.0, 0.0],
        Ff=[10.0],
    )
    window = _window_with_model()
    window.latest_static_results = results

    columns, rows = window._static_result_table_data("Nodal Displacements")
    assert columns == ("Node", "UX [m]", "UY [m]", "RZ [rad]")
    assert rows == [("1", "0.001", "0", "0")]

    columns, rows = window._static_result_table_data("Support Reactions")
    assert columns == ("Node", "FX [kN]", "FY [kN]", "MZ [kN-m]")
    assert rows == [("1", "10", "-2.5", "0")]

    columns, rows = window._static_result_table_data("Member End Forces")
    assert columns == ("Element", "End", "N [kN]", "V [kN]", "M [kN-m]")
    assert ("e1", "i", "10", "0", "0") in rows

    columns, rows = window._static_result_table_data("DOF Map")
    assert columns == ("Node", "UX", "UY", "RZ")
    assert rows == [("1", "Fixed", "Eq 0", "Eq 3")]

    columns, rows = window._static_result_table_data("Global Stiffness Matrix K")
    assert columns == ("Row", "C0", "C1")
    assert rows == [("R0", "1", "0"), ("R1", "0", "1")]


def test_desktop_result_formatting_handles_near_zero_and_missing_intermediate_data():
    assert format_scalar(1.0e-12, tolerance=0.001) == "0"
    assert format_scalar(1.23456, tolerance=0.001) == "1.235"
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
    window.latest_static_results = results

    columns, rows = window._static_result_table_data("Reduced Force Vector Ff")
    assert columns == ("Message",)
    assert rows == [("Reduced force vector Ff is unavailable.",)]


def test_desktop_dof_map_uses_cached_model_mapping_when_result_field_missing():
    model = SimpleNamespace(unit_system="kN_m_tonne", cached_dof_map={2: [-1, 4, -1]})
    window = _window_with_model(model=model)
    window.latest_static_results = SimpleNamespace(
        displacements={},
        reactions={},
        element_forces={},
        dof_map=None,
        K=None,
        Kff=None,
        F=None,
        Ff=None,
    )

    columns, rows = window._static_result_table_data("DOF Map")

    assert columns == ("Node", "UX", "UY", "RZ")
    assert rows == [("2", "Fixed", "Eq 4", "Fixed")]


def test_desktop_member_force_rows_unwrap_nested_scalar_lists():
    model = SimpleNamespace(unit_system="kN_m_tonne")
    window = _window_with_model(model=model)

    columns, rows = window._member_force_rows({"e2": [[3.2], [0.0004], [-1.2], [-3.2], [0.0], [1.2]]}, {"force": "kN", "moment": "kN-m"})

    assert columns == ("Element", "End", "N [kN]", "V [kN]", "M [kN-m]")
    assert ("e2", "i", "3.2", "0", "-1.2") in rows
    assert ("e2", "j", "-3.2", "0", "1.2") in rows


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
    window._create_static_results_window = lambda: object()
    window._refresh_static_result_table = lambda: refreshes.append("table")
    window._refresh_static_viewer = lambda: refreshes.append("viewer")

    window._toolbar_action("Results")

    assert refreshes == ["table", "viewer"]
    assert selected_tabs == []
    assert window.messages[-1] == "Run Static Analysis first."


def test_desktop_results_workflow_initializes_individual_member_tab(monkeypatch):
    builder = ModelBuilder(name="Viewer Model")
    builder.add_material("m1", E=200000.0)
    builder.add_section("s1", A=0.02, I=0.0001)
    builder.add_node(1, 0.0, 0.0)
    builder.add_node(2, 3.0, 0.0)
    builder.add_element("e1", "frame", 1, 2, "m1", "s1")
    window = _window_with_model(model=builder.model)
    window.latest_static_results = SimpleNamespace(
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

    def fake_create_results_window():
        window.result_viewer_notebook = SimpleNamespace(select=lambda tab: selected_tabs.append(tab))
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
        return object()

    window._create_static_results_window = fake_create_results_window
    window._refresh_static_result_table = lambda: None
    window._refresh_static_viewer = lambda: None

    window._toolbar_action("Results")

    assert selected_tabs == [table_tab]
    assert window.result_viewer_member_message.get() == "Member e1 selected for static review."
    assert window.messages[-1] == "Static results opened."


def test_desktop_static_complete_model_viewer_renders_plots(monkeypatch):
    assert main_window.COMMAND_TABS[-1][1] == (("action", "Results"),)
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

    window.latest_static_results = SimpleNamespace(
        displacements={1: [0.0, 0.0, 0.0]},
        nvm_data={"e1": {"x": [0.0, 1.5, 3.0], "N": [5.0, -8.0, 2.0], "V": [1.0, -3.0, 4.0], "M": [0.5, 2.5, -1.0]}},
    )
    window._refresh_static_viewer()

    assert messages[-1] == "Complete model viewer shows the stored Static result."
    assert ("deformed", window.model_canvas.builder.model, window.latest_static_results) in calls
    assert ("N", True) in calls
    assert ("V", True) in calls
    assert ("M", True) in calls
    assert window.result_viewer_plot_canvases


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

    window.latest_static_results = SimpleNamespace(displacements={1: [0.0, 0.0, 0.0]}, nvm_data={})
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

    window.latest_static_results = SimpleNamespace(
        load_case_id="LC1",
        displacements={1: [0.0, 0.0, 0.0], 2: [0.01, 0.02, 0.03]},
        element_forces={"e1": {"i": [1.0, 2.0, 3.0], "j": [4.0, 5.0, 6.0]}},
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
    assert any(label and label.startswith("N=") for label in text_labels)
    assert any(label and label.startswith("V=") for label in text_labels)
    assert any(label and label.startswith("M=") for label in text_labels)
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

    window.latest_static_results = SimpleNamespace(element_forces={}, nvm_data={})
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
        nvm_data={"e1": {"x": [0.0, 1.5, 3.0], "N": [5.0, -8.0, 2.0], "V": [1.0, -3.0, 4.0], "M": [0.5, 2.5, -1.0]}},
    )

    profile = build_member_review_profile(builder.model, results, "e1")
    assert profile is not None
    assert profile["member_id"] == "e1"
    assert profile["end_forces"]["Ni"] == 1.0

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

    window.latest_static_results = object()
    window.static_analysis_error = "old error"
    window.result_view_category = "Nodal Displacements"
    window.result_view_tree = object()

    window._toolbar_action("Open XML")

    assert window.model_canvas.builder.model.name == "Imported Desktop Model"
    assert window.latest_static_results is None
    assert window.static_analysis_error is None
    assert window.result_view_category is None
    assert window.result_view_tree is None
    assert ("refresh_object_tree", None) in events
    assert ("tree_select", None) in events
    assert ("panel_selection", None, None) in events
    assert ("sync_from_canvas", None) in events
    assert ("show_command", "Assign Load") in events
    assert ("restore_full_view", False) in events
    assert errors == []
    assert window.messages[-1] == f"Opened XML: {xml_path}"


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
