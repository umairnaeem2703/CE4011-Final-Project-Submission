import os
import sys
from types import SimpleNamespace
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from model_builder import ModelBuilder
from ui_desktop import main_window
from ui_desktop.result_formatting import format_matrix, format_scalar


def _window_with_model(model=object()):
    window = main_window.MainWindow.__new__(main_window.MainWindow)
    window.model_canvas = SimpleNamespace(builder=SimpleNamespace(model=model))
    window.messages = []
    window._write_status = window.messages.append
    window.latest_static_results = None
    window.static_analysis_error = None
    window.result_view_category = None
    window.result_view_tree = None
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


def test_desktop_static_plot_rendering_handles_missing_result_and_invalid_member(monkeypatch):
    window = _window_with_model()
    messages = []
    window._set_plot_message = messages.append
    monkeypatch.setattr(main_window.ttk, "Label", lambda *args, **kwargs: SimpleNamespace(grid=lambda **_kw: None))

    class DummyContainer:
        def __init__(self):
            self.children = []

        def winfo_children(self):
            return self.children

        def columnconfigure(self, *_args, **_kwargs):
            pass

        def rowconfigure(self, *_args, **_kwargs):
            pass

    container = DummyContainer()
    window.result_plot_deformed_container = container
    window.result_plot_nvm_container = container

    window._render_static_deformed_plot()
    window._render_static_nvm_plot()

    assert messages[0] == "Run Static Analysis first."

    window.latest_static_results = SimpleNamespace(displacements={1: [0.0, 0.0, 0.0]}, nvm_data={})
    window.result_plot_member_var = SimpleNamespace(get=lambda: "All members")
    window._render_static_nvm_plot()
    assert messages[-1] == "No N/V/M data available for diagrams."

    window.latest_static_results = SimpleNamespace(displacements={1: [0.0, 0.0, 0.0]}, nvm_data={"e1": {"N": [], "V": [], "M": []}})
    window.result_plot_member_var = SimpleNamespace(get=lambda: "missing-member")
    window._resolve_nvm_member_key = lambda member_id, nvm_data: None
    window._render_static_nvm_plot()
    assert messages[-1] == "Selected member is invalid for N/V/M diagrams."


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
