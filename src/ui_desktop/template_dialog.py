"""New model template dialog for the Tkinter desktop UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk


def _load_model_builder():
    try:
        from src.model_builder import ModelBuilder
    except ModuleNotFoundError:
        src_dir = Path(__file__).resolve().parents[1]
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        from model_builder import ModelBuilder

    return ModelBuilder


@dataclass
class ShearFrameSettings:
    stories: int
    bays: int
    story_height: float
    bay_width: float
    material_id: str
    column_section_id: str
    beam_section_id: str
    lumped_mass_per_floor: float
    mass_placement: str
    diaphragm_per_floor: bool
    unit_system: str
    project_name: str


class NewModelDialog(tk.Toplevel):
    """Modal wizard-style dialog that creates a ModelBuilder-backed model."""

    TEMPLATE_OPTIONS = ("Blank Model", "2D Shear Frame Template")

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.title("New Model")
        self.resizable(False, False)
        self.result = None
        self.error_message = tk.StringVar(value="")

        self.project_name_var = tk.StringVar(value="New Model")
        self.unit_system_var = tk.StringVar(value="kN_m_tonne")
        self.template_var = tk.StringVar(value="Blank Model")
        self.stories_var = tk.StringVar(value="1")
        self.bays_var = tk.StringVar(value="1")
        self.story_height_var = tk.StringVar(value="3.0")
        self.bay_width_var = tk.StringVar(value="5.0")
        self.material_var = tk.StringVar(value="M1")
        self.column_section_var = tk.StringVar(value="COL")
        self.beam_section_var = tk.StringVar(value="BEAM")
        self.mass_var = tk.StringVar(value="")
        self.mass_placement_var = tk.StringVar(value="none")
        self.diaphragm_var = tk.BooleanVar(value=True)
        self._template_sensitive_widgets = []
        self._general_section_widgets = []
        self._shear_section_widgets = []
        self._mass_widgets = []

        self._build()
        self._sync_template_fields()
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        setup = ttk.LabelFrame(frame, text="Step 1: Units / Project Setup", padding=8)
        setup.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        setup.columnconfigure(1, weight=1)
        self._add_entry(setup, 0, "Project name", self.project_name_var)
        ttk.Label(setup, text="Units").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Combobox(
            setup,
            textvariable=self.unit_system_var,
            values=("N_m_kg", "kN_m_tonne", "kN_m_kNsec2_per_m"),
            state="readonly",
            width=20,
        ).grid(row=1, column=1, sticky="ew", pady=2)

        model_type = ttk.LabelFrame(frame, text="Step 2: Model Type", padding=8)
        model_type.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        model_type.columnconfigure(1, weight=1)
        ttk.Label(model_type, text="Template").grid(row=0, column=0, sticky="w", pady=2)
        template_box = ttk.Combobox(
            model_type,
            textvariable=self.template_var,
            values=self.TEMPLATE_OPTIONS,
            state="readonly",
            width=22,
        )
        template_box.grid(row=0, column=1, sticky="ew", pady=2)
        template_box.bind("<<ComboboxSelected>>", lambda event: self._sync_template_fields())

        defaults = ttk.LabelFrame(frame, text="Step 3: Default Properties", padding=8)
        defaults.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        defaults.columnconfigure(1, weight=1)
        self._add_entry(defaults, 0, "Default material", self.material_var)
        column_label, column_entry = self._add_entry(defaults, 1, "Column section", self.column_section_var)
        beam_label, beam_entry = self._add_entry(defaults, 2, "Beam/member section", self.beam_section_var)
        self._shear_section_widgets.extend([column_label, column_entry])
        self._general_section_widgets.extend([beam_label, beam_entry])

        self.geometry_frame = ttk.LabelFrame(frame, text="Step 4: Geometry / Template Settings", padding=8)
        self.geometry_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.geometry_frame.columnconfigure(1, weight=1)
        for widgets in (
            self._add_entry(self.geometry_frame, 0, "Stories", self.stories_var),
            self._add_entry(self.geometry_frame, 1, "Bays", self.bays_var),
            self._add_entry(self.geometry_frame, 2, "Story height", self.story_height_var),
            self._add_entry(self.geometry_frame, 3, "Bay width", self.bay_width_var),
        ):
            self._template_sensitive_widgets.extend(widgets)
        placement_label = ttk.Label(self.geometry_frame, text="Mass placement")
        placement_label.grid(row=4, column=0, sticky="w", pady=2)
        placement_box = ttk.Combobox(
            self.geometry_frame,
            textvariable=self.mass_placement_var,
            values=("none", "center floor node", "distribute to floor nodes"),
            state="readonly",
            width=22,
        )
        placement_box.grid(row=4, column=1, sticky="ew", pady=2)
        placement_box.bind("<<ComboboxSelected>>", lambda event: self._sync_template_fields())
        mass_label, mass_entry = self._add_entry(self.geometry_frame, 5, "Mass per floor", self.mass_var)
        self._mass_widgets = [mass_label, mass_entry]
        diaphragm_check = ttk.Checkbutton(
            self.geometry_frame,
            text="Rigid floor diaphragm system",
            variable=self.diaphragm_var,
        )
        diaphragm_check.grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(6, 0),
        )
        self._template_sensitive_widgets.extend([placement_label, placement_box, diaphragm_check])

        ttk.Label(frame, textvariable=self.error_message, foreground="#a00000").grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(2, 6),
        )

        actions = ttk.Frame(frame)
        actions.grid(row=5, column=0, columnspan=2, sticky="e")
        ttk.Button(actions, text="Cancel", command=self._cancel).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(actions, text="Create", command=self._create).grid(row=0, column=1)

    def _add_entry(self, parent, row: int, label: str, variable: tk.StringVar) -> tuple[ttk.Label, ttk.Entry]:
        label_widget = ttk.Label(parent, text=label)
        label_widget.grid(row=row, column=0, sticky="w", pady=2)
        entry_widget = ttk.Entry(parent, textvariable=variable, width=16)
        entry_widget.grid(row=row, column=1, sticky="ew", pady=2)
        return label_widget, entry_widget

    def _sync_template_fields(self) -> None:
        is_shear_frame = self.template_var.get() == "2D Shear Frame Template"
        state = "normal" if is_shear_frame else "disabled"
        for child in self._template_sensitive_widgets:
            try:
                child.configure(state=state)
            except tk.TclError:
                pass
        mass_state = "normal" if is_shear_frame and self.mass_placement_var.get() != "none" else "disabled"
        for child in self._mass_widgets:
            try:
                child.configure(state=mass_state)
            except tk.TclError:
                pass
        for child in self._shear_section_widgets:
            if is_shear_frame:
                child.grid()
            else:
                child.grid_remove()
        if self._general_section_widgets:
            self._general_section_widgets[0].configure(
                text="Beam/member section" if is_shear_frame else "Default section"
            )

    def _create(self) -> None:
        try:
            if self.template_var.get() == "Blank Model":
                self.result = create_general_structure_builder(
                    self.project_name_var.get().strip() or "Blank Model",
                    self.unit_system_var.get().strip() or "kN_m_tonne",
                    self.material_var.get().strip() or "M1",
                    self.beam_section_var.get().strip() or "S1",
                )
            else:
                self.result = create_shear_frame_builder(self._read_shear_frame_settings())
        except ValueError as exc:
            self.error_message.set(str(exc))
            return
        self.destroy()

    def _read_shear_frame_settings(self) -> ShearFrameSettings:
        stories = _positive_int(self.stories_var.get(), "Stories")
        bays = _positive_int(self.bays_var.get(), "Bays")
        story_height = _positive_float(self.story_height_var.get(), "Story height")
        bay_width = _positive_float(self.bay_width_var.get(), "Bay width")
        mass_text = self.mass_var.get().strip()
        mass = _nonnegative_float(mass_text, "Mass/floor") if mass_text else 0.0
        return ShearFrameSettings(
            stories=stories,
            bays=bays,
            story_height=story_height,
            bay_width=bay_width,
            material_id=self.material_var.get().strip() or "M1",
            column_section_id=self.column_section_var.get().strip() or "COL",
            beam_section_id=self.beam_section_var.get().strip() or "BEAM",
            lumped_mass_per_floor=mass,
            mass_placement=self.mass_placement_var.get(),
            diaphragm_per_floor=self.diaphragm_var.get(),
            unit_system=self.unit_system_var.get().strip() or "kN_m_tonne",
            project_name=self.project_name_var.get().strip() or "New Model",
        )

    def _cancel(self) -> None:
        self.result = None
        self.destroy()


def ask_new_model(parent):
    dialog = NewModelDialog(parent)
    parent.wait_window(dialog)
    return dialog.result


def create_general_structure_builder(name: str, unit_system: str, material_id: str, section_id: str):
    ModelBuilder = _load_model_builder()
    builder = ModelBuilder(name=name, unit_system=unit_system)
    builder.add_material(material_id, E=1.0)
    builder.add_section(section_id, A=1.0, I=1.0)
    return builder


def create_shear_frame_builder(settings: ShearFrameSettings):
    ModelBuilder = _load_model_builder()
    builder = ModelBuilder(name=settings.project_name, unit_system=settings.unit_system)
    builder.creation_messages = []
    builder.add_material(settings.material_id, E=1.0)
    builder.add_section(settings.column_section_id, A=1.0, I=1.0)
    builder.add_section(settings.beam_section_id, A=1.0, I=1.0)

    node_ids: dict[tuple[int, int], int] = {}
    node_id = 1
    for story in range(settings.stories + 1):
        y = story * settings.story_height
        for bay in range(settings.bays + 1):
            x = bay * settings.bay_width
            builder.add_node(node_id, x, y)
            node_ids[(story, bay)] = node_id
            node_id += 1

    element_number = 1
    for story in range(settings.stories):
        for bay in range(settings.bays + 1):
            builder.add_element(
                f"E{element_number}",
                "frame",
                node_ids[(story, bay)],
                node_ids[(story + 1, bay)],
                settings.material_id,
                settings.column_section_id,
            )
            element_number += 1

    for story in range(1, settings.stories + 1):
        for bay in range(settings.bays):
            builder.add_element(
                f"E{element_number}",
                "frame",
                node_ids[(story, bay)],
                node_ids[(story, bay + 1)],
                settings.material_id,
                settings.beam_section_id,
            )
            element_number += 1

    for bay in range(settings.bays + 1):
        builder.add_support(node_ids[(0, bay)], restrain_ux=True, restrain_uy=True, restrain_rz=True)

    if settings.mass_placement != "none" and settings.lumped_mass_per_floor > 0.0:
        for story in range(1, settings.stories + 1):
            floor_nodes = [node_ids[(story, bay)] for bay in range(settings.bays + 1)]
            center_bay = settings.bays / 2.0
            if settings.mass_placement == "center floor node" and center_bay.is_integer():
                center_node_id = node_ids[(story, int(center_bay))]
                builder.add_lumped_mass(center_node_id, mass_ux=settings.lumped_mass_per_floor)
                builder.creation_messages.append(
                    f"Floor {story}: story mass assigned to center node {center_node_id}."
                )
            else:
                mass_per_node = settings.lumped_mass_per_floor / len(floor_nodes)
                for node_id in floor_nodes:
                    builder.add_lumped_mass(node_id, mass_ux=mass_per_node)
                if settings.mass_placement == "center floor node":
                    builder.creation_messages.append(
                        f"Floor {story}: no center node exists; distributed story mass to {len(floor_nodes)} floor nodes."
                    )
                else:
                    builder.creation_messages.append(
                        f"Floor {story}: story mass distributed to {len(floor_nodes)} floor nodes."
                    )

    if settings.diaphragm_per_floor:
        for story in range(1, settings.stories + 1):
            floor_nodes = [node_ids[(story, bay)] for bay in range(settings.bays + 1)]
            builder.add_diaphragm_group(f"D{story}", floor_nodes)

    return builder


def _positive_int(value: str, label: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an integer.") from exc
    if number <= 0:
        raise ValueError(f"{label} must be positive.")
    return number


def _positive_float(value: str, label: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if number <= 0.0:
        raise ValueError(f"{label} must be positive.")
    return number


def _nonnegative_float(value: str, label: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if number < 0.0:
        raise ValueError(f"{label} cannot be negative.")
    return number
