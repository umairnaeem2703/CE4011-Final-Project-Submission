# src/visualizer.py

import math
from collections.abc import Mapping, Sequence
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from parser import StructuralModel, UniformlyDL, PointLoad, MemberLoad, LoadCase
from post_processor import PostProcessor
from element_physics import ElementPhysics
from results import ModalResults, RSAResults, StaticResults, THAResults

N_STEPS = 30  # discretization points per element


def build_full_displacements(model: StructuralModel, D_active: List[List[float]]) -> Dict[int, List[float]]:
    """
    Build nodal displacement map {node_id: [ux, uy, rz]} from active equation results.
    Restrained DOFs use prescribed settlement values (or 0.0 by default).
    """
    displacements: Dict[int, List[float]] = {}

    for node_id, node in model.nodes.items():
        node_disp: List[float] = []
        support = model.supports.get(node_id)

        for dof_idx, dof in enumerate(node.dofs):
            if dof >= 0:
                node_disp.append(D_active[dof][0])
                continue

            if support is None:
                node_disp.append(0.0)
                continue

            if dof_idx == 0 and support.restrain_ux:
                node_disp.append(support.settlement_ux)
            elif dof_idx == 1 and support.restrain_uy:
                node_disp.append(support.settlement_uy)
            elif dof_idx == 2 and support.restrain_rz:
                node_disp.append(support.settlement_rz)
            else:
                node_disp.append(0.0)

        displacements[node_id] = node_disp

    return displacements


def _local_nodal_displacements(c: float, s: float, d_i: List[float], d_j: List[float]) -> List[float]:
    """
    Step 1: Extract element nodal displacements in global coordinates and transform to local.
    Returns [u1, v1, th1, u2, v2, th2].
    """
    ux1, uy1, th1 = d_i
    ux2, uy2, th2 = d_j

    u1 = c * ux1 + s * uy1
    v1 = -s * ux1 + c * uy1
    u2 = c * ux2 + s * uy2
    v2 = -s * ux2 + c * uy2

    return [u1, v1, th1, u2, v2, th2]


def _hermite_transverse_displacement(x: float, L: float, v1: float, th1: float, v2: float, th2: float) -> float:
    """
    Step 3: Hermite cubic interpolation of transverse displacement:
        v(x) = N1*v1 + N2*th1 + N3*v2 + N4*th2
    """
    xi = x / L

    n1 = 1.0 - 3.0 * xi * xi + 2.0 * xi * xi * xi
    n2 = L * (xi - 2.0 * xi * xi + xi * xi * xi)
    n3 = 3.0 * xi * xi - 2.0 * xi * xi * xi
    n4 = L * (-xi * xi + xi * xi * xi)

    return n1 * v1 + n2 * th1 + n3 * v2 + n4 * th2


# ============================================================
# Support and Hinge Drawing Helpers
# ============================================================

def _draw_support(ax: plt.Axes, x: float, y: float, support, size: float = 0.35) -> None:
    """
    Draw a support symbol at the given (x, y) position.

    Types determined from restrain flags:
      - Fixed (ux + uy + rz): filled square with ground hatching
      - Pin   (ux + uy):      triangle
      - Roller_x (uy only):   triangle with horizontal rollers line
      - Roller_y (ux only):   rotated triangle with vertical rollers line
    """
    color = "0.3"

    ux = support.restrain_ux
    uy = support.restrain_uy
    rz = support.restrain_rz

    if ux and uy and rz:
        half = size * 0.6
        rect = mpatches.FancyBboxPatch(
            (x - half, y - half * 1.4), half * 2, half * 1.4,
            boxstyle="square,pad=0", facecolor="none", edgecolor=color, linewidth=1.5
        )
        ax.add_patch(rect)
        n_hatch = 5
        for i in range(n_hatch):
            hx = x - half + (2 * half) * i / (n_hatch - 1)
            ax.plot([hx, hx - half * 0.4], [y - half * 1.4, y - half * 1.4 - half * 0.4],
                    color=color, linewidth=0.8)

    elif ux and uy and not rz:
        tri_h = size
        tri_w = size * 0.8
        triangle = plt.Polygon(
            [[x, y], [x - tri_w / 2, y - tri_h], [x + tri_w / 2, y - tri_h]],
            closed=True, facecolor="none", edgecolor=color, linewidth=1.5
        )
        ax.add_patch(triangle)
        ax.plot([x - tri_w * 0.7, x + tri_w * 0.7], [y - tri_h, y - tri_h],
                color=color, linewidth=1.5)

    elif uy and not ux:
        tri_h = size * 0.8
        tri_w = size * 0.7
        triangle = plt.Polygon(
            [[x, y], [x - tri_w / 2, y - tri_h], [x + tri_w / 2, y - tri_h]],
            closed=True, facecolor="none", edgecolor=color, linewidth=1.5
        )
        ax.add_patch(triangle)
        r = size * 0.1
        for cx in [x - tri_w * 0.25, x + tri_w * 0.25]:
            circle = plt.Circle((cx, y - tri_h - r * 1.2), r, facecolor="none",
                                edgecolor=color, linewidth=1.0)
            ax.add_patch(circle)
        ax.plot([x - tri_w * 0.7, x + tri_w * 0.7], [y - tri_h - r * 2.4, y - tri_h - r * 2.4],
                color=color, linewidth=1.5)

    elif ux and not uy:
        tri_h = size * 0.8
        tri_w = size * 0.7
        triangle = plt.Polygon(
            [[x, y], [x - tri_h, y - tri_w / 2], [x - tri_h, y + tri_w / 2]],
            closed=True, facecolor="none", edgecolor=color, linewidth=1.5
        )
        ax.add_patch(triangle)
        r = size * 0.1
        for cy in [y - tri_w * 0.25, y + tri_w * 0.25]:
            circle = plt.Circle((x - tri_h - r * 1.2, cy), r, facecolor="none",
                                edgecolor=color, linewidth=1.0)
            ax.add_patch(circle)
        ax.plot([x - tri_h - r * 2.4, x - tri_h - r * 2.4], [y - tri_w * 0.7, y + tri_w * 0.7],
                color=color, linewidth=1.5)


