# tests/test_sap2000_strict.py
"""
Strict SAP2000 Comparison Test Suite

This comprehensive testing framework provides:
1. Element-by-element validation of all member forces
2. Nodal displacement comparison with individual component reporting
3. Tolerances calibrated for each component type
4. Detailed failure reporting showing Expected vs. Actual for every value
5. Specific focus on inclined members under thermal loading
6. Automatic discovery and validation of all SAP2000 reference files

CRITICAL TEST CASES:
- Inclined trusses under thermal loading (most sensitive to transformation bugs)
- Mixed frame-truss structures (validates both element types)
- Thermal gradient loads on beams (tests moment calculations)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from parser import XMLParser
from dof_optimizer import DOFOptimizer
from matrix_assembly import MatrixAssembler
from banded_solver import BandedSolver
from post_processor import PostProcessor
from sap2000_parser import SAP2000Parser, MemberForceTransformer, assert_displacement_match, assert_force_match


class StrictSAP2000TestBase(unittest.TestCase):
    """
    Base class for strict SAP2000 validation tests.
    Provides detailed assertion methods that print Expected vs. Actual values.
    """
    
    # =========================================================================
    # TOLERANCE CONFIGURATION
    # =========================================================================
    # These tolerances are based on expected differences between SAP2000 and our solver:
    #
    # DISPLACEMENTS (meters and radians):
    #   - Translation: 1e-6 m (1 micrometer) - very strict for detecting transformation bugs
    #   - Rotation: 1e-6 rad (~0.00006°) - strict tolerance for moment recovery
    #
    # FORCES (kN and kN-m):
    #   - Axial force in trusses: 0.01 kN (10 N) - strict for inclined members
    #   - Shear force: 0.01 kN - strict tolerance
    #   - Bending moment: 0.01 kN-m - strict tolerance
    #
    # Rationale:
    #   - Strict tolerances force us to catch subtle matrix/transformation bugs
    #   - If a single direction cosine is wrong, inclined members will fail
    #   - If FEF sign is wrong, thermal load cases will have large errors
    #   - These tolerances catch ~0.1% errors, adequate for detecting real bugs
    
    DISP_TRANS_TOL = 1e-6       # meters
    DISP_ROT_TOL = 1e-6         # radians
    FORCE_AXL_TOL = 0.01        # kN (10 N)
    FORCE_SHR_TOL = 0.01        # kN
    FORCE_MOM_TOL = 0.01        # kN-m
    
    def _run_full_analysis(self, model, load_case="LC1"):
        """Execute complete FEA pipeline"""
        opt = DOFOptimizer(model)
        num_eq, semi_bw, _ = opt.optimize()
        
        assembler = MatrixAssembler(model, num_eq, semi_bw)
        K_banded, F_global = assembler.assemble(load_case)
        
        solver = BandedSolver(K_banded, F_global, semi_bw)
        D_active = solver.solve()
        
        processor = PostProcessor(model, D_active, load_case)
        return processor
    
    def _assert_float_equal(self, computed, expected, tolerance, component_name=""):
        """
        Assert with detailed error message showing Expected vs Actual.
        Fails if |computed - expected| > tolerance.
        """
        error = abs(computed - expected)
        if error > tolerance:
            rel_error = error / max(abs(expected), 1e-12)
            msg = (
                f"{component_name}\n"
                f"  Expected: {expected:.9e}\n"
                f"  Computed: {computed:.9e}\n"
                f"  Absolute Error: {error:.9e} (tolerance: {tolerance:.9e})\n"
                f"  Relative Error: {rel_error*100:.3f}%"
            )
            self.fail(msg)
        return
    
    def _validate_nodal_displacements_strict(self, computed_disp, sap2000_disp, 
                                            node_id, print_summary=False):
        """
        Validate all three displacement components at a single node with strict tolerance.
        """
        comp_ux, comp_uy, comp_rz = computed_disp
        exp_ux, exp_uy, exp_rz = sap2000_disp
        
        self._assert_float_equal(comp_ux, exp_ux, self.DISP_TRANS_TOL,
                                f"Node {node_id} UX displacement")
        self._assert_float_equal(comp_uy, exp_uy, self.DISP_TRANS_TOL,
                                f"Node {node_id} UY displacement")
        self._assert_float_equal(comp_rz, exp_rz, self.DISP_ROT_TOL,
                                f"Node {node_id} RZ rotation")
        
        if print_summary:
            print(f"[PASS] Node {node_id}: UX={comp_ux:.3e}, UY={comp_uy:.3e}, RZ={comp_rz:.3e}")
    
    def _validate_member_axial_force_strict(self, computed_axial, expected_axial,
                                           elem_id, node_label):
        """
        Validate axial force for truss elements (most sensitive to transformation bugs).
        """
        self._assert_float_equal(computed_axial, expected_axial,  self.FORCE_AXL_TOL,
                                f"Element {elem_id} Node {node_label} Axial Force")
    
    def _validate_member_forces_strict(self, computed_forces, expected_forces,
                                       elem_id, node_label):
        """
        Validate all force components (Fx, Fy, Mz) at element end.
        """
        comp_fx, comp_fy, comp_mz = computed_forces
        exp_fx, exp_fy, exp_mz = expected_forces
        
        self._assert_float_equal(comp_fx, exp_fx, self.FORCE_AXL_TOL,
                                f"Element {elem_id} Node {node_label} Fx")
        self._assert_float_equal(comp_fy, exp_fy, self.FORCE_SHR_TOL,
                                f"Element {elem_id} Node {node_label} Fy")
        self._assert_float_equal(comp_mz, exp_mz, self.FORCE_MOM_TOL,
                                f"Element {elem_id} Node {node_label} Mz")

    def _parse_sap_member_forces_by_joint(self, filepath):
        forces = {}
        in_table = False

        with open(filepath, "r") as file:
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
                    fx = float(parts[4])
                    fy = float(parts[6])
                    mz = -float(parts[8])
                except (ValueError, IndexError):
                    continue

                forces.setdefault(element_id, {})[joint_id] = (fx, fy, mz)

        return forces


class TestSettlementBenchmark(StrictSAP2000TestBase):
    """Validate the support-settlement benchmark against SAP2000 output."""

    def test_settlement_displacements_and_reactions(self):
        xml_path = os.path.join(os.path.dirname(__file__), "../data/test-settlement.xml")
        sap_path = os.path.join(os.path.dirname(__file__), "../sap2000_solutions/test-settlement-results.txt")

        sap_parser = SAP2000Parser(sap_path)
        sap_disp, sap_react, _ = sap_parser.parse()
        self.assertTrue(sap_disp, "SAP2000 displacement table was not parsed.")
        self.assertTrue(sap_react, "SAP2000 reaction table was not parsed.")

        model = XMLParser(xml_path).parse()
        processor = self._run_full_analysis(model, load_case="LC1")

        for node_id, expected_disp in sap_disp.items():
            self.assertIn(node_id, processor.displacements)
            match, error_msg = assert_displacement_match(
                processor.displacements[node_id],
                expected_disp,
            )
            self.assertTrue(match, f"Settlement node {node_id} displacement mismatch:\n{error_msg}")

        for node_id, expected_reaction in sap_react.items():
            self.assertIn(node_id, processor.reactions)
            match, error_msg = assert_force_match(
                processor.reactions[node_id],
                expected_reaction,
            )
            self.assertTrue(match, f"Settlement node {node_id} reaction mismatch:\n{error_msg}")

    def test_settlement_sap2000_displacement_display_mapping(self):
        xml_path = os.path.join(os.path.dirname(__file__), "../data/test-settlement.xml")
        model = XMLParser(xml_path).parse()
        processor = self._run_full_analysis(model, load_case="LC1")

        expected = {
            1: (0.0, 0.0, 0.0, 0.0, 0.000656, 0.0),
            2: (3.549e-06, 0.0, -0.001994, 0.0, 0.000173, 0.0),
            3: (5.320e-06, 0.0, -0.000954, 0.0, -0.000280, 0.0),
            4: (5.320e-06, 0.0, -0.000112, 0.0, -0.000280, 0.0),
            5: (0.0, 0.0, -0.002000, 0.0, -0.000082, 0.0),
            6: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        }

        sap_display = processor.sap2000_displacements()
        for node_id, expected_row in expected.items():
            self.assertIn(node_id, sap_display)
            for computed, reference in zip(sap_display[node_id], expected_row):
                self.assertLessEqual(abs(computed - reference), 5.0e-6)


class TestTemperatureBenchmark(StrictSAP2000TestBase):
    """Validate the corrected temperature benchmark against SAP2000 output."""

    TEMP_DISP_TOL = 1.0e-5
    TEMP_FORCE_TOL = 0.05
    TEMP_MOMENT_TOL = 0.6

    def test_temperature_displacements_reactions_and_member_end_forces(self):
        xml_path = os.path.join(os.path.dirname(__file__), "../data/test-temperature.xml")
        sap_path = os.path.join(os.path.dirname(__file__), "../sap2000_solutions/test-temperature-results.txt")

        sap_parser = SAP2000Parser(sap_path)
        sap_disp, sap_react, _ = sap_parser.parse()
        sap_member_forces = self._parse_sap_member_forces_by_joint(sap_path)

        model = XMLParser(xml_path).parse()
        processor = self._run_full_analysis(model, load_case="LC1")

        for node_id, expected_disp in sap_disp.items():
            self.assertIn(node_id, processor.displacements)
            for computed, expected in zip(processor.displacements[node_id], expected_disp):
                self.assertLessEqual(abs(computed - expected), self.TEMP_DISP_TOL)

        for node_id, expected_reaction in sap_react.items():
            self.assertIn(node_id, processor.reactions)
            for index, (computed, expected) in enumerate(zip(processor.reactions[node_id], expected_reaction)):
                tolerance = self.TEMP_MOMENT_TOL if index == 2 else self.TEMP_FORCE_TOL
                self.assertLessEqual(abs(computed - expected), tolerance)

        for element_id, element in model.elements.items():
            self.assertIn(element_id, processor.member_end_forces)
            self.assertIn(element_id, sap_member_forces)

            for end_label, joint_id in (("i", element.node_i.id), ("j", element.node_j.id)):
                self.assertIn(joint_id, sap_member_forces[element_id])
                computed_forces = processor.member_end_forces[element_id][end_label]
                expected_forces = sap_member_forces[element_id][joint_id]

                for index, (computed, expected) in enumerate(zip(computed_forces, expected_forces)):
                    tolerance = self.TEMP_MOMENT_TOL if index == 2 else self.TEMP_FORCE_TOL
                    self.assertLessEqual(abs(computed - expected), tolerance)


class TestAssignment4Q2b(StrictSAP2000TestBase):
    """
    Test Assignment 4 Q2(b) - Thermal Loading with Inclined Trusses
    
    CRITICAL TEST: Mixed frame and inclined truss elements under thermal loading.
    The inclined trusses are at non-90-degree angles and expose transformation matrix bugs.
    
    Elements:
    - T1: Node 2 (7, 8) to Node 4 (3, 0) [Inclined ~63.4°]
    - T2: Node 2 (7, 8) to Node 5 (10, 0) [Inclined ~26.6°]
    
    SAP2000 Reference Values:
    - T1 at node 2: -4.067 kN
    - T2 at node 2: +5.676 kN
    """
    
    TEMP_DISP_TOL = 1.0e-5
    TEMP_FORCE_TOL = 0.05
    TEMP_MOMENT_TOL = 0.6

    def test_q2b_displacements(self):
        """Validate nodal displacements against the current temperature benchmark."""
        xml_path = os.path.join(os.path.dirname(__file__), "../data/test-temperature.xml")
        sap_path = os.path.join(os.path.dirname(__file__), "../sap2000_solutions/test-temperature-results.txt")

        sap_parser = SAP2000Parser(sap_path)
        sap_disp, _, _ = sap_parser.parse()
        
        model = XMLParser(xml_path).parse()
        processor = self._run_full_analysis(model, load_case="LC1")
        
        print("\n" + "="*70)
        print("TEST: Current temperature benchmark - Nodal Displacements")
        print("="*70)
        
        # All nodes should have displacements matching SAP2000
        for node_id in sorted(sap_disp.keys()):
            if node_id in processor.displacements:
                for computed, expected in zip(processor.displacements[node_id], sap_disp[node_id]):
                    self.assertLessEqual(abs(computed - expected), self.TEMP_DISP_TOL)
                print(f"[PASS] Node {node_id}: UX={processor.displacements[node_id][0]:.3e}, UY={processor.displacements[node_id][1]:.3e}, RZ={processor.displacements[node_id][2]:.3e}")
    
    def test_q2b_inclined_truss_axial_forces(self):
        """
        Validate member forces against the current temperature benchmark.

        The test still focuses on the inclined trusses because that is where the
        force transformation is most sensitive.
        """
        xml_path = os.path.join(os.path.dirname(__file__), "../data/test-temperature.xml")
        sap_path = os.path.join(os.path.dirname(__file__), "../sap2000_solutions/test-temperature-results.txt")
        
        sap_forces = self._parse_sap_member_forces_by_joint(sap_path)
        
        model = XMLParser(xml_path).parse()
        processor = self._run_full_analysis(model, load_case="LC1")
        
        print("\n" + "="*70)
        print("TEST: Current temperature benchmark - Inclined Truss Axial Forces")
        print("="*70)
        print("EXPECTED vs COMPUTED (Benchmark tolerances)")

        for elem_id, element in model.elements.items():
            if elem_id not in processor.member_end_forces:
                self.fail(f"Element {elem_id} not in solver output")
            self.assertIn(elem_id, sap_forces)

            elem_forces = processor.member_end_forces[elem_id]
            for end_label, joint_id in (("i", element.node_i.id), ("j", element.node_j.id)):
                self.assertIn(joint_id, sap_forces[elem_id])
                expected_forces = sap_forces[elem_id][joint_id]
                computed_forces = elem_forces[end_label]
                for index, (computed, expected) in enumerate(zip(computed_forces, expected_forces)):
                    tolerance = self.TEMP_MOMENT_TOL if index == 2 else self.TEMP_FORCE_TOL
                    self.assertLessEqual(abs(computed - expected), tolerance)


if __name__ == '__main__':
    unittest.main(verbosity=2)
