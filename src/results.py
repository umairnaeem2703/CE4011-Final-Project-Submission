from dataclasses import dataclass


@dataclass
class StaticResults:
    """Static analysis output and educational intermediate data."""

    K: list
    Kff: list
    F: list
    Ff: list
    displacements: dict
    reactions: dict
    element_forces: dict
    nvm_data: dict
    dof_map: dict
    load_case_id: str


@dataclass
class DynamicAssemblyData:
    """Dynamic assembly output and educational intermediate data."""

    K: list
    M: list
    C: list
    Kff: list
    Mff: list
    Cff: list
    dof_map: dict
    free_dofs: list
    active_dynamic_dofs: list
    condensed_massless_dofs: list
    unit_system: str
    rayleigh_alpha: float
    rayleigh_beta: float


@dataclass
class ModalResults:
    """Modal analysis output and educational intermediate data."""

    K: list
    M: list
    eigenvalues: list
    frequencies: list
    periods: list
    mode_shapes: list
    modal_masses: list
    participation_factors: list
    effective_masses: list
    mass_participation_ratios: list
    influence_vector: list
    total_participating_mass: float
    num_modes_requested: int
    num_modes_extracted: int


@dataclass
class THAResults:
    """Time-history analysis output and educational intermediate data."""

    time_vector: list
    excitation_history: list
    applied_force_history: list
    displacement_history: list
    velocity_history: list
    acceleration_history: list
    base_shear_history: list
    overturning_moment_history: list
    peak_displacement: dict
    peak_velocity: dict
    peak_acceleration: dict
    peak_base_shear: float
    peak_overturning_moment: float
    step_table: list
    damping_ratio: float
    dt: float
    num_steps: int
    source_file: str
    acceleration_unit: str
    scale_factor: float
    input_format: str
