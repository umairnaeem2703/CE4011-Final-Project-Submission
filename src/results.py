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
