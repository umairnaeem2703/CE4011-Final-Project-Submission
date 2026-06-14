import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from banded_solver import UnstableStructureError
from controller import ModelController
from parser import StructuralModel, XMLParser


def _build_supported_controller() -> ModelController:
    controller = ModelController(name="Controller Demo")
    controller.add_material("m1", E=200000.0)
    controller.add_section("s1", A=0.02, I=0.0001)
    controller.add_node(1, 0.0, 0.0)
    controller.add_node(2, 3.0, 0.0)
    controller.add_element("e1", "frame", 1, 2, "m1", "s1")
    controller.add_support(1, restrain_ux=True, restrain_uy=True, restrain_rz=True)
    return controller


def test_model_controller_creates_model_through_builder():
    controller = ModelController(name="Empty Controller")

    assert isinstance(controller.model, StructuralModel)
    assert controller.model.name == "Empty Controller"
    assert controller.builder.model is controller.model


def test_model_controller_validates_using_existing_path():
    controller = _build_supported_controller()

    assert controller.validate() is controller.model


def test_model_controller_validation_raises_existing_error():
    controller = ModelController()

    with pytest.raises(UnstableStructureError, match="No boundary conditions"):
        controller.validate()


def test_model_controller_exports_xml_when_available(tmp_path):
    controller = _build_supported_controller()

    xml_path = tmp_path / "controller_model.xml"
    controller.export_xml(xml_path)
    parsed = XMLParser(xml_path).parse()

    assert parsed.name == controller.model.name
    assert len(parsed.elements) == len(controller.model.elements)