def _draw_hinges(ax: plt.Axes, model: StructuralModel, radius: float = 0.15) -> None:
    """
    Draw small open circles at element ends that have moment releases (hinges).
    Placed slightly inset from the node along the element axis.
    """
    for element in model.elements.values():
        if element.type != 'frame':
            continue

        xi, yi = element.node_i.x, element.node_i.y
        xj, yj = element.node_j.x, element.node_j.y
        dx = xj - xi
        dy = yj - yi
        L = math.hypot(dx, dy)
        if L == 0.0:
            continue
        cx, cy = dx / L, dy / L
        inset = min(0.3, L * 0.08)

        if element.release_start:
            hx = xi + cx * inset
            hy = yi + cy * inset
            circle = plt.Circle((hx, hy), radius, facecolor="white",
                                edgecolor="tab:red", linewidth=1.5, zorder=5)
            ax.add_patch(circle)

        if element.release_end:
            hx = xj - cx * inset
            hy = yj - cy * inset
            circle = plt.Circle((hx, hy), radius, facecolor="white",
                                edgecolor="tab:red", linewidth=1.5, zorder=5)
            ax.add_patch(circle)


# ============================================================
# Deformed Shape — Core Plot Function
# ============================================================

def plot_deformed_shape(
    model: StructuralModel,
    displacements: Dict[int, List[float]],
    scale_factor: Optional[float] = None,
    sub_segments: int = 20,
    show_undeformed: bool = True,
    lc_id: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """
    Plot deformed structural shape using per-element Hermite interpolation.
    Supports Adaptive Auto-Scaling if `scale_factor` is set to None.
    """
    if sub_segments <= 0:
        raise ValueError("sub_segments must be a positive integer.")

    if ax is None:
        _, ax = plt.subplots(figsize=(9, 6))

    # --- Adaptive Auto-Scaling ---
    if scale_factor is None:
        x_coords = [n.x for n in model.nodes.values()]
        y_coords = [n.y for n in model.nodes.values()]

        if not x_coords or not y_coords:
            scale_factor = 1.0
        else:
            diag = math.hypot(max(x_coords) - min(x_coords), max(y_coords) - min(y_coords))
            if diag == 0.0:
                diag = 1.0

            max_disp = 0.0

            for element in model.elements.values():
                node_i = element.node_i
                node_j = element.node_j

                dx = node_j.x - node_i.x
                dy = node_j.y - node_i.y
                L = math.hypot(dx, dy)
                if L == 0.0:
                    continue

                c = dx / L
                s = dy / L

                d_i = displacements.get(node_i.id, [0.0, 0.0, 0.0])
                d_j = displacements.get(node_j.id, [0.0, 0.0, 0.0])
                u1, v1, th1, u2, v2, th2 = _local_nodal_displacements(c, s, d_i, d_j)

                for i in range(11):
                    x_local = L * i / 10.0
                    u_local = (1.0 - x_local / L) * u1 + (x_local / L) * u2

                    if element.type == 'truss':
                        v_local = (1.0 - x_local / L) * v1 + (x_local / L) * v2
                    else:
                        v_local = _hermite_transverse_displacement(x_local, L, v1, th1, v2, th2)

                    disp_mag = math.hypot(u_local, v_local)
                    if disp_mag > max_disp:
                        max_disp = disp_mag

            if max_disp > 1e-12:
                scale_factor = (0.10 * diag) / max_disp
            else:
                scale_factor = 1.0

    # --- Geometry Mapping ---
    for element in model.elements.values():
        node_i = element.node_i
        node_j = element.node_j

        x_i, y_i = node_i.x, node_i.y
        x_j, y_j = node_j.x, node_j.y

        dx = x_j - x_i
        dy = y_j - y_i
        L = math.hypot(dx, dy)
        if L == 0.0:
            continue

        c = dx / L
        s = dy / L

        d_i = displacements.get(node_i.id, [0.0, 0.0, 0.0])
        d_j = displacements.get(node_j.id, [0.0, 0.0, 0.0])
        u1, v1, th1, u2, v2, th2 = _local_nodal_displacements(c, s, d_i, d_j)

        if show_undeformed:
            ax.plot([x_i, x_j], [y_i, y_j], color="0.75", linestyle="--", linewidth=1.0)

        x_values = [L * i / sub_segments for i in range(sub_segments + 1)]
        x_global_def: List[float] = []
        y_global_def: List[float] = []

        for x_local in x_values:
            u_local = (1.0 - x_local / L) * u1 + (x_local / L) * u2

            if element.type == 'truss':
                v_local = (1.0 - x_local / L) * v1 + (x_local / L) * v2
            else:
                v_local = _hermite_transverse_displacement(x_local, L, v1, th1, v2, th2)

            x_local_def = x_local + scale_factor * u_local
            y_local_def = scale_factor * v_local

            x_global = x_i + c * x_local_def - s * y_local_def
            y_global = y_i + s * x_local_def + c * y_local_def

            x_global_def.append(x_global)
            y_global_def.append(y_global)

        ax.plot(x_global_def, y_global_def, color="tab:blue", linewidth=1.8)

    for node_id, support in model.supports.items():
        node = model.nodes[node_id]
        _draw_support(ax, node.x, node.y, support)

    _draw_hinges(ax, model)

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(f"Deformed Shape (Scale = {scale_factor:.1f}x)")
    ax.grid(True, linestyle=":", linewidth=0.6)

    return ax


def plot_deformed_shape_from_active(
    model: StructuralModel,
    D_active: List[List[float]],
    scale_factor: Optional[float] = None,
    sub_segments: int = 20,
    show_undeformed: bool = True,
    lc_id: Optional[str] = None,
    ax: Optional[plt.Axes] = None,
) -> plt.Axes:
    """Convenience wrapper when solved active displacement vector is available."""
    displacements = build_full_displacements(model, D_active)
    return plot_deformed_shape(
        model=model,
        displacements=displacements,
        scale_factor=scale_factor,
        sub_segments=sub_segments,
        show_undeformed=show_undeformed,
        lc_id=lc_id,
        ax=ax,
    )


def save_deformed_shape_from_active(
    model: StructuralModel,
    D_active: List[List[float]],
    filepath: str,
    scale_factor: Optional[float] = None,
    sub_segments: int = 20,
    show_undeformed: bool = True,
    lc_id: Optional[str] = None,
    dpi: int = 200,
) -> None:
    """Create a deformed-shape figure and save it to disk."""
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_deformed_shape_from_active(
        model=model,
        D_active=D_active,
        scale_factor=scale_factor,
        sub_segments=sub_segments,
        show_undeformed=show_undeformed,
        lc_id=lc_id,
        ax=ax,
    )
    fig.tight_layout()
    fig.savefig(filepath, dpi=dpi)
    print(f"✅ Deformed shape plot written to {filepath}")
    plt.close(fig)


# ============================================================
# Result-object plotting adapters
# ============================================================

def plot_model_preview(
    model: StructuralModel,
    ax: Optional[plt.Axes] = None,
) -> tuple:
    """Plot model geometry, node/element labels, supports, and hinges."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 6))
    else:
        fig = ax.figure

    _draw_structure(ax, model)

    for node in model.nodes.values():
        ax.text(node.x, node.y, str(node.id), fontsize=8, ha="right", va="bottom")

    for element in model.elements.values():
        mx = 0.5 * (element.node_i.x + element.node_j.x)
        my = 0.5 * (element.node_i.y + element.node_j.y)
        ax.text(mx, my, str(element.id), fontsize=8, ha="center", va="bottom")

    for node_id, support in model.supports.items():
        node = model.nodes[node_id]
        _draw_support(ax, node.x, node.y, support)

    _draw_hinges(ax, model)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Model Preview")
    ax.grid(True, linestyle=":", linewidth=0.6)
    return fig, ax


def plot_static_deformed_shape(
    model: StructuralModel,
    results: StaticResults,
    scale_factor: Optional[float] = None,
    sub_segments: int = 20,
    show_undeformed: bool = True,
    ax: Optional[plt.Axes] = None,
) -> tuple:
    """Plot deformed shape directly from StaticResults."""
    ax = plot_deformed_shape(
        model=model,
        displacements=getattr(results, "displacements", {}) or {},
        scale_factor=scale_factor,
        sub_segments=sub_segments,
        show_undeformed=show_undeformed,
        lc_id=getattr(results, "load_case_id", None),
        ax=ax,
    )
    return ax.figure, ax


def _annotate_extrema_labels(ax, raw_values: list[float], diag_x: list[float], diag_y: list[float]) -> None:
    if not raw_values:
        return

    max_val = max(raw_values)
    min_val = min(raw_values)

    if max(abs(max_val), abs(min_val)) < 1e-5:
        return

    indices_to_label = set()
    if abs(max_val - min_val) < 1e-5:
        indices_to_label.add(len(raw_values) // 2)
    else:
        indices_to_label.add(raw_values.index(max_val))
        indices_to_label.add(raw_values.index(min_val))

    for idx in indices_to_label:
        val = raw_values[idx]
        if abs(val) < 1e-5:
            continue

        val_str = f"{val:.2f}".rstrip("0").rstrip(".")
        ax.text(
            diag_x[idx],
            diag_y[idx],
            val_str,
            color="black",
            fontsize=8,
            ha="center",
            va="center",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", pad=1.0),
            zorder=5,
        )


def _draw_element_diagram_from_nvm(ax, el, nvm: dict, diagram_key: str, dynamic_scale: float, *, show_extrema: bool = False):
    phys = ElementPhysics(el)
    cos_x, sin_x = phys.cos_x, phys.sin_x
    nx, ny = -sin_x, cos_x
    xi, yi = el.node_i.x, el.node_i.y
    raw_values = nvm.get(diagram_key, []) if nvm else []
    stations = nvm.get("x", []) if nvm else []
    if raw_values and not stations:
        if len(raw_values) == 1:
            stations = [0.0]
        else:
            stations = [phys.L * i / (len(raw_values) - 1) for i in range(len(raw_values))]
    count = min(len(stations), len(raw_values))
    stations = stations[:count]
    raw_values = raw_values[:count]

    base_pts = []
    diag_pts = []
    for station, raw_value in zip(stations, raw_values):
        plot_val = -raw_value if diagram_key == "M" else raw_value
        bx = xi + station * cos_x
        by = yi + station * sin_x
        base_pts.append((bx, by))
        diag_pts.append((bx + plot_val * dynamic_scale * nx, by + plot_val * dynamic_scale * ny))

    pos_color = "tab:green"
    neg_color = "tab:red"
    for i in range(len(base_pts) - 1):
        v0 = raw_values[i]
        v1 = raw_values[i + 1]
        b0, b1 = base_pts[i], base_pts[i + 1]
        d0, d1 = diag_pts[i], diag_pts[i + 1]
        if v0 * v1 >= 0:
            color = pos_color if (v0 + v1) >= 0 else neg_color
            ax.fill(
                [b0[0], b1[0], d1[0], d0[0]],
                [b0[1], b1[1], d1[1], d0[1]],
                alpha=0.35,
                color=color,
                edgecolor="none",
                zorder=2,
            )
        else:
            t = v0 / (v0 - v1)
            zx = b0[0] + t * (b1[0] - b0[0])
            zy = b0[1] + t * (b1[1] - b0[1])
            c0 = pos_color if v0 >= 0 else neg_color
            c1 = pos_color if v1 >= 0 else neg_color
            ax.fill(
                [b0[0], zx, zx, d0[0]],
                [b0[1], zy, zy, d0[1]],
                alpha=0.35,
                color=c0,
                edgecolor="none",
                zorder=2,
            )
            ax.fill(
                [zx, b1[0], d1[0], zx],
                [zy, b1[1], d1[1], zy],
                alpha=0.35,
                color=c1,
                edgecolor="none",
                zorder=2,
            )

    if diag_pts:
        ax.plot([p[0] for p in diag_pts], [p[1] for p in diag_pts], color="black", linewidth=1.0, zorder=3)

    if show_extrema:
        _annotate_extrema_labels(ax, raw_values, [p[0] for p in diag_pts], [p[1] for p in diag_pts])


def _flatten_scalar(value):
    current = value
    while isinstance(current, Sequence) and not isinstance(current, (str, bytes)) and len(current) == 1:
        current = current[0]
    return current


def _coerce_float_sequence(values) -> list[float]:
    if values is None:
        return []
    if isinstance(values, Mapping):
        values = values.values()
    if isinstance(values, (str, bytes)):
        values = [values]

    coerced: list[float] = []
    for value in values:
        scalar = _flatten_scalar(value)
        try:
            coerced.append(float(scalar))
        except (TypeError, ValueError):
            coerced.append(0.0)
    return coerced


def _resolve_member_key(values: Mapping, member_id: object):
    for key in values.keys():
        if str(key) == str(member_id):
            return key
    return None


def _series_value_at(stations: list[float], values: list[float], x: float) -> float:
    if not stations or not values:
        return 0.0
    if len(stations) == 1:
        return values[0]
    if x <= stations[0]:
        return values[0]
    if x >= stations[-1]:
        return values[-1]

    for index in range(len(stations) - 1):
        x0 = stations[index]
        x1 = stations[index + 1]
        if x0 <= x <= x1:
            if x1 == x0:
                return values[index]
            ratio = (x - x0) / (x1 - x0)
            return values[index] + (values[index + 1] - values[index]) * ratio
    return values[-1]


def _series_extrema(stations: list[float], values: list[float]) -> dict:
    if not stations or not values:
        return {}
    max_index = max(range(len(values)), key=lambda idx: abs(values[idx]))
    return {
        "x": stations[max_index],
        "value": values[max_index],
        "index": max_index,
    }


def build_member_review_profile(model: StructuralModel, results: StaticResults, member_id: object) -> dict | None:
    """Build SAP-style member review data from stored StaticResults."""
    if model is None or results is None:
        return None

    element_key = None
    model_elements = getattr(model, "elements", {}) or {}
    result_keys = []
    for source in (getattr(results, "element_forces", None) or {}, getattr(results, "nvm_data", None) or {}):
        result_keys.extend(list(source.keys()))

    for key in list(model_elements.keys()) + result_keys:
        if str(key) == str(member_id):
            element_key = key
            break
    if element_key is None or element_key not in model_elements:
        return None

    element = model_elements[element_key]
    phys = ElementPhysics(element)
    L = phys.L
    nvm_data = getattr(results, "nvm_data", None) or {}
    member_nvm = nvm_data.get(element_key) or nvm_data.get(str(element_key)) or {}
    stations = _coerce_float_sequence(member_nvm.get("x")) if member_nvm else []
    if not stations:
        station_count = 20
        stations = [L * i / station_count for i in range(station_count + 1)]

    n_values = _coerce_float_sequence(member_nvm.get("N"))
    v_values = _coerce_float_sequence(member_nvm.get("V"))
    m_values = _coerce_float_sequence(member_nvm.get("M"))

    displacements = getattr(results, "displacements", {}) or {}
    d_i = _coerce_float_sequence(displacements.get(element.node_i.id))
    d_j = _coerce_float_sequence(displacements.get(element.node_j.id))
    while len(d_i) < 3:
        d_i.append(0.0)
    while len(d_j) < 3:
        d_j.append(0.0)
    c, s = phys.cos_x, phys.sin_x
    u1, v1, th1, u2, v2, th2 = _local_nodal_displacements(c, s, d_i[:3], d_j[:3])
    if element.type == "truss":
        disp_values = [((1.0 - x / L) * u1 + (x / L) * u2) if L else 0.0 for x in stations]
        disp_label = "Axial displacement"
    else:
        disp_values = [_hermite_transverse_displacement(x, L, v1, th1, v2, th2) if L else 0.0 for x in stations]
        disp_label = "Transverse displacement"

    forces = getattr(results, "element_forces", None) or {}
    raw_forces = forces.get(element_key) or forces.get(str(element_key)) or {}
    if isinstance(raw_forces, Mapping):
        i_forces = _coerce_float_sequence(raw_forces.get("i"))
        j_forces = _coerce_float_sequence(raw_forces.get("j"))
    else:
        force_values = _coerce_float_sequence(raw_forces)
        if len(force_values) >= 6:
            i_forces = force_values[:3]
            j_forces = force_values[3:6]
        elif len(force_values) >= 4:
            i_forces = force_values[:2] + [0.0]
            j_forces = force_values[2:4] + [0.0]
        else:
            i_forces = force_values[:3] + [0.0] * max(0, 3 - len(force_values))
            j_forces = [0.0, 0.0, 0.0]

    if len(i_forces) < 3:
        i_forces += [0.0] * (3 - len(i_forces))
    if len(j_forces) < 3:
        j_forces += [0.0] * (3 - len(j_forces))
    end_forces = {
        "Ni": i_forces[0],
        "Vi": i_forces[1],
        "Mi": i_forces[2],
        "Nj": j_forces[0],
        "Vj": j_forces[1],
        "Mj": j_forces[2],
    }

    return {
        "member_id": element_key,
        "element": element,
        "length": L,
        "stations": stations,
        "N": n_values,
        "V": v_values,
        "M": m_values,
        "disp": disp_values,
        "disp_label": disp_label,
        "end_forces": end_forces,
        "load_case_id": getattr(results, "load_case_id", None),
    }


def _prepare_display_series(profile: dict, displacement_mode: str) -> tuple[list[float], list[float], list[float], list[float]]:
    stations = list(profile.get("stations", []) or [])
    n_values = list(profile.get("N", []) or [])
    v_values = list(profile.get("V", []) or [])
    m_values = list(profile.get("M", []) or [])
    disp_values = list(profile.get("disp", []) or [])

    if displacement_mode == "relative_min" and disp_values:
        min_value = min(disp_values)
        disp_values = [value - min_value for value in disp_values]
    elif displacement_mode == "relative_ends" and len(disp_values) >= 2 and stations:
        start_value = disp_values[0]
        end_value = disp_values[-1]
        length = stations[-1] if stations[-1] else 1.0
        disp_values = [value - (start_value + (end_value - start_value) * (station / length)) for station, value in zip(stations, disp_values)]

    return stations, n_values, v_values, m_values, disp_values


def _annotate_series_extrema(ax, stations: list[float], values: list[float]) -> None:
    if not stations or not values:
        return
    max_index = max(range(len(values)), key=lambda idx: abs(values[idx]))
    if abs(values[max_index]) < 1e-5:
        return
    ax.scatter([stations[max_index]], [values[max_index]], color="black", s=18, zorder=4)
    ax.annotate(
        f"{values[max_index]:.2f}".rstrip("0").rstrip("."),
        xy=(stations[max_index], values[max_index]),
        xytext=(5, 6),
        textcoords="offset points",
        fontsize=8,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1.0),
    )


def plot_member_review_panel(
    profile: dict,
    cursor_x: float,
    *,
    displacement_mode: str = "absolute",
    scroll_for_values: bool = True,
    show_max: bool = True,
):
    """Plot a SAP-style member review panel for one static member."""
    fig, axes = plt.subplots(
        5,
        1,
        sharex=True,
        figsize=(12, 10),
        gridspec_kw={"height_ratios": [0.9, 1.0, 1.0, 1.0, 1.0]},
        constrained_layout=True,
    )

    stations, n_values, v_values, m_values, disp_values = _prepare_display_series(profile, displacement_mode)
    length = profile.get("length", 1.0) or 1.0
    cursor_x = max(0.0, min(float(cursor_x), length))
    current = {
        "N": _series_value_at(stations, n_values, cursor_x),
        "V": _series_value_at(stations, v_values, cursor_x),
        "M": _series_value_at(stations, m_values, cursor_x),
        "disp": _series_value_at(stations, disp_values, cursor_x),
    }

    titles = [
        "Member End Forces",
        "Axial Force N",
        "Shear Force V",
        "Bending Moment M",
        f"{profile.get('disp_label', 'Displacement')} Diagram",
    ]

    end_forces = profile.get("end_forces", {}) or {}
    forces_axis = axes[0]
    forces_axis.set_title(titles[0], fontsize=11, fontweight="bold")
    forces_axis.set_xlim(0, length)
    forces_axis.set_ylim(-1.2, 1.2)
    forces_axis.set_yticks([])
    forces_axis.grid(True, axis="x", alpha=0.15)
    forces_axis.axhline(0.0, color="0.45", linewidth=1.0)
    forces_axis.axvline(cursor_x, color="tab:blue", linestyle="--", linewidth=1.0)
    forces_axis.plot([0.0, length], [0.0, 0.0], color="black", linewidth=1.4)
    left_text = f"I-End\nN={end_forces.get('Ni', 0.0):.2f}\nV={end_forces.get('Vi', 0.0):.2f}\nM={end_forces.get('Mi', 0.0):.2f}"
    right_text = f"J-End\nN={end_forces.get('Nj', 0.0):.2f}\nV={end_forces.get('Vj', 0.0):.2f}\nM={end_forces.get('Mj', 0.0):.2f}"
    forces_axis.text(0.01 * length, 0.75, left_text, fontsize=8, ha="left", va="top", bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1.0))
    forces_axis.text(0.99 * length, 0.75, right_text, fontsize=8, ha="right", va="top", bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1.0))

    series_payload = [
        (axes[1], stations, n_values, "N", "Axial"),
        (axes[2], stations, v_values, "V", "Shear"),
        (axes[3], stations, m_values, "M", "Moment"),
        (axes[4], stations, disp_values, "disp", profile.get("disp_label", "Displacement")),
    ]

    maxima = {}
    for index, (ax, x_values, y_values, key, ylabel) in enumerate(series_payload):
        ax.set_title(titles[index + 1] if key != "disp" else titles[4], fontsize=11, fontweight="bold")
        ax.set_ylabel(ylabel)
        ax.set_xlim(0, length)
        ax.axhline(0.0, color="0.45", linewidth=1.0)
        ax.axvline(cursor_x, color="tab:blue", linestyle="--", linewidth=1.0)
        ax.grid(True, alpha=0.2)

        if not x_values or not y_values:
            ax.text(0.5, 0.5, "No N/V/M data available." if key in {"N", "V", "M"} else "Displacement unavailable.", ha="center", va="center", transform=ax.transAxes)
            continue

        ax.plot(x_values, y_values, color="black", linewidth=1.3)
        ax.fill_between(x_values, 0.0, y_values, where=[value >= 0.0 for value in y_values], color="tab:green", alpha=0.22)
        ax.fill_between(x_values, 0.0, y_values, where=[value < 0.0 for value in y_values], color="tab:red", alpha=0.18)
        if show_max:
            _annotate_series_extrema(ax, x_values, y_values)
            max_index = max(range(len(y_values)), key=lambda idx: abs(y_values[idx]))
            maxima[key] = {"x": x_values[max_index], "value": y_values[max_index]}
        else:
            max_index = max(range(len(y_values)), key=lambda idx: abs(y_values[idx]))
            maxima[key] = {"x": x_values[max_index], "value": y_values[max_index]}

        if scroll_for_values:
            y_at_cursor = _series_value_at(x_values, y_values, cursor_x)
            ax.scatter([cursor_x], [y_at_cursor], color="tab:blue", s=14, zorder=5)
            ax.annotate(
                f"{y_at_cursor:.2f}".rstrip("0").rstrip("."),
                xy=(cursor_x, y_at_cursor),
                xytext=(5, 6),
                textcoords="offset points",
                fontsize=8,
                bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1.0),
            )

    axes[-1].set_xlabel("Member Length")
    fig.suptitle(f"Member Review - {profile.get('member_id', '')} ({profile.get('load_case_id', '')})", fontsize=13, fontweight="bold")
    return fig, axes, {"cursor_x": cursor_x, "current": current, "end_forces": end_forces, "maxima": maxima}


def plot_static_nvm_diagram(
    model: StructuralModel,
    results: StaticResults,
    diagram_key: str,
    scale: Optional[float] = None,
    ax: Optional[plt.Axes] = None,
    show_extrema: bool = False,
):
    """Plot one axial/shear/moment diagram from StaticResults.nvm_data."""
    labels = {
        "N": "Axial Force (N)",
        "V": "Shear Force (V)",
        "M": "Bending Moment (M)",
    }
    if diagram_key not in labels:
        raise ValueError("diagram_key must be one of 'N', 'V', or 'M'.")
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 6))
    else:
        fig = ax.figure

    x_coords = [node.x for node in model.nodes.values()]
    y_coords = [node.y for node in model.nodes.values()]
    max_dim = max(max(x_coords) - min(x_coords), max(y_coords) - min(y_coords)) if x_coords and y_coords else 1.0
    nvm_data = getattr(results, "nvm_data", {}) or {}

    _draw_structure(ax, model)
    max_value = max((abs(value) for data in nvm_data.values() for value in data.get(diagram_key, [])), default=1.0)
    dynamic_scale = scale if scale is not None else (0.15 * max_dim) / max_value if max_value > 0 else 1.0

    for element_id, element in model.elements.items():
        if element_id in nvm_data:
            _draw_element_diagram_from_nvm(ax, element, nvm_data[element_id], diagram_key, dynamic_scale, show_extrema=show_extrema)

    ax.set_title(labels[diagram_key], fontsize=11, fontweight="bold")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    fig.suptitle(f"{labels[diagram_key]} - {getattr(results, 'load_case_id', '')}", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig, ax


def plot_static_nvm_diagrams(
    model: StructuralModel,
    results: StaticResults,
    scale: Optional[float] = None,
    axes: Optional[List[plt.Axes]] = None,
    show_extrema: bool = False,
):
    """Plot axial, shear, and moment diagrams from StaticResults.nvm_data."""
    if axes is None:
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    else:
        fig = axes[0].figure

    x_coords = [node.x for node in model.nodes.values()]
    y_coords = [node.y for node in model.nodes.values()]
    max_dim = max(max(x_coords) - min(x_coords), max(y_coords) - min(y_coords)) if x_coords and y_coords else 1.0
    nvm_data = getattr(results, "nvm_data", {}) or {}
    labels = [("N", "Axial Force (N)"), ("V", "Shear Force (V)"), ("M", "Bending Moment (M)")]

    for ax, (key, label) in zip(axes, labels):
        _draw_structure(ax, model)
        max_value = max((abs(value) for data in nvm_data.values() for value in data.get(key, [])), default=1.0)
        dynamic_scale = scale if scale is not None else (0.15 * max_dim) / max_value if max_value > 0 else 1.0

        for element_id, element in model.elements.items():
            if element_id in nvm_data:
                _draw_element_diagram_from_nvm(ax, element, nvm_data[element_id], key, dynamic_scale, show_extrema=show_extrema)

        ax.set_title(label, fontsize=11, fontweight="bold")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("X (m)")
        ax.set_ylabel("Y (m)")

    fig.suptitle(f"NVM Diagrams - {getattr(results, 'load_case_id', '')}", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return fig, axes


def _mode_shape_displacements(model: StructuralModel, mode_shape: list) -> Dict[int, List[float]]:
    displacements: Dict[int, List[float]] = {}
    for node_id, node in model.nodes.items():
        values = []
        for dof in node.dofs:
            value = mode_shape[dof] if dof >= 0 and dof < len(mode_shape) else 0.0
            if isinstance(value, list):
                value = value[0] if value else 0.0
            values.append(value)
        while len(values) < 3:
            values.append(0.0)
        displacements[node_id] = values[:3]
    return displacements


def plot_mode_shape(
    model: StructuralModel,
    results: ModalResults,
    mode_index: int = 0,
    scale_factor: Optional[float] = None,
    ax: Optional[plt.Axes] = None,
) -> tuple:
    """Plot one modal deformed shape from ModalResults."""
    mode_shapes = getattr(results, "mode_shapes", []) or []
    if mode_index < 0 or mode_index >= len(mode_shapes):
        raise ValueError("mode_index is outside available mode_shapes.")

    ax = plot_deformed_shape(
        model=model,
        displacements=_mode_shape_displacements(model, mode_shapes[mode_index]),
        scale_factor=scale_factor,
        show_undeformed=True,
        ax=ax,
    )
    periods = getattr(results, "periods", []) or []
    period = periods[mode_index] if mode_index < len(periods) else None
    suffix = f", T = {period:.3g} s" if period is not None else ""
    ax.set_title(f"Mode Shape {mode_index + 1}{suffix}")
    return ax.figure, ax


def _response_component(history: list, dof: int) -> list:
    values = []
    for step in history:
        if isinstance(step, dict):
            values.append(step.get(dof, 0.0))
        elif isinstance(step, (list, tuple)):
            values.append(step[dof] if dof < len(step) else 0.0)
        else:
            values.append(step)
    return values


def plot_tha_history(
    results: THAResults,
    response: str = "displacement",
    dof: int = 0,
    ax: Optional[plt.Axes] = None,
) -> tuple:
    """Plot a THA response history from THAResults."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4))
    else:
        fig = ax.figure

    histories = {
        "displacement": (getattr(results, "displacement_history", []) or [], "Displacement", "m"),
        "velocity": (getattr(results, "velocity_history", []) or [], "Velocity", "m/s"),
        "acceleration": (getattr(results, "acceleration_history", []) or [], "Acceleration", "m/s^2"),
        "base_shear": (getattr(results, "base_shear_history", []) or [], "Base Shear", "kN"),
        "overturning_moment": (getattr(results, "overturning_moment_history", []) or [], "Overturning Moment", "kN-m"),
    }
    if response not in histories:
        raise ValueError(f"Unknown THA response: {response}")

    history, label, unit = histories[response]
    if response in {"base_shear", "overturning_moment"}:
        values = history
    else:
        values = _response_component(history, dof)

    time_vector = getattr(results, "time_vector", []) or []
    count = min(len(time_vector), len(values))
    ax.plot(time_vector[:count], values[:count], color="tab:blue", linewidth=1.5)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel(f"{label} ({unit})")
    ax.set_title(f"THA {label} History")
    ax.grid(True, linestyle=":", linewidth=0.6)
    return fig, ax


def plot_response_spectrum(
    results: RSAResults,
    ax: Optional[plt.Axes] = None,
) -> tuple:
    """Plot the input response spectrum from RSAResults."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 4))
    else:
        fig = ax.figure

    periods = getattr(results, "spectrum_periods", []) or []
    accelerations = getattr(results, "spectrum_accelerations", []) or []
    if not accelerations:
        accelerations = getattr(results, "spectrum_values", []) or []
    count = min(len(periods), len(accelerations))
    ax.plot(periods[:count], accelerations[:count], color="tab:blue", linewidth=1.5)
    ax.set_xlabel("Period (s)")
    ax.set_ylabel("Spectral Acceleration")
    ax.set_title("Response Spectrum")
    ax.grid(True, linestyle=":", linewidth=0.6)
    return fig, ax


# ============================================================
# NVM Diagrams
# ============================================================

def plot_nvm_diagrams(
    model: StructuralModel,
    processor: PostProcessor,
    load_case_id: str,
    scale: float = None,
    save_path: str = None,
) -> None:
    """
    Generates Axial (N), Shear (V), and Bending Moment (M) diagrams and saves to disk.
    """
    load_case = model.load_cases[load_case_id]

    x_coords = [n.x for n in model.nodes.values()]
    y_coords = [n.y for n in model.nodes.values()]
    max_dim = max(max(x_coords) - min(x_coords), max(y_coords) - min(y_coords)) if x_coords and y_coords else 1.0

    max_forces = _compute_max_forces(model, processor, load_case)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    diagram_labels = ['Axial Force (N)', 'Shear Force (V)', 'Bending Moment (M)']

    for idx, (ax, label) in enumerate(zip(axes, diagram_labels)):
        _draw_structure(ax, model)

        if scale is not None:
            dynamic_scale = scale
        else:
            max_val = max_forces[idx]
            dynamic_scale = (0.15 * max_dim) / max_val if max_val > 0 else 1.0

        for el_id, el in model.elements.items():
            _draw_element_diagram(ax, el, processor, load_case, idx, dynamic_scale)

        ax.set_title(label, fontsize=11, fontweight='bold')
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('X (m)')
        ax.set_ylabel('Y (m)')

    fig.suptitle(f'NVM Diagrams — {load_case.name} ({load_case_id})',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 NVM diagram saved to {save_path}")

    plt.close(fig)


# ============================================================
# Internal helpers for NVM computation
# ============================================================

def _compute_max_forces(model: StructuralModel, processor: PostProcessor, load_case: LoadCase) -> list:
    max_N = 0.0
    max_V = 0.0
    max_M = 0.0

    for el_id, el in model.elements.items():
        phys = ElementPhysics(el)
        L = phys.L

        forces = processor.member_forces[el_id]
        if el.type == 'truss':
            N1, V1, M1 = forces[0][0], forces[1][0], 0.0
        else:
            N1, V1, M1 = forces[0][0], forces[1][0], forces[2][0]

        wx, wy, point_loads = _get_element_loads(el, load_case)

        for i in range(N_STEPS + 1):
            x = L * i / N_STEPS
            N_x, V_x, M_x = _compute_internal_forces(x, N1, V1, M1, wx, wy, point_loads)

            max_N = max(max_N, abs(N_x))
            max_V = max(max_V, abs(V_x))
            max_M = max(max_M, abs(M_x))

    return [max_N if max_N > 0 else 1.0, max_V if max_V > 0 else 1.0, max_M if max_M > 0 else 1.0]


def _draw_structure(ax, model: StructuralModel):
    for el in model.elements.values():
        xi, yi = el.node_i.x, el.node_i.y
        xj, yj = el.node_j.x, el.node_j.y
        ax.plot([xi, xj], [yi, yj], 'k-', linewidth=1.5, zorder=1)

    for node in model.nodes.values():
        ax.plot(node.x, node.y, 'ko', markersize=4, zorder=3)


def _get_element_loads(el, load_case: LoadCase):
    wx_total = 0.0
    wy_total = 0.0
    point_loads = []

    for load in load_case.loads:
        if not isinstance(load, MemberLoad) or load.element.id != el.id:
            continue
        if isinstance(load, UniformlyDL):
            wx_total += load.wx
            wy_total += load.wy
        elif isinstance(load, PointLoad):
            point_loads.append((load.position, load.fx, load.fy))

    point_loads.sort(key=lambda p: p[0])
    return wx_total, wy_total, point_loads


def _build_x_stations(L: float, point_loads: list):
    stations = set()
    for i in range(N_STEPS + 1):
        stations.add(L * i / N_STEPS)

    eps = L * 1e-6
    for pos, _, _ in point_loads:
        if 0.0 < pos < L:
            stations.add(pos - eps)
            stations.add(pos)
            stations.add(pos + eps)

    return sorted(stations)


def _compute_internal_forces(x: float, N1: float, V1: float, M1: float,
                             wx: float, wy: float, point_loads: list):
    N = N1
    V = V1
    M = M1

    N -= wx * x
    V += wy * x
    M += V1 * x + (wy * x * x) / 2.0

    for pos, pfx, pfy in point_loads:
        if pos <= x:
            N -= pfx
            V += pfy
            M += pfy * (x - pos)

    return N, -V, M


def _draw_element_diagram(ax, el, processor: PostProcessor,
                          load_case: LoadCase, diagram_idx: int,
                          dynamic_scale: float):
    phys = ElementPhysics(el)
    L = phys.L
    cos_x, sin_x = phys.cos_x, phys.sin_x
    nx, ny = -sin_x, cos_x  # element normal direction

    forces = processor.member_forces[el.id]
    if el.type == 'truss':
        N1, V1, M1 = forces[0][0], forces[1][0], 0.0
    else:
        N1, V1, M1 = forces[0][0], forces[1][0], forces[2][0]

    wx, wy, point_loads = _get_element_loads(el, load_case)
    stations = _build_x_stations(L, point_loads)
    xi, yi = el.node_i.x, el.node_i.y

    raw_values = []
    base_pts   = []
    diag_pts   = []

    for x in stations:
        N_x, V_x, M_x = _compute_internal_forces(x, N1, V1, M1, wx, wy, point_loads)
        raw_value = (N_x, V_x, M_x)[diagram_idx]
        raw_values.append(raw_value)

        plot_val = -raw_value if diagram_idx == 2 else raw_value

        bx = xi + x * cos_x
        by = yi + x * sin_x
        base_pts.append((bx, by))
        diag_pts.append((bx + plot_val * dynamic_scale * nx,
                         by + plot_val * dynamic_scale * ny))

    POS_COLOR = 'tab:green'
    NEG_COLOR = 'tab:red'

    n = len(stations)
    for i in range(n - 1):
        v0 = raw_values[i]
        v1 = raw_values[i + 1]
        b0, b1 = base_pts[i], base_pts[i + 1]
        d0, d1 = diag_pts[i], diag_pts[i + 1]

        if v0 * v1 >= 0:
            color = POS_COLOR if (v0 + v1) >= 0 else NEG_COLOR
            ax.fill([b0[0], b1[0], d1[0], d0[0]],
                    [b0[1], b1[1], d1[1], d0[1]],
                    alpha=0.35, color=color, edgecolor='none', zorder=2)
        else:
            t = v0 / (v0 - v1)
            zx = b0[0] + t * (b1[0] - b0[0])
            zy = b0[1] + t * (b1[1] - b0[1])

            c0 = POS_COLOR if v0 >= 0 else NEG_COLOR
            ax.fill([b0[0], zx, zx, d0[0]],
                    [b0[1], zy, zy, d0[1]],
                    alpha=0.35, color=c0, edgecolor='none', zorder=2)

            c1 = POS_COLOR if v1 >= 0 else NEG_COLOR
            ax.fill([zx, b1[0], d1[0], zx],
                    [zy, b1[1], d1[1], zy],
                    alpha=0.35, color=c1, edgecolor='none', zorder=2)

    diag_x = [p[0] for p in diag_pts]
    diag_y = [p[1] for p in diag_pts]
    ax.plot(diag_x, diag_y, color='black', linewidth=1.0, zorder=3)

    if raw_values:
        max_val = max(raw_values)
        min_val = min(raw_values)

        if max(abs(max_val), abs(min_val)) >= 1e-5:
            indices_to_label = set()
            if abs(max_val - min_val) < 1e-5:
                indices_to_label.add(len(raw_values) // 2)
            else:
                indices_to_label.add(raw_values.index(max_val))
                indices_to_label.add(raw_values.index(min_val))

            for idx in indices_to_label:
                val = raw_values[idx]
                if abs(val) < 1e-5:
                    continue

                val_str = f"{val:.2f}".rstrip('0').rstrip('.')
                ax.text(diag_x[idx], diag_y[idx], val_str,
                        color='black', fontsize=8,
                        ha='center', va='center',
                        bbox=dict(facecolor='white', alpha=0.7,
                                  edgecolor='none', pad=1.0),
                        zorder=5)
