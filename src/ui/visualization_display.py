"""Streamlit adapters around the canonical matplotlib visualizer."""

from __future__ import annotations

try:
    from visualizer import (
        plot_mode_shape,
        plot_model_preview,
        plot_response_spectrum,
        plot_static_deformed_shape,
        plot_static_nvm_diagrams,
        plot_tha_history,
    )
except ImportError:  # pragma: no cover - supports package-style imports in some runners
    from ..visualizer import (
        plot_mode_shape,
        plot_model_preview,
        plot_response_spectrum,
        plot_static_deformed_shape,
        plot_static_nvm_diagrams,
        plot_tha_history,
    )


def render_model_preview(st_module, model) -> None:
    """Render model preview through visualizer.py."""
    if model is None:
        st_module.info("Build or load a model before displaying plots.")
        return
    fig, _ = plot_model_preview(model)
    st_module.pyplot(fig)


def render_static_visualizations(st_module, model, results) -> None:
    """Render static result plots when the required results exist."""
    if model is None:
        st_module.info("Build or load a model before displaying plots.")
        return
    if results is None:
        st_module.info("Run static analysis to display visualizations.")
        return

    st_module.subheader("Static Visualizations")
    fig, _ = plot_static_deformed_shape(model, results)
    st_module.pyplot(fig)
    if getattr(results, "nvm_data", None):
        fig, _ = plot_static_nvm_diagrams(model, results)
        st_module.pyplot(fig)
    else:
        st_module.info("No N/V/M data available for diagrams.")


def render_dynamic_visualizations(st_module, model, modal_results=None, rsa_results=None, tha_results=None) -> None:
    """Render dynamic plots for whichever result objects are available."""
    if model is None:
        st_module.info("Build or load a model before displaying plots.")
        return
    if modal_results is None and rsa_results is None and tha_results is None:
        st_module.info("Run dynamic analysis to display visualizations.")
        return

    st_module.subheader("Dynamic Visualizations")
    if modal_results is not None:
        mode_count = len(getattr(modal_results, "mode_shapes", []) or [])
        if mode_count:
            for mode_index in range(mode_count):
                fig, _ = plot_mode_shape(model, modal_results, mode_index=mode_index)
                st_module.pyplot(fig)
        else:
            st_module.info("No mode shapes available for plotting.")

    if rsa_results is not None:
        fig, _ = plot_response_spectrum(rsa_results)
        st_module.pyplot(fig)

    if tha_results is not None:
        history_specs = (
            ("displacement", "displacement_history"),
            ("velocity", "velocity_history"),
            ("acceleration", "acceleration_history"),
            ("base_shear", "base_shear_history"),
            ("overturning_moment", "overturning_moment_history"),
        )
        for response, attribute in history_specs:
            if not getattr(tha_results, attribute, None):
                continue
            fig, _ = plot_tha_history(tha_results, response=response, dof=0)
            st_module.pyplot(fig)
