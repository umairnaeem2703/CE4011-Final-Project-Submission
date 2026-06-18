# tests/test_regression.py

import math
import os
import re
import sys
import unittest

# Add both source and test directories to path.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from banded_solver import BandedSolver
from dof_optimizer import DOFOptimizer
from matrix_assembly import DynamicAssembler, MatrixAssembler
from modal_solver import ModalSolver
from parser import XMLParser
from post_processor import PostProcessor
from sap2000_parser import (
    CoordinateMapper,
    SAP2000Parser,
    assert_displacement_match,
    assert_force_match,
)
from ui.dynamic_analysis import _build_rayleigh_damping_data


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _repo_path(*parts):
    return os.path.join(REPO_ROOT, *parts)


def _floats(text):
    pattern = r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][+-]?\d+)?"
    return [float(value) for value in re.findall(pattern, text)]


def _run_static_analysis(xml_path, load_case_id="LC1"):
    model = XMLParser(xml_path).parse()
    optimizer = DOFOptimizer(model)
    num_eq, semi_bw, _ = optimizer.optimize()
    assembler = MatrixAssembler(model, num_eq, semi_bw)
    K_banded, F_global = assembler.assemble(load_case_id)
    displacements = BandedSolver(K_banded, F_global, semi_bw).solve()
    processor = PostProcessor(model, displacements, load_case_id)
    results = processor.to_static_results(
        model.cached_K,
        model.cached_Kff,
        model.cached_F,
        model.cached_Ff,
        optimizer.dof_map,
        load_case_id,
    )
    return model, results


def _parse_sap_member_forces_by_model_end(sap_path, model):
    """Parse SAP2000 frame force rows and map them to each XML element I/J end."""
    forces_by_joint = {}
    in_table = False

    with open(sap_path, "r", encoding="utf-8") as file:
        for line in file:
            stripped = line.strip()
            if stripped == "Table:  Element Joint Forces - Frames":
                in_table = True
                continue
            if in_table and stripped.startswith("Table:"):
                break
            if not in_table or not stripped or stripped.startswith("Frame") or stripped.startswith("KN"):
                continue

            parts = stripped.split()
            if len(parts) < 11:
                continue

            try:
                element_id = parts[0]
                joint_id = int(parts[1])
                f1 = float(parts[4])
                f3 = float(parts[6])
                m2 = float(parts[8])
            except (ValueError, IndexError):
                continue

            forces_by_joint.setdefault(element_id, {})[joint_id] = CoordinateMapper.map_sap2000_force(
                f1,
                f3,
                m2,
            )

    forces_by_end = {}
    for element_id, element in model.elements.items():
        element_forces = forces_by_joint.get(element_id, {})
        if element.node_i.id in element_forces and element.node_j.id in element_forces:
            forces_by_end[element_id] = {
                "i": element_forces[element.node_i.id],
                "j": element_forces[element.node_j.id],
            }
    return forces_by_end


def _run_modal_analysis(xml_path, num_modes=3):
    model = XMLParser(xml_path).parse()
    optimizer = DOFOptimizer(model)
    num_eq, semi_bw, _ = optimizer.optimize()
    stiffness_assembler = MatrixAssembler(model, num_eq, semi_bw)
    K_full = stiffness_assembler.assemble_full_stiffness_matrix()
    dynamic_data = DynamicAssembler(model, num_eq).assemble_dynamic_data(K_full, matrix_type="lumped")
    influence_vector = _ux_influence_vector(model, dynamic_data.active_dynamic_dofs)
    modal_results = ModalSolver(dynamic_data.Kff, dynamic_data.Mff).solve(
        r=influence_vector,
        num_modes=num_modes,
    )
    return model, dynamic_data, modal_results


def _ux_influence_vector(model, active_dynamic_dofs):
    vector = []
    for dof in active_dynamic_dofs:
        vector.append(1.0 if any(node.dofs[0] == dof for node in model.nodes.values()) else 0.0)
    return vector


def _bottom_to_top_reduced_order(model, active_dynamic_dofs):
    dof_to_elevations = {}
    active_set = set(active_dynamic_dofs)

    for node_id, mass in model.lumped_masses.items():
        node = model.nodes[node_id]
        mass_ux = float(getattr(mass, "mass_ux", mass if isinstance(mass, (int, float)) else 0.0))
        dof = node.dofs[0]
        if mass_ux > 0.0 and dof in active_set:
            dof_to_elevations.setdefault(dof, []).append(node.y)

    bottom_to_top_dofs = sorted(dof_to_elevations, key=lambda dof: min(dof_to_elevations[dof]))
    dof_to_reduced_index = {dof: index for index, dof in enumerate(active_dynamic_dofs)}
    return [dof_to_reduced_index[dof] for dof in bottom_to_top_dofs]


def _reorder_square_matrix(matrix, order):
    return [[matrix[row][col] for col in order] for row in order]


