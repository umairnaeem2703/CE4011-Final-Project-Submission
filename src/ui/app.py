"""Streamlit UI shell for the CE 4011 structural analysis app."""

from __future__ import annotations

try:
    from ground_motion import GroundMotionConfig

    from .dynamic_analysis import (
        run_modal_analysis_into_state,
        run_response_spectrum_analysis_into_state,
        run_time_history_analysis_into_state,
    )
    from .model_input import build_model_from_tables, build_model_from_xml_upload, mark_model_dirty, store_model_in_state
    from .state import NAVIGATION_SECTIONS, initialize_session_state
    from .static_analysis import load_case_ids, run_static_analysis_into_state
except ImportError:  # pragma: no cover - supports direct `streamlit run src/ui/app.py`
    from ground_motion import GroundMotionConfig

    from dynamic_analysis import (
        run_modal_analysis_into_state,
        run_response_spectrum_analysis_into_state,
        run_time_history_analysis_into_state,
    )
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
    elif selected_section == "Dynamic Analysis":
        render_dynamic_analysis(st_module)
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


def render_dynamic_analysis(st_module) -> None:
    """Render modal, RSA, and THA controls with cached result summaries."""
    if st_module.session_state.get("model") is None:
        st_module.info("Build or load a model before running dynamic analysis.")
        return

    analysis_type = st_module.selectbox(
        "Analysis type",
        ("Modal", "Response Spectrum", "Time History"),
        key="dynamic_analysis_type",
    )
    mass_matrix_type = st_module.selectbox("Mass matrix", ("lumped", "consistent"), key="dynamic_mass_matrix_type")
    damping_ratio = st_module.number_input(
        "Damping ratio",
        min_value=0.0,
        max_value=0.99,
        value=0.05,
        step=0.01,
        key="dynamic_damping_ratio",
    )

    if analysis_type == "Modal":
        num_modes = st_module.number_input("Modes", min_value=1, value=3, step=1, key="modal_num_modes")
        if st_module.button("Run Modal Analysis"):
            result = run_modal_analysis_into_state(st_module.session_state, int(num_modes), mass_matrix_type)
            _show_dynamic_run_message(st_module, result, "Modal analysis complete.")
        _render_modal_summary(st_module)
    elif analysis_type == "Response Spectrum":
        spectrum_text = st_module.text_area("Spectrum periods, accelerations", key="rsa_spectrum_csv")
        combination_method = st_module.selectbox("Combination", ("SRSS", "CQC"), key="rsa_combination_method")
        if st_module.button("Run Response Spectrum"):
            periods, accelerations, parse_error = _parse_spectrum_text(spectrum_text)
            if parse_error:
                st_module.session_state["rsa_results"] = None
                st_module.session_state["rsa_analysis_error"] = parse_error
                st_module.error(parse_error)
            else:
                result = run_response_spectrum_analysis_into_state(
                    st_module.session_state,
                    periods,
                    accelerations,
                    combination_method,
                    damping_ratio,
                )
                _show_dynamic_run_message(st_module, result, "Response spectrum analysis complete.")
        _render_rsa_summary(st_module)
    else:
        ground_motion_path = st_module.text_input("Ground motion file", key="tha_ground_motion_path")
        input_format = st_module.selectbox("Ground motion format", ("time_acceleration", "acceleration_only"), key="tha_input_format")
        time_step = st_module.number_input("Time step", min_value=0.0, value=0.01, step=0.01, key="tha_time_step")
        acceleration_unit = st_module.selectbox("Acceleration unit", ("m/s2", "cm/s2", "mm/s2", "g"), key="tha_acceleration_unit")
        scale_factor = st_module.number_input("Scale factor", value=1.0, step=0.1, key="tha_scale_factor")
        direction = st_module.selectbox("Direction", ("x", "y"), key="tha_excitation_direction")
        if st_module.button("Run Time History"):
            config = None
            if ground_motion_path:
                config = GroundMotionConfig(
                    file_path=ground_motion_path,
                    input_format=input_format,
                    time_step_dt=time_step if input_format == "acceleration_only" else None,
                    acceleration_column=0 if input_format == "acceleration_only" else 1,
                    acceleration_unit=acceleration_unit,
                    scale_factor=scale_factor,
                    excitation_direction=direction,
                )
            result = run_time_history_analysis_into_state(st_module.session_state, config, damping_ratio, mass_matrix_type)
            _show_dynamic_run_message(st_module, result, "Time history analysis complete.")
        _render_tha_summary(st_module)


def _show_dynamic_run_message(st_module, result, success_message: str) -> None:
    if result.ok:
        st_module.success(success_message)
    else:
        st_module.error(result.error)


def _render_modal_summary(st_module) -> None:
    error = st_module.session_state.get("modal_analysis_error")
    if error:
        st_module.error(error)
        return
    results = st_module.session_state.get("modal_results")
    if results is not None:
        st_module.subheader("Modal Results")
        st_module.write({"modes": results.num_modes_extracted, "periods": results.periods})


def _render_rsa_summary(st_module) -> None:
    error = st_module.session_state.get("rsa_analysis_error")
    if error:
        st_module.error(error)
        return
    results = st_module.session_state.get("rsa_results")
    if results is not None:
        st_module.subheader("Response Spectrum Results")
        st_module.write({"method": results.combination_method, "base_shear": results.combined_base_shear})


def _render_tha_summary(st_module) -> None:
    error = st_module.session_state.get("tha_analysis_error")
    if error:
        st_module.error(error)
        return
    results = st_module.session_state.get("tha_results")
    if results is not None:
        st_module.subheader("Time History Results")
        st_module.write({"steps": results.num_steps, "peak_base_shear": results.peak_base_shear})


def _parse_spectrum_text(text: str) -> tuple[list[float], list[float], str | None]:
    periods = []
    accelerations = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = [part for part in stripped.replace(",", " ").split() if part]
        if len(parts) != 2:
            return [], [], "Enter response spectrum rows as period, acceleration pairs."
        try:
            periods.append(float(parts[0]))
            accelerations.append(float(parts[1]))
        except ValueError:
            return [], [], "Response spectrum values must be numeric."
    if not periods:
        return [], [], "Provide a response spectrum before running RSA."
    return periods, accelerations, None


def main() -> None:
    """Run the Streamlit app."""
    import streamlit as st

    render_shell(st)


if __name__ == "__main__":
    main()
