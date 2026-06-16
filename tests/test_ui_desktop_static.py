import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ui_desktop import main_window
from ui_desktop.result_formatting import format_matrix, format_scalar


def _window_with_model(model=object()):
    window = main_window.MainWindow.__new__(main_window.MainWindow)
    window.model_canvas = SimpleNamespace(builder=SimpleNamespace(model=model))
    window.messages = []
    window._write_status = window.messages.append
    window.latest_static_results = None
    window.static_analysis_error = None
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
