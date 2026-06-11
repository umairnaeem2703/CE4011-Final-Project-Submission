# src/matrix_assembly.py

import math_utils
from parser import StructuralModel, NodalLoad
from element_physics import ElementPhysics

class MatrixAssembler:
    def __init__(self, model: StructuralModel, num_active_dofs: int, semi_bandwidth: int):
        self.model = model
        self.num_active_dofs = num_active_dofs
        self.semi_bandwidth = semi_bandwidth

    def assemble_full_stiffness_matrix(self) -> list:
        """
        Assembles the full NxN global stiffness matrix [K] for educational output.
        Unlike the banded matrix used for solving, this produces a symmetric 2D list
        that students can easily read and verify against hand calculations.
        """
        K_full = math_utils.zeros(self.num_active_dofs, self.num_active_dofs)

        for element_id, element in self.model.elements.items():
            physics = ElementPhysics(element)
            
            k_local = physics.get_local_k()
            # Dummy FEF since we only care about stiffness here
            fef_dummy = math_utils.zeros(len(k_local), 1) 
            k_condensed, _ = physics.condense(k_local, fef_dummy)
            k_global, _ = physics.transform_to_global(k_condensed, fef_dummy)
            
            if element.type == 'truss':
                element_dofs = element.node_i.dofs[0:2] + element.node_j.dofs[0:2]
                num_dofs = 4
            else:
                element_dofs = element.node_i.dofs + element.node_j.dofs
                num_dofs = 6

            for i in range(num_dofs):
                dof_i = element_dofs[i]
                if dof_i >= 0:
                    for j in range(num_dofs):
                        dof_j = element_dofs[j]
                        if dof_j >= 0:
                            K_full[dof_i][dof_j] += k_global[i][j]

        return K_full

    def banded_to_full(self, K_banded: list) -> list:
        """Expand the symmetric banded active stiffness matrix into a full matrix."""
        n = len(K_banded)
        K_full = math_utils.zeros(n, n)

        for i, row in enumerate(K_banded):
            for offset, value in enumerate(row):
                j = i + offset
                if j >= n:
                    break
                K_full[i][j] = value
                K_full[j][i] = value

        return K_full

    def reduce_free_system(self, K_full: list, F_full: list) -> tuple[list, list]:
        """
        Return the Phase 2 reduced free-DOF system.

        Current DOF numbering contains only active/free equations, with restrained
        DOFs represented by -1 in the model map. Therefore Kff/Ff are the active
        assembled system after prescribed-support effects have been moved to F.
        """
        free_dofs = list(range(self.num_active_dofs))
        Kff = [[K_full[i][j] for j in free_dofs] for i in free_dofs]
        Ff = [[F_full[i][0]] for i in free_dofs]
        return Kff, Ff

    def assemble(self, load_case_id: str) -> tuple[list, list]:
        """
        Assembles banded stiffness matrix [K] and load vector {F}.
        Handles element contributions, nodal loads, and settlement forces via element-level
        unbalanced loads: F -= K_element @ u_prescribed.
        """
        safe_bandwidth = max(self.semi_bandwidth + 1, self.num_active_dofs)
        K_banded = math_utils.zeros(self.num_active_dofs, safe_bandwidth)
        F_global = math_utils.zeros(self.num_active_dofs, 1)

        load_case = self.model.load_cases.get(load_case_id)
        if not load_case:
            raise ValueError(f"Load case '{load_case_id}' not found in the model.")

        # Stage 1: Assemble element stiffness and fixed-end forces
        for element_id, element in self.model.elements.items():
            physics = ElementPhysics(element)

            k_local = physics.get_local_k()
            fef_local = physics.get_local_fef(load_case, self.model)

            k_condensed, fef_condensed = physics.condense(k_local, fef_local)
            k_global, fef_global = physics.transform_to_global(k_condensed, fef_condensed)
            
            if element.type == 'truss':
                element_dofs = element.node_i.dofs[0:2] + element.node_j.dofs[0:2]
                num_dofs = 4
            else:
                element_dofs = element.node_i.dofs + element.node_j.dofs
                num_dofs = 6

            # Step 2: Build d_prescribed (settlement at restrained DOFs)
            d_prescribed = math_utils.zeros(num_dofs, 1)

            sup_i = self.model.supports.get(element.node_i.id)
            if sup_i is not None:
                if sup_i.restrain_ux: d_prescribed[0][0] = sup_i.settlement_ux
                if sup_i.restrain_uy: d_prescribed[1][0] = sup_i.settlement_uy
                if element.type == 'frame' and sup_i.restrain_rz: d_prescribed[2][0] = sup_i.settlement_rz

            j_offset = 2 if element.type == 'truss' else 3
            sup_j = self.model.supports.get(element.node_j.id)
            if sup_j is not None:
                if sup_j.restrain_ux: d_prescribed[j_offset][0] = sup_j.settlement_ux
                if sup_j.restrain_uy: d_prescribed[j_offset + 1][0] = sup_j.settlement_uy
                if element.type == 'frame' and sup_j.restrain_rz: d_prescribed[j_offset + 2][0] = sup_j.settlement_rz

            # Step 3: Compute equivalent element force vector
            f_settlement = math_utils.matmul(k_global, d_prescribed)

            # Step 4: Assemble K (active-active) and subtract F_eq from F_global
            for row_idx in range(num_dofs):
                dof_row = element_dofs[row_idx]
                if dof_row >= 0:
                    F_global[dof_row][0] -= (fef_global[row_idx][0] + f_settlement[row_idx][0])
                    for col_idx in range(num_dofs):
                        dof_col = element_dofs[col_idx]
                        if dof_col >= dof_row:
                            band_col = dof_col - dof_row
                            K_banded[dof_row][band_col] += k_global[row_idx][col_idx]

        # Stage 2: Add nodal loads
        for load in load_case.loads:
            if isinstance(load, NodalLoad):
                node = load.node
                nodal_forces = load.NodalLoads()

                if node.dofs[0] >= 0: F_global[node.dofs[0]][0] += nodal_forces[0]
                if node.dofs[1] >= 0: F_global[node.dofs[1]][0] += nodal_forces[1]
                if len(node.dofs) > 2 and node.dofs[2] >= 0: F_global[node.dofs[2]][0] += nodal_forces[2]

        # Stage 3: Apply settlement constraint forces via FULL un-condensed stiffness
        for element_id, element in self.model.elements.items():
            if element.type == 'truss':
                element_dofs = element.node_i.dofs[0:2] + element.node_j.dofs[0:2]
                num_dofs = 4
            else:
                element_dofs = element.node_i.dofs + element.node_j.dofs
                num_dofs = 6
            
            u_prescribed = math_utils.zeros(num_dofs, 1)
            has_settlement = False
            
            node_i_support = self.model.supports.get(element.node_i.id)
            if node_i_support is not None:
                if node_i_support.restrain_ux: u_prescribed[0][0] = node_i_support.settlement_ux; has_settlement = True
                if node_i_support.restrain_uy: u_prescribed[1][0] = node_i_support.settlement_uy; has_settlement = True
                if node_i_support.restrain_rz: u_prescribed[2][0] = node_i_support.settlement_rz; has_settlement = True
            
            node_j_offset = 2 if element.type == 'truss' else 3
            node_j_support = self.model.supports.get(element.node_j.id)
            if node_j_support is not None:
                if node_j_support.restrain_ux: u_prescribed[node_j_offset + 0][0] = node_j_support.settlement_ux; has_settlement = True
                if node_j_support.restrain_uy: u_prescribed[node_j_offset + 1][0] = node_j_support.settlement_uy; has_settlement = True
                if node_j_support.restrain_rz and node_j_offset + 2 < num_dofs: u_prescribed[node_j_offset + 2][0] = node_j_support.settlement_rz; has_settlement = True
            
            if not has_settlement:
                continue
            
            physics = ElementPhysics(element)
            k_local = physics.get_local_k()
            fef_dummy = math_utils.zeros(num_dofs, 1)
            k_global_full, _ = physics.transform_to_global(k_local, fef_dummy)
            
            f_unbalanced = math_utils.matmul(k_global_full, u_prescribed)
            
            for dof_idx in range(len(element_dofs)):
                dof = element_dofs[dof_idx]
                if dof >= 0:
                    F_global[dof][0] -= f_unbalanced[dof_idx][0]

        K_full = self.banded_to_full(K_banded)
        Kff, Ff = self.reduce_free_system(K_full, F_global)
        self.model.cached_K = K_full
        self.model.cached_F = F_global
        self.model.cached_Kff = Kff
        self.model.cached_Ff = Ff

        return K_banded, F_global


class DynamicAssembler:
    def __init__(self, model: StructuralModel, num_active_dofs: int):
        self.model = model
        self.num_active_dofs = num_active_dofs

    def assemble_mass_matrix(self, matrix_type: str = 'lumped', rho: float = 1.0) -> list:
        """
        Assembles the global mass matrix [M] as a full 2D list.
        matrix_type can be 'lumped' or 'consistent'.
        """
        M_global = math_utils.zeros(self.num_active_dofs, self.num_active_dofs)

        for element_id, element in self.model.elements.items():
            physics = ElementPhysics(element)
            m_elem_global = physics.get_global_mass_matrix(matrix_type, rho)
            
            if element.type == 'truss':
                element_dofs = element.node_i.dofs[0:2] + element.node_j.dofs[0:2]
            else:
                element_dofs = element.node_i.dofs + element.node_j.dofs
                
            num_dofs = len(element_dofs)
            
            for i in range(num_dofs):
                dof_i = element_dofs[i]
                if dof_i >= 0:
                    for j in range(num_dofs):
                        dof_j = element_dofs[j]
                        if dof_j >= 0:
                            M_global[dof_i][dof_j] += m_elem_global[i][j]

        return M_global
