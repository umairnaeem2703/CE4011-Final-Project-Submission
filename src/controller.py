"""Thin MVC-style controller facade for model construction and analysis calls."""

from __future__ import annotations

from typing import Any

from main import run_analysis, run_response_spectrum_analysis, run_time_history_analysis
from model_builder import ModelBuilder
from parser import StructuralModel
from structural_validator import StructuralValidator


class ModelController:
    """Coordinate model-building operations without owning solver or UI logic."""

    def __init__(
        self,
        model: StructuralModel | None = None,
        *,
        name: str | None = None,
        unit_system: str | None = None,
    ) -> None:
        self.builder = ModelBuilder(model, name=name, unit_system=unit_system)

    @property
    def model(self) -> StructuralModel:
        return self.builder.model

    def add_material(self, *args: Any, **kwargs: Any):
        return self.builder.add_material(*args, **kwargs)

    def add_section(self, *args: Any, **kwargs: Any):
        return self.builder.add_section(*args, **kwargs)

    def add_node(self, *args: Any, **kwargs: Any):
        return self.builder.add_node(*args, **kwargs)

    def add_element(self, *args: Any, **kwargs: Any):
        return self.builder.add_element(*args, **kwargs)

    def add_support(self, *args: Any, **kwargs: Any):
        return self.builder.add_support(*args, **kwargs)

    def validate(self) -> StructuralModel:
        StructuralValidator(self.model).validate()
        return self.model

    def export_xml(self, filepath: str) -> None:
        self.builder.export_xml(filepath)

    def run_analysis_from_xml(self, xml_filepath: str, output_dir: str = "./results", plot: bool = True):
        return run_analysis(xml_filepath, output_dir=output_dir, plot=plot)

    def run_time_history_analysis(self, K, M, C, ground_motion_config, r, damping_ratio: float = 0.0):
        return run_time_history_analysis(K, M, C, ground_motion_config, r, damping_ratio=damping_ratio)

    def run_response_spectrum_analysis(
        self,
        modal_results,
        spectrum_periods: list,
        spectrum_accelerations: list,
        combination_method: str = "SRSS",
        damping_ratio: float = 0.05,
    ):
        return run_response_spectrum_analysis(
            modal_results,
            spectrum_periods,
            spectrum_accelerations,
            combination_method=combination_method,
            damping_ratio=damping_ratio,
        )