class ModalBenchmarkParser:
    @staticmethod
    def parse(path):
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        return {
            "Kff": ModalBenchmarkParser._parse_stiffness(lines),
            "eigenvalues": ModalBenchmarkParser._parse_modal_column(lines, column=1),
            "omegas": ModalBenchmarkParser._parse_modal_column(lines, column=2),
            "periods": ModalBenchmarkParser._parse_modal_column(lines, column=3),
            "mode_shape_rows": ModalBenchmarkParser._parse_three_row_block(lines, "Mode Shapes"),
            "alpha": ModalBenchmarkParser._parse_named_value(lines, "alpha"),
            "beta": ModalBenchmarkParser._parse_named_value(lines, "beta"),
            "Cff": ModalBenchmarkParser._parse_three_row_block(lines, "Rayleigh Damping Matrix"),
        }

    @staticmethod
    def _parse_stiffness(lines):
        for index, line in enumerate(lines):
            if "*" not in line:
                continue
            values = _floats(line)
            if not values:
                continue

            scale = values[0]
            rows = ModalBenchmarkParser._collect_numeric_rows(lines, index + 1, count=3)
            if len(rows) == 3:
                return [[scale * value for value in row] for row in rows]
        raise AssertionError("Could not parse condensed stiffness matrix from modal benchmark.")

    @staticmethod
    def _parse_modal_column(lines, column):
        values = []
        in_table = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Mode | lambda"):
                in_table = True
                continue
            if in_table and not stripped:
                if values:
                    break
                continue
            if not in_table:
                continue

            row_values = _floats(stripped)
            if len(row_values) >= 4:
                values.append(row_values[column])

        if not values:
            raise AssertionError("Could not parse modal property table from benchmark.")
        return values

    @staticmethod
    def _parse_three_row_block(lines, header):
        for index, line in enumerate(lines):
            if header in line:
                rows = ModalBenchmarkParser._collect_numeric_rows(lines, index + 1, count=3)
                if len(rows) == 3:
                    return rows
        raise AssertionError(f"Could not parse '{header}' block from modal benchmark.")

    @staticmethod
    def _collect_numeric_rows(lines, start_index, count):
        rows = []
        for line in lines[start_index:]:
            values = _floats(line)
            if len(values) >= count:
                rows.append(values[:count])
                if len(rows) == count:
                    break
        return rows

    @staticmethod
    def _parse_named_value(lines, name):
        pattern = re.compile(rf"^\s*{re.escape(name)}\s*=\s*({_number_pattern()})", re.IGNORECASE)
        for line in lines:
            match = pattern.search(line)
            if match:
                return float(match.group(1))
        raise AssertionError(f"Could not parse {name} from modal benchmark.")


def _number_pattern():
    return r"[+-]?(?:\d+\.\d*|\.\d+|\d+)(?:[Ee][+-]?\d+)?"


