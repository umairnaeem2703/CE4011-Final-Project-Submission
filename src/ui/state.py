"""Session-state defaults for the Streamlit UI."""

from __future__ import annotations

from collections.abc import MutableMapping
from copy import deepcopy


NAVIGATION_SECTIONS = (
    "Model Input",
    "Static Analysis",
    "Dynamic Analysis",
    "Results",
    "Visualization",
)

SESSION_DEFAULTS = {
    "model": None,
    "model_input_error": None,
    "static_analysis_error": None,
    "static_results": None,
    "modal_results": None,
    "rsa_results": None,
    "tha_results": None,
    "model_is_dirty": True,
    "ui_current_section": NAVIGATION_SECTIONS[0],
}


def initialize_session_state(session_state: MutableMapping[str, object]) -> MutableMapping[str, object]:
    """Populate missing UI session keys while preserving existing values."""
    for key, value in SESSION_DEFAULTS.items():
        session_state.setdefault(key, deepcopy(value))
    return session_state
