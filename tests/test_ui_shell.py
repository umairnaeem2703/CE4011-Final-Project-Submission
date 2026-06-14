import importlib
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ui.state import NAVIGATION_SECTIONS, initialize_session_state


class FakeStreamlit:
    def __init__(self, session_state=None, selectbox_values=None):
        self.session_state = session_state or {}
        self.selectbox_values = list(selectbox_values or [])
        self.messages = []
        self.text_inputs = []

    def info(self, message):
        self.messages.append(("info", message))

    def error(self, message):
        self.messages.append(("error", message))

    def selectbox(self, *args, **kwargs):
        return self.selectbox_values.pop(0)

    def number_input(self, *args, **kwargs):
        return kwargs.get("value")

    def text_area(self, *args, **kwargs):
        return ""

    def text_input(self, *args, **kwargs):
        self.text_inputs.append(kwargs)
        return kwargs.get("value", "")

    def button(self, *args, **kwargs):
        return False


def test_ui_state_defaults():
    state = initialize_session_state({})

    assert state["model"] is None
    assert state["model_is_dirty"] is True
    assert state["ui_current_section"] == "Model Input"


def test_ui_navigation_sections_exist():
    assert NAVIGATION_SECTIONS == (
        "Model Input",
        "Static Analysis",
        "Dynamic Analysis",
        "Results",
        "Visualization",
    )


def test_ui_app_imports_without_running_streamlit_server():
    app = importlib.import_module("ui.app")

    assert callable(app.main)
    assert callable(app.render_shell)


def test_ui_app_direct_file_import_does_not_load_ground_motion():
    src_root = Path(__file__).resolve().parents[1] / "src"
    app_path = src_root / "ui" / "app.py"
    old_path = sys.path[:]
    for module_name in ("ground_motion", "dynamic_analysis", "ui.app", "app_direct_test"):
        sys.modules.pop(module_name, None)

    try:
        sys.path = [path for path in sys.path if os.path.abspath(path) != str(src_root)]
        sys.path.insert(0, str(app_path.parent))
        spec = importlib.util.spec_from_file_location("app_direct_test", app_path)
        app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app)
    finally:
        sys.path = old_path

    assert callable(app.render_shell)
    assert "ground_motion" not in sys.modules


def test_static_modal_rsa_pages_load_without_ground_motion():
    sys.modules.pop("ground_motion", None)
    app = importlib.import_module("ui.app")

    app.render_static_analysis(FakeStreamlit())
    app.render_dynamic_analysis(FakeStreamlit({"model": object()}, ["Modal", "lumped"]))
    app.render_dynamic_analysis(FakeStreamlit({"model": object()}, ["Response Spectrum", "lumped", "SRSS"]))

    assert "ground_motion" not in sys.modules


def test_tha_page_offers_default_ground_motion_without_importing_reader():
    sys.modules.pop("ground_motion", None)
    app = importlib.import_module("ui.app")
    st = FakeStreamlit({"model": object()}, ["Time History", "lumped", "time_acceleration", "m/s2", "x"])

    app.render_dynamic_analysis(st)

    assert st.text_inputs[0]["value"].endswith(os.path.join("data", "ground_motion.txt"))
    assert "ground_motion" not in sys.modules
