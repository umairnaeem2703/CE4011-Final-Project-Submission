"""Formatting helpers for desktop result tables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


DEFAULT_DISPLAY_TOLERANCE = 1.0e-3

_UNIT_LABELS = {
    "kN_m_tonne": {"length": "m", "rotation": "rad", "force": "kN", "moment": "kN-m"},
}


def unit_labels(unit_system: str | None) -> dict[str, str]:
    """Return display unit labels, defaulting to metric placeholders."""
    return _UNIT_LABELS.get(unit_system or "", _UNIT_LABELS["kN_m_tonne"]).copy()


def format_scalar(value: object, *, tolerance: float = DEFAULT_DISPLAY_TOLERANCE) -> str:
    """Format one display value with configurable near-zero cleanup."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return str(value)
    value = unwrap_scalar(value)
    if isinstance(value, (int, float)):
        value = float(value)
        if abs(value) < tolerance:
            return "0"
        decimals = tolerance_decimals(tolerance)
        return f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    return str(value)


def format_vector(values: object, *, tolerance: float = DEFAULT_DISPLAY_TOLERANCE) -> tuple[str, ...]:
    """Format a row-like vector for display."""
    return tuple(format_scalar(value, tolerance=tolerance) for value in as_sequence(values))


def format_matrix(matrix: object, *, tolerance: float = DEFAULT_DISPLAY_TOLERANCE) -> list[tuple[str, ...]]:
    """Format a matrix or vector into string rows for table display."""
    if matrix is None:
        return []
    if not isinstance(matrix, Sequence) or isinstance(matrix, (str, bytes)):
        return [(format_scalar(matrix, tolerance=tolerance),)]
    rows: list[tuple[str, ...]] = []
    for row in matrix:
        if isinstance(row, Sequence) and not isinstance(row, (str, bytes)):
            rows.append(tuple(format_scalar(value, tolerance=tolerance) for value in row))
        else:
            rows.append((format_scalar(row, tolerance=tolerance),))
    return rows


def as_sequence(values: object) -> tuple[object, ...]:
    """Normalize scalars and iterables into a tuple."""
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        return tuple(values)
    return (values,)


def dof_display_rows(dof_map: Mapping[object, object]) -> list[tuple[str, str, str, str]]:
    """Display DOF map by node with restrained and active labels."""
    node_map: dict[object, dict[str, str]] = {}
    for key, value in (dof_map or {}).items():
        if isinstance(key, Sequence) and not isinstance(key, (str, bytes)) and len(key) >= 2:
            node_id, dof_name = key[0], str(key[1]).lower()
            if dof_name not in ("ux", "uy", "rz"):
                continue
            node_map.setdefault(node_id, {"ux": "-", "uy": "-", "rz": "-"})[dof_name] = format_dof_value(value)
            continue

        vector = as_sequence(value)
        if len(vector) < 3:
            continue
        node_map[key] = {
            "ux": format_dof_value(vector[0]),
            "uy": format_dof_value(vector[1]),
            "rz": format_dof_value(vector[2]),
        }

    def sort_key(item: tuple[object, dict[str, str]]) -> tuple[int, str]:
        node_id = item[0]
        return (0, str(node_id)) if isinstance(node_id, int) else (1, str(node_id))

    return [
        (str(node_id), entry["ux"], entry["uy"], entry["rz"])
        for node_id, entry in sorted(node_map.items(), key=sort_key)
    ]


def matrix_columns(matrix: object) -> tuple[str, ...]:
    """Create columns for vector or matrix display."""
    rows = format_matrix(matrix)
    if not rows:
        return ("Message",)
    width = max(len(row) for row in rows)
    return tuple(["Row"] + [f"C{index}" for index in range(width)])


def matrix_rows(matrix: object, *, tolerance: float = DEFAULT_DISPLAY_TOLERANCE) -> list[tuple[str, ...]]:
    """Create indexed rows for vector or matrix display."""
    rows = format_matrix(matrix, tolerance=tolerance)
    if not rows:
        return []
    width = max(len(row) for row in rows)
    padded_rows = []
    for index, row in enumerate(rows):
        padded = row + tuple("-" for _ in range(width - len(row)))
        padded_rows.append((f"R{index}",) + padded)
    return padded_rows


def unwrap_scalar(value: object) -> object:
    """Unwrap nested single-item sequences into one scalar display value."""
    current = value
    while isinstance(current, Sequence) and not isinstance(current, (str, bytes)) and len(current) == 1:
        current = current[0]
    return current


def tolerance_decimals(tolerance: float) -> int:
    """Convert a display tolerance into a practical decimal precision."""
    if tolerance <= 0.0:
        return 6
    text = f"{tolerance:.12f}".rstrip("0")
    if "." not in text:
        return 0
    return len(text.split(".", 1)[1])


def format_dof_value(value: object) -> str:
    """Format one DOF map entry for display."""
    scalar = unwrap_scalar(value)
    if scalar == -1:
        return "Fixed"
    return f"Eq {scalar}"
