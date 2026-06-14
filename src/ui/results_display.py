"""Formatting helpers for Streamlit result display."""

from __future__ import annotations


def render_static_results(st_module, results) -> None:
    """Display static-analysis result objects without solver or plotting work."""
    if results is None:
        st_module.info("Run static analysis to display results.")
        return

    st_module.subheader("Static Results")
    st_module.caption(f"Load case: {getattr(results, 'load_case_id', '')}")
    _display_mapping_table(st_module, "Displacements", getattr(results, "displacements", None), ("ux", "uy", "rz"))
    _display_mapping_table(st_module, "Reactions", getattr(results, "reactions", None), ("Fx", "Fy", "Mz"))
    _display_mapping_table(
        st_module,
        "Member Forces",
        getattr(results, "element_forces", None),
        ("Ni", "Vi", "Mi", "Nj", "Vj", "Mj"),
    )
    _display_nvm_data(st_module, getattr(results, "nvm_data", None))


def render_dynamic_results(st_module, modal_results=None, rsa_results=None, tha_results=None) -> None:
    """Display available modal, RSA, and THA result objects."""
    if modal_results is None and rsa_results is None and tha_results is None:
        st_module.info("Run dynamic analysis to display results.")
        return

    if modal_results is not None:
        st_module.subheader("Modal Results")
        _display_rows(
            st_module,
            "Modes",
            [
                {
                    "mode": index + 1,
                    "frequency": frequency,
                    "period": _value_at(getattr(modal_results, "periods", []), index),
                    "modal_mass": _value_at(getattr(modal_results, "modal_masses", []), index),
                    "participation": _value_at(getattr(modal_results, "participation_factors", []), index),
                    "effective_mass": _value_at(getattr(modal_results, "effective_masses", []), index),
                }
                for index, frequency in enumerate(getattr(modal_results, "frequencies", []) or [])
            ],
        )
        _display_sequence(st_module, "Mode Shapes", getattr(modal_results, "mode_shapes", None))

    if rsa_results is not None:
        st_module.subheader("Response Spectrum Results")
        st_module.write(
            {
                "method": getattr(rsa_results, "combination_method", ""),
                "combined_base_shear": getattr(rsa_results, "combined_base_shear", None),
                "combined_overturning_moment": getattr(rsa_results, "combined_overturning_moment", None),
                "combined_response": getattr(rsa_results, "combined_response", {}),
            }
        )
        _display_rows(
            st_module,
            "Modal RSA Responses",
            [
                {
                    "mode": index + 1,
                    "period": _value_at(getattr(rsa_results, "periods", []), index),
                    "base_shear": _value_at(getattr(rsa_results, "modal_base_shears", []), index),
                    "overturning_moment": _value_at(getattr(rsa_results, "modal_overturning_moments", []), index),
                    "response": response,
                }
                for index, response in enumerate(getattr(rsa_results, "modal_response_vectors", []) or [])
            ],
        )

    if tha_results is not None:
        st_module.subheader("Time History Results")
        st_module.write(
            {
                "steps": getattr(tha_results, "num_steps", None),
                "dt": getattr(tha_results, "dt", None),
                "peak_displacement": getattr(tha_results, "peak_displacement", {}),
                "peak_base_shear": getattr(tha_results, "peak_base_shear", None),
                "peak_overturning_moment": getattr(tha_results, "peak_overturning_moment", None),
            }
        )
        _display_sequence(st_module, "Time Vector", getattr(tha_results, "time_vector", None))
        _display_sequence(st_module, "Excitation History", getattr(tha_results, "excitation_history", None))
        _display_sequence(st_module, "Applied Force History", getattr(tha_results, "applied_force_history", None))
        _display_sequence(st_module, "Displacement History", getattr(tha_results, "displacement_history", None))
        _display_sequence(st_module, "Velocity History", getattr(tha_results, "velocity_history", None))
        _display_sequence(st_module, "Acceleration History", getattr(tha_results, "acceleration_history", None))
        _display_sequence(st_module, "Base Shear History", getattr(tha_results, "base_shear_history", None))
        _display_sequence(
            st_module,
            "Overturning Moment History",
            getattr(tha_results, "overturning_moment_history", None),
        )


def _display_mapping_table(st_module, title: str, mapping, columns: tuple[str, ...]) -> None:
    st_module.markdown(f"**{title}**")
    if not mapping:
        st_module.info(f"No {title.lower()} available.")
        return
    rows = []
    for item_id, values in mapping.items():
        row = {"id": item_id}
        for index, column in enumerate(columns):
            row[column] = _value_at(values, index)
        rows.append(row)
    st_module.dataframe(rows)


def _display_nvm_data(st_module, nvm_data) -> None:
    st_module.markdown("**N/V/M Data**")
    if not nvm_data:
        st_module.info("No N/V/M data available.")
        return
    rows = []
    for element_id, data in nvm_data.items():
        rows.append(
            {
                "element": element_id,
                "x": data.get("x", []),
                "N": data.get("N", []),
                "V": data.get("V", []),
                "M": data.get("M", []),
            }
        )
    st_module.dataframe(rows)


def _display_rows(st_module, title: str, rows: list[dict]) -> None:
    st_module.markdown(f"**{title}**")
    if rows:
        st_module.dataframe(rows)
    else:
        st_module.info(f"No {title.lower()} available.")


def _display_sequence(st_module, title: str, values) -> None:
    st_module.markdown(f"**{title}**")
    if values:
        st_module.write(values)
    else:
        st_module.info(f"No {title.lower()} available.")


def _value_at(values, index: int):
    if isinstance(values, dict):
        return values.get(index)
    if isinstance(values, (list, tuple)) and index < len(values):
        return values[index]
    return None
