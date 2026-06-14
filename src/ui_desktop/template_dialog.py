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
    base_support_type: str
    lumped_mass_per_floor: float
    diaphragm_per_floor: bool
    unit_system: str


class NewModelDialog(tk.Toplevel):
    """Modal wizard-style dialog that creates a ModelBuilder-backed model."""

    TEMPLATE_OPTIONS = ("2D General Structure", "2D Shear Frame")

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.title("New Model")
        self.resizable(False, False)
        self.result = None
        self.error_message = tk.StringVar(value="")

        self.project_name_var = tk.StringVar(value="Desktop Model")
        self.unit_system_var = tk.StringVar(value="kN_m_tonne")
        self.template_var = tk.StringVar(value="2D General Structure")
        self.stories_var = tk.StringVar(value="1")
        self.bays_var = tk.StringVar(value="1")
        self.story_height_var = tk.StringVar(value="3.0")
        self.bay_width_var = tk.StringVar(value="5.0")
        self.material_var = tk.StringVar(value="M1")
        self.column_section_var = tk.StringVar(value="COL")
        self.beam_section_var = tk.StringVar(value="BEAM")
        self.support_var = tk.StringVar(value="fixed")
        self.mass_var = tk.StringVar(value="")
        self.diaphragm_var = tk.BooleanVar(value=True)

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
        self._add_entry(setup, 1, "Units", self.unit_system_var)

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
        self._add_entry(defaults, 1, "Column section", self.column_section_var)
        self._add_entry(defaults, 2, "Beam/member section", self.beam_section_var)

        self.geometry_frame = ttk.LabelFrame(frame, text="Step 4: Geometry / Template Settings", padding=8)
        self.geometry_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.geometry_frame.columnconfigure(1, weight=1)
        self._add_entry(self.geometry_frame, 0, "Stories", self.stories_var)
        self._add_entry(self.geometry_frame, 1, "Bays", self.bays_var)
        self._add_entry(self.geometry_frame, 2, "Story height", self.story_height_var)
        self._add_entry(self.geometry_frame, 3, "Bay width", self.bay_width_var)
        ttk.Label(self.geometry_frame, text="Base support").grid(row=4, column=0, sticky="w", pady=2)
        support_box = ttk.Combobox(
            self.geometry_frame,
            textvariable=self.support_var,
            values=("fixed", "pin", "roller_x", "roller_y"),
            state="readonly",
            width=14,
        )
        support_box.grid(row=4, column=1, sticky="ew", pady=2)
        self._add_entry(self.geometry_frame, 5, "Mass/floor", self.mass_var)
        ttk.Checkbutton(self.geometry_frame, text="Diaphragm per floor", variable=self.diaphragm_var).grid(
            row=6,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(6, 0),
        )

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

    def _add_entry(self, parent, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=2)
        ttk.Entry(parent, textvariable=variable, width=16).grid(row=row, column=1, sticky="ew", pady=2)

    def _sync_template_fields(self) -> None:
        state = "normal" if self.template_var.get() == "2D Shear Frame" else "disabled"
        for child in self.geometry_frame.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass

    def _create(self) -> None:
        try:
            if self.template_var.get() == "2D General Structure":
                self.result = create_general_structure_builder(
                    self.project_name_var.get().strip() or "2D General Structure",
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
            base_support_type=self.support_var.get(),
            lumped_mass_per_floor=mass,
            diaphragm_per_floor=self.diaphragm_var.get(),
            unit_system=self.unit_system_var.get().strip() or "kN_m_tonne",
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
    builder = ModelBuilder(name="2D Shear Frame", unit_system=settings.unit_system)
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
        builder.add_support(node_ids[(0, bay)], **_support_kwargs(settings.base_support_type))

    if settings.lumped_mass_per_floor > 0.0:
        mass_per_node = settings.lumped_mass_per_floor / (settings.bays + 1)
        for story in range(1, settings.stories + 1):
            for bay in range(settings.bays + 1):
                builder.add_lumped_mass(node_ids[(story, bay)], mass_ux=mass_per_node, mass_uy=mass_per_node)

    if settings.diaphragm_per_floor:
        for story in range(1, settings.stories + 1):
            floor_nodes = [node_ids[(story, bay)] for bay in range(settings.bays + 1)]
            builder.add_diaphragm_group(f"D{story}", floor_nodes)

    return builder


def _support_kwargs(support_type: str) -> dict[str, bool]:
    if support_type == "pin":
        return {"restrain_ux": True, "restrain_uy": True, "restrain_rz": False}
    if support_type == "roller_x":
        return {"restrain_ux": False, "restrain_uy": True, "restrain_rz": False}
    if support_type == "roller_y":
        return {"restrain_ux": True, "restrain_uy": False, "restrain_rz": False}
    return {"restrain_ux": True, "restrain_uy": True, "restrain_rz": True}


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
