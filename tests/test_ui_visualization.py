import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ui.visualization_display import render_dynamic_visualizations, render_static_visualizations


class FakeStreamlit:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def recorder(*args, **kwargs):
            self.calls.append((name, args, kwargs))

        return recorder


def test_visualization_adapter_handles_missing_results():
    st = FakeStreamlit()

    render_static_visualizations(st, model=object(), results=None)
    render_dynamic_visualizations(st, model=object(), modal_results=None, rsa_results=None, tha_results=None)

    messages = [args[0] for name, args, _ in st.calls if name == "info"]
    assert messages == [
        "Run static analysis to display visualizations.",
        "Run dynamic analysis to display visualizations.",
    ]
