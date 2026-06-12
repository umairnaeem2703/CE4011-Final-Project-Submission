"""Streamlit UI shell for the CE 4011 structural analysis app."""

from __future__ import annotations

try:
    from .model_input import build_model_from_tables, build_model_from_xml_upload, mark_model_dirty, store_model_in_state
    from .state import NAVIGATION_SECTIONS, initialize_session_state
    from .static_analysis import load_case_ids, run_static_analysis_into_state
except ImportError:  # pragma: no cover - supports direct `streamlit run src/ui/app.py`
    from model_input import build_model_from_tables, build_model_from_xml_upload, mark_model_dirty, store_model_in_state
    from state import NAVIGATION_SECTIONS, initialize_session_state
    from static_analysis import load_case_ids, run_static_analysis_into_state


def render_shell(st_module) -> None:
    """Render the navigation shell without performing analysis work."""
    initialize_session_state(st_module.session_state)

    st_module.set_page_config(
        page_title="CE 4011 Structural Analysis",
        layout="wide",
    )
    st_module.title("CE 4011 Structural Analysis")

    selected_section = st_module.sidebar.radio(
        "Navigation",
        NAVIGATION_SECTIONS,
        key="ui_current_section",
    )

    st_module.header(selected_section)
    if selected_section == "Model Input":
        render_model_input(st_module)
    elif selected_section == "Static Analysis":
        render_static_analysis(st_module)
    else:
        st_module.info("Select or build a model before running analysis.")


def render_model_input(st_module) -> None:
    """Render XML upload and spreadsheet-style table inputs."""
    uploaded_xml = st_module.file_uploader("XML model", type=["xml"], key="model_xml_upload")
    if uploaded_xml is not None and st_module.button("Build from XML"):
        result = build_model_from_xml_upload(uploaded_xml)
        if result.ok:
            store_model_in_state(st_module.session_state, result.model)
            st_module.session_state["model_input_error"] = None
            st_module.success(f"Loaded {result.model.name}")
        else:
            st_module.session_state["model_input_error"] = result.error
            st_module.error(result.error)

    st_module.subheader("Table Input")
    st_module.caption("Paste CSV text with headers for each model table.")
    nodes = st_module.text_area("Nodes", key="model_nodes_csv", on_change=mark_model_dirty, args=(st_module.session_state,))
    elements = st_module.text_area("Elements", key="model_elements_csv", on_change=mark_model_dirty, args=(st_module.session_state,))
    materials = st_module.text_area("Materials", key="model_materials_csv", on_change=mark_model_dirty, args=(st_module.session_state,))
    sections = st_module.text_area("Sections", key="model_sections_csv", on_change=mark_model_dirty, args=(st_module.session_state,))
    supports = st_module.text_area("Supports", key="model_supports_csv", on_change=mark_model_dirty, args=(st_module.session_state,))
    loads = st_module.text_area("Loads", key="model_loads_csv", on_change=mark_model_dirty, args=(st_module.session_state,))
    masses = st_module.text_area("Masses", key="model_masses_csv", on_change=mark_model_dirty, args=(st_module.session_state,))

    if st_module.button("Build from Tables"):
        result = build_model_from_tables(
            nodes=nodes,
            elements=elements,
            materials=materials,
            sections=sections,
            supports=supports,
            loads=loads,
            masses=masses,
        )
        if result.ok:
            store_model_in_state(st_module.session_state, result.model)
            st_module.session_state["model_input_error"] = None
            st_module.success(f"Built {result.model.name}")
        else:
            st_module.session_state["model_input_error"] = result.error
            st_module.error(result.error)


def render_static_analysis(st_module) -> None:
    """Render static-analysis controls and cached result summary."""
    model = st_module.session_state.get("model")
    cases = load_case_ids(model)
    if model is None:
        st_module.info("Build or load a model before running static analysis.")
        return
    if not cases:
        st_module.error("Add at least one load case before running static analysis.")
        return

    selected_load_case = st_module.selectbox("Load case", cases, key="static_load_case_id")
    if st_module.button("Run Static Analysis"):
        result = run_static_analysis_into_state(st_module.session_state, selected_load_case)
        if result.ok:
            st_module.success(f"Static analysis complete for {result.results.load_case_id}.")
        else:
            st_module.error(result.error)

    error = st_module.session_state.get("static_analysis_error")
    if error:
        st_module.error(error)
        return

    results = st_module.session_state.get("static_results")
    if results is not None:
        st_module.subheader("Static Results")
        st_module.caption(f"Load case: {results.load_case_id}")
        st_module.write(
            {
                "nodes": len(results.displacements),
                "reactions": len(results.reactions),
                "elements": len(results.element_forces),
            }
        )


def main() -> None:
    """Run the Streamlit app."""
    import streamlit as st

    render_shell(st)


if __name__ == "__main__":
    main()