class TestRegression(unittest.TestCase):
    def setUp(self):
        self.disp_rel_tol = 0.02
        self.force_rel_tol = 0.02

    def _compare_static_case(self, xml_path, sap_path, test_name):
        self.assertTrue(os.path.exists(xml_path), f"Missing XML input: {xml_path}")
        self.assertTrue(os.path.exists(sap_path), f"Missing SAP2000 benchmark: {sap_path}")

        model, solver_results = _run_static_analysis(xml_path)
        sap_disp, sap_react, _ = SAP2000Parser(sap_path).parse()
        sap_forces = _parse_sap_member_forces_by_model_end(sap_path, model)

        self.assertTrue(sap_disp, f"{test_name} SAP2000 displacement table was not parsed.")
        self.assertTrue(sap_react, f"{test_name} SAP2000 reaction table was not parsed.")
        self.assertTrue(sap_forces, f"{test_name} SAP2000 member-force table was not parsed.")

        self._assert_displacements_match(sap_disp, solver_results.displacements, test_name)
        self._assert_reactions_match(sap_react, solver_results.reactions, test_name)
        self._assert_member_end_forces_match(
            sap_forces,
            solver_results.member_end_forces,
            test_name,
        )

    def _assert_displacements_match(self, expected, computed, test_name):
        for node_id, expected_disp in expected.items():
            self.assertIn(node_id, computed, f"{test_name} node {node_id} missing from solver displacements.")
            match, error_msg = assert_displacement_match(
                computed[node_id],
                expected_disp,
                rel_tol=self.disp_rel_tol,
            )
            self.assertTrue(match, f"{test_name} node {node_id} displacement mismatch:\n{error_msg}")

    def _assert_reactions_match(self, expected, computed, test_name):
        for node_id, expected_reaction in expected.items():
            self.assertIn(node_id, computed, f"{test_name} node {node_id} missing from solver reactions.")
            match, error_msg = assert_force_match(
                computed[node_id],
                expected_reaction,
                rel_tol=self.force_rel_tol,
            )
            self.assertTrue(match, f"{test_name} node {node_id} reaction mismatch:\n{error_msg}")

    def _assert_member_end_forces_match(self, expected, computed, test_name):
        for element_id, expected_forces in expected.items():
            self.assertIn(element_id, computed, f"{test_name} element {element_id} missing from solver forces.")
            for end_label in ("i", "j"):
                match, error_msg = assert_force_match(
                    computed[element_id][end_label],
                    expected_forces[end_label],
                    rel_tol=self.force_rel_tol,
                )
                self.assertTrue(
                    match,
                    f"{test_name} element {element_id} end {end_label} force mismatch:\n{error_msg}",
                )

    def _assert_matrix_close(self, computed, expected, tolerance, label):
        self.assertEqual(len(computed), len(expected), f"{label} row count mismatch.")
        for row_index, (computed_row, expected_row) in enumerate(zip(computed, expected)):
            self.assertEqual(len(computed_row), len(expected_row), f"{label} column count mismatch.")
            for col_index, (computed_value, expected_value) in enumerate(zip(computed_row, expected_row)):
                self.assertLessEqual(
                    abs(computed_value - expected_value),
                    tolerance,
                    (
                        f"{label}[{row_index}][{col_index}] mismatch: "
                        f"computed {computed_value:.9g}, expected {expected_value:.9g}"
                    ),
                )

    def _assert_sequence_close(self, computed, expected, tolerance, label):
        self.assertEqual(len(computed), len(expected), f"{label} length mismatch.")
        for index, (computed_value, expected_value) in enumerate(zip(computed, expected)):
            self.assertLessEqual(
                abs(computed_value - expected_value),
                tolerance,
                f"{label}[{index}] mismatch: computed {computed_value:.9g}, expected {expected_value:.9g}",
            )

    def test_regression_01_frame_static_benchmark(self):
        self._compare_static_case(
            _repo_path("data", "test-frame.xml"),
            _repo_path("sap2000_solutions", "test-frame-results.txt"),
            "Frame",
        )

    def test_regression_02_settlement_static_benchmark(self):
        self._compare_static_case(
            _repo_path("data", "test-settlement.xml"),
            _repo_path("sap2000_solutions", "test-settlement-results.txt"),
            "Settlement",
        )

    def test_regression_03_temperature_static_benchmark(self):
        self._compare_static_case(
            _repo_path("data", "test-temperature.xml"),
            _repo_path("sap2000_solutions", "test-temperature-results.txt"),
            "Temperature",
        )

    def test_regression_04_modal_flexible_beam_benchmark(self):
        xml_path = _repo_path("data", "test-modal-flex-beam.xml")
        benchmark_path = _repo_path("modal_solution", "test-modal-flex-beam-results.txt")
        self.assertTrue(os.path.exists(xml_path), f"Missing XML input: {xml_path}")
        self.assertTrue(os.path.exists(benchmark_path), f"Missing modal benchmark: {benchmark_path}")

        benchmark = ModalBenchmarkParser.parse(benchmark_path)
        model, dynamic_data, modal_results = _run_modal_analysis(xml_path, num_modes=3)
        reduced_order = _bottom_to_top_reduced_order(model, dynamic_data.active_dynamic_dofs)
        self.assertEqual(len(reduced_order), 3, "Expected three positive-mass story UX DOFs.")

        rayleigh = _build_rayleigh_damping_data(
            modal_results,
            dynamic_data.Kff,
            dynamic_data.Mff,
            target_mode_i=1,
            zeta_i=0.05,
            target_mode_j=2,
            zeta_j=0.05,
        )

        self._assert_matrix_close(
            _reorder_square_matrix(dynamic_data.Kff, reduced_order),
            benchmark["Kff"],
            tolerance=1.0,
            label="Modal condensed Kff",
        )
        self._assert_sequence_close(
            modal_results.eigenvalues,
            benchmark["eigenvalues"],
            tolerance=0.02,
            label="Modal eigenvalue",
        )
        self._assert_sequence_close(
            [math.sqrt(value) for value in modal_results.eigenvalues],
            benchmark["omegas"],
            tolerance=0.002,
            label="Modal omega",
        )
        self._assert_sequence_close(
            modal_results.periods,
            benchmark["periods"],
            tolerance=0.002,
            label="Modal period",
        )

        normalized_modes = []
        top_reduced_index = reduced_order[-1]
        for mode_shape in modal_results.mode_shapes:
            top_value = mode_shape[top_reduced_index]
            self.assertGreater(abs(top_value), 1.0e-12, "Cannot normalize mode shape by top-story DOF.")
            normalized_modes.append([mode_shape[index] / top_value for index in reduced_order])

        computed_shape_rows = [
            [normalized_modes[mode_index][story_index] for mode_index in range(len(normalized_modes))]
            for story_index in range(len(reduced_order))
        ]
        self._assert_matrix_close(
            computed_shape_rows,
            benchmark["mode_shape_rows"],
            tolerance=1.0e-3,
            label="Modal mode shape",
        )

        self.assertLessEqual(abs(rayleigh["alpha"] - benchmark["alpha"]), 1.0e-4)
        self.assertLessEqual(abs(rayleigh["beta"] - benchmark["beta"]), 1.0e-6)
        self._assert_matrix_close(
            _reorder_square_matrix(rayleigh["Cff"], reduced_order),
            benchmark["Cff"],
            tolerance=1.0e-2,
            label="Rayleigh Cff",
        )


if __name__ == "__main__":
    unittest.main()
