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
