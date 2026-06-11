# tests/test_dynamics.py

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from parser import Node, Material, Section, Element, StructuralModel
from element_physics import ElementPhysics
from matrix_assembly import DynamicAssembler
import math_utils

class TestDynamics(unittest.TestCase):
    def setUp(self):
        # Create a simple structure with 1 frame and 1 truss for testing mass properties
        self.model = StructuralModel(name="Dynamics_Test")
        self.mat = Material(id="mat_steel", E=2.0e11)
        self.sec = Section(id="sec_frame", A=0.05, I=0.0001, d=0.3)
        self.n1 = Node(id=1, x=0.0, y=0.0)
        self.n2 = Node(id=2, x=4.0, y=0.0)
        self.n3 = Node(id=3, x=4.0, y=3.0)
        
        self.model.nodes = {1: self.n1, 2: self.n2, 3: self.n3}
        self.e1 = Element(id="E1", type="frame", node_i=self.n1, node_j=self.n2, material=self.mat, section=self.sec)
        self.e2 = Element(id="E2", type="truss", node_i=self.n2, node_j=self.n3, material=self.mat, section=self.sec)
        self.model.elements = {"E1": self.e1, "E2": self.e2}

    def test_mass_matrices_symmetry_and_size(self):
        """Verify that mass matrices for both frames and trusses are square and symmetric."""
        physics_frame = ElementPhysics(self.e1)
        physics_truss = ElementPhysics(self.e2)
        rho = 7850.0  # kg/m^3
        
        m_lumped_frame = physics_frame.get_lumped_mass_matrix(rho)
        m_cons_frame = physics_frame.get_consistent_mass_matrix(rho)
        
        m_lumped_truss = physics_truss.get_lumped_mass_matrix(rho)
        m_cons_truss = physics_truss.get_consistent_mass_matrix(rho)
        
        # Check Sizes
        self.assertEqual(len(m_lumped_frame), 6)
        self.assertEqual(len(m_lumped_frame[0]), 6)
        self.assertEqual(len(m_cons_frame), 6)
        self.assertEqual(len(m_cons_frame[0]), 6)
        
        self.assertEqual(len(m_lumped_truss), 4)
        self.assertEqual(len(m_lumped_truss[0]), 4)
        self.assertEqual(len(m_cons_truss), 4)
        self.assertEqual(len(m_cons_truss[0]), 4)
        
        # Check Symmetry
        for i in range(6):
            for j in range(6):
                self.assertAlmostEqual(m_lumped_frame[i][j], m_lumped_frame[j][i], places=6)
                self.assertAlmostEqual(m_cons_frame[i][j], m_cons_frame[j][i], places=6)
                
        for i in range(4):
            for j in range(4):
                self.assertAlmostEqual(m_lumped_truss[i][j], m_lumped_truss[j][i], places=6)
                self.assertAlmostEqual(m_cons_truss[i][j], m_cons_truss[j][i], places=6)

    def test_lumped_mass_trace_equals_total_mass(self):
        """
        Verify that the trace of the lumped mass matrix aligns with the total mass.
        For a 2D element, mass acts independently in both X and Y translation.
        Therefore, trace(M) should equal exactly 2 * (total elemental mass).
        """
        physics_frame = ElementPhysics(self.e1)
        physics_truss = ElementPhysics(self.e2)
        rho = 7850.0
        
        m_lumped_frame = physics_frame.get_lumped_mass_matrix(rho)
        m_lumped_truss = physics_truss.get_lumped_mass_matrix(rho)
        
        total_trace_frame = math_utils.trace(m_lumped_frame)
        total_trace_truss = math_utils.trace(m_lumped_truss)
        
        element_mass_frame = rho * self.sec.A * physics_frame.L
        element_mass_truss = rho * self.sec.A * physics_truss.L
        
        # Verify trace / 2 is strictly the total structural mass of the element.
        self.assertAlmostEqual(total_trace_frame / 2.0, element_mass_frame)
        self.assertAlmostEqual(total_trace_truss / 2.0, element_mass_truss)

    def test_global_mass_matrix_assembly(self):
        """Verify the global mass matrix [M] assembles symmetrically and handles missing DOFs."""
        # Manually map DOFs for dynamic validation testing
        self.n1.dofs = [-1, -1, -1] # fully restrained
        self.n2.dofs = [0, 1, 2]    # free
        self.n3.dofs = [3, 4, -1]   # pinned
        
        # We only have 5 active DOFs defined 
        assembler = DynamicAssembler(self.model, num_active_dofs=5)
        
        M_global_lumped = assembler.assemble_mass_matrix(matrix_type='lumped', rho=1.0)
        M_global_cons = assembler.assemble_mass_matrix(matrix_type='consistent', rho=1.0)
        
        # Dimensional checks
        self.assertEqual(len(M_global_lumped), 5)
        self.assertEqual(len(M_global_lumped[0]), 5)
        self.assertEqual(len(M_global_cons), 5)
        
        # Assembly Symmetry verification
        for i in range(5):
            for j in range(5):
                self.assertAlmostEqual(M_global_lumped[i][j], M_global_lumped[j][i], places=6)
                self.assertAlmostEqual(M_global_cons[i][j], M_global_cons[j][i], places=6)

if __name__ == '__main__':
    unittest.main(verbosity=2)