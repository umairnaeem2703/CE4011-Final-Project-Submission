"""Grouped object tree for the desktop model builder."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


SelectionCallback = Callable[[str, str], None]


class ObjectTreePanel(ttk.LabelFrame):
    """Displays model objects grouped by type."""

    GROUPS = ("Materials", "Sections", "Nodes", "Elements", "Supports", "Loads", "Masses", "Diaphragms")

    def __init__(self, parent, *, selection_callback: SelectionCallback | None = None) -> None:
        super().__init__(parent, text="Objects", padding=6)
        self.selection_callback = selection_callback or (lambda kind, object_id: None)
        self.tree = ttk.Treeview(self, show="tree", height=10)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self._handle_select)

    def refresh(self, model) -> None:
        self.tree.delete(*self.tree.get_children())
        parents = {group: self.tree.insert("", "end", text=group, open=True) for group in self.GROUPS}

        for material_id in sorted(model.materials):
            material = model.materials[material_id]
            self.tree.insert(
                parents["Materials"],
                "end",
                iid=f"material:{material_id}",
                text=f"{material_id} (E={material.E:.3g})",
            )
        for section_id in sorted(model.sections):
            section = model.sections[section_id]
            self.tree.insert(
                parents["Sections"],
                "end",
                iid=f"section:{section_id}",
                text=f"{section_id} ({_section_summary(section)})",
            )
        for node_id in sorted(model.nodes):
            self.tree.insert(parents["Nodes"], "end", iid=f"node:{node_id}", text=f"Node {node_id}")
        for element_id in sorted(model.elements):
            element = model.elements[element_id]
            self.tree.insert(
                parents["Elements"],
                "end",
                iid=f"element:{element_id}",
                text=f"{element_id} ({element.type})",
            )
        for node_id in sorted(model.supports):
            support = model.supports[node_id]
            restraint = "".join(
                dof
                for dof, active in (
                    ("ux ", support.restrain_ux),
                    ("uy ", support.restrain_uy),
                    ("rz ", support.restrain_rz),
                )
                if active
            ).strip() or "free"
            self.tree.insert(parents["Supports"], "end", iid=f"support:{node_id}", text=f"Node {node_id} ({restraint})")
        for load_case in model.load_cases.values():
            for index, load in enumerate(load_case.loads, start=1):
                if hasattr(load, "node"):
                    text = f"{load_case.id} / Nodal / Node {load.node.id}"
                elif load.__class__.__name__ == "UniformlyDL":
                    text = f"{load_case.id} / UDL / {load.element.id}"
                elif load.__class__.__name__ == "PointLoad":
                    text = f"{load_case.id} / Point / {load.element.id}"
                elif load.__class__.__name__ == "TemperatureL":
                    text = f"{load_case.id} / Temperature / {load.element.id} (Tu={load.Tu:.3g}, Tb={load.Tb:.3g})"
                else:
                    text = f"{load_case.id}:{index}"
                self.tree.insert(parents["Loads"], "end", iid=f"load:{load_case.id}:{index}", text=text)
        for node_id in sorted(model.lumped_masses):
            self.tree.insert(
                parents["Masses"],
                "end",
                iid=f"mass:{node_id}",
                text=f"Node {node_id} ({_mass_summary(model.lumped_masses[node_id])})",
            )
        for diaphragm_id in sorted(model.diaphragm_ux_groups):
            self.tree.insert(
                parents["Diaphragms"],
                "end",
                iid=f"diaphragm:{diaphragm_id}",
                text=str(diaphragm_id),
            )

    def _handle_select(self, _event) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        if ":" not in item_id:
            return
        kind, object_id = item_id.split(":", 1)
        self.selection_callback(kind, object_id)


def _mass_summary(mass) -> str:
    if isinstance(mass, (int, float)):
        return f"mass_ux={mass:.3g}, mass_uy={mass:.3g}, mass_rz=0"
    return (
        f"mass_ux={mass.mass_ux:.3g}, "
        f"mass_uy={mass.mass_uy:.3g}, "
        f"mass_rz={mass.inertia_rz:.3g}"
    )


def _section_summary(section) -> str:
    if getattr(section, "EA", None) is not None or getattr(section, "EI", None) is not None:
        parts = [
            "EA/EI direct",
            f"EA={_format_optional(section.EA)}",
            f"EI={_format_optional(section.EI)}",
            f"thermal d={section.d:.3g}" if section.d else "thermal d=unset",
            "ignores material E for stiffness",
        ]
    else:
        parts = ["Geometric", f"A={section.A:.3g}", f"I={section.I:.3g}", f"d={section.d:.3g}"]
    return ", ".join(parts)


def _format_optional(value) -> str:
    return "unset" if value is None else f"{value:.3g}"
