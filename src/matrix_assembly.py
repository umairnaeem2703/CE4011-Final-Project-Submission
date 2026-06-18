# src/matrix_assembly.py

import math_utils
from parser import StructuralModel, NodalLoad
from element_physics import ElementPhysics
from results import DynamicAssemblyData

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

        K_full = self.banded_to_full(K_banded)
        Kff, Ff = self.reduce_free_system(K_full, F_global)
        self.model.cached_K = K_full
        self.model.cached_F = F_global
        self.model.cached_Kff = Kff
        self.model.cached_Ff = Ff

        return K_banded, F_global


class DynamicAssembler:
    SUPPORTED_UNIT_SYSTEMS = ("kN_m_tonne", "N_m_kg", "kN_m_kNsec2_per_m")

    def __init__(self, model: StructuralModel, num_active_dofs: int):
        self.model = model
        self.num_active_dofs = num_active_dofs
        self._explicit_rotational_inertia_dofs = set()

    def _mass_to_internal(self, value: float) -> float:
        """Convert mass-like inputs to internal kN-m-tonne-s units."""
        unit_system = getattr(self.model, 'unit_system', 'kN_m_tonne')
        if unit_system not in self.SUPPORTED_UNIT_SYSTEMS:
            raise ValueError(f"Unsupported unit system '{unit_system}'.")
        if unit_system == "N_m_kg":
            return value / 1000.0
        return value

    def assemble_mass_matrix(self, matrix_type: str = 'lumped', rho: float = None) -> list:
        """
        Assembles the global mass matrix [M] as a full 2D list.
        matrix_type can be 'lumped' or 'consistent'.
        """
        M_global = math_utils.zeros(self.num_active_dofs, self.num_active_dofs)

        for element_id, element in self.model.elements.items():
            physics = ElementPhysics(element)
            density = element.material.density if rho is None else rho
            m_elem_global = physics.get_global_mass_matrix(matrix_type, self._mass_to_internal(density))
            
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

        self._add_explicit_lumped_masses(M_global)
        self.model.cached_M = M_global
        return M_global

    def _add_explicit_lumped_masses(self, M_global: list) -> None:
        """Scatter explicit nodal masses from model.lumped_masses onto active DOFs."""
        self._explicit_rotational_inertia_dofs = set()

        for node_id, mass_data in self.model.lumped_masses.items():
            node = self.model.nodes[node_id]

            if isinstance(mass_data, (int, float)):
                masses = [float(mass_data), float(mass_data), 0.0]
            else:
                masses = [
                    float(getattr(mass_data, 'mass_ux', 0.0)),
                    float(getattr(mass_data, 'mass_uy', 0.0)),
                    float(getattr(mass_data, 'inertia_rz', 0.0)),
                ]

            for local_index, mass in enumerate(masses):
                dof = node.dofs[local_index]
                if dof >= 0:
                    mass_internal = self._mass_to_internal(mass)
                    M_global[dof][dof] += mass_internal
                    if local_index == 2 and abs(mass_internal) > 1.0e-12:
                        self._explicit_rotational_inertia_dofs.add(dof)

    def assemble_damping_matrix(self, K_full: list, M_full: list) -> list:
        """Assemble Rayleigh damping C = alpha*M + beta*K."""
        if self.model.damping_model not in ('rayleigh', 'none'):
            raise ValueError(f"Unsupported damping model '{self.model.damping_model}'.")

        alpha = self.model.rayleigh_alpha if self.model.damping_model == 'rayleigh' else 0.0
        beta = self.model.rayleigh_beta if self.model.damping_model == 'rayleigh' else 0.0
        C_global = math_utils.zeros(self.num_active_dofs, self.num_active_dofs)

        for i in range(self.num_active_dofs):
            for j in range(self.num_active_dofs):
                C_global[i][j] = alpha * M_full[i][j] + beta * K_full[i][j]

        self.model.cached_C = C_global
        return C_global

    def get_active_dynamic_dofs(self, M_full: list) -> list:
        """Return translational mass DOFs plus rotations with explicit inertia."""
        dof_types = self._get_dof_types()
        active = []
        for dof in range(self.num_active_dofs):
            if abs(M_full[dof][dof]) <= 1.0e-12:
                continue
            if dof_types.get(dof) in (0, 1) or dof in self._explicit_rotational_inertia_dofs:
                active.append(dof)
        return active

    def _get_dof_types(self) -> dict:
        """Map global DOF index to local node DOF type: 0=ux, 1=uy, 2=rz."""
        dof_types = {}
        for node in self.model.nodes.values():
            for local_index, dof in enumerate(node.dofs):
                if dof >= 0:
                    dof_types.setdefault(dof, local_index)
        return dof_types

    def _has_stiffness_coupling(self, K_full: list, dof: int) -> bool:
        for j in range(self.num_active_dofs):
            if abs(K_full[dof][j]) > 1.0e-12 or abs(K_full[j][dof]) > 1.0e-12:
                return True
        return False

    def reduce_dynamic_matrices(
        self,
        K_full: list,
        M_full: list,
        C_full: list,
        active_dynamic_dofs: list = None,
    ) -> tuple[list, list, list, list]:
        """Condense stiffness-coupled massless DOFs and reduce M/C for Phase 4."""
        retained = active_dynamic_dofs if active_dynamic_dofs is not None else self.get_active_dynamic_dofs(M_full)
        retained_set = set(retained)
        massless = [i for i in range(self.num_active_dofs) if i not in retained_set]
        condensed = [i for i in massless if self._has_stiffness_coupling(K_full, i)]

        Kaa = [[K_full[i][j] for j in retained] for i in retained]
        Maa = [[M_full[i][j] for j in retained] for i in retained]
        if not retained:
            return Kaa, Maa, [], []

        if condensed:
            Kam = [[K_full[i][j] for j in condensed] for i in retained]
            Kma = [[K_full[i][j] for j in retained] for i in condensed]
            Kmm = [[K_full[i][j] for j in condensed] for i in condensed]
            Kmm_inv = math_utils.invert_matrix(Kmm)
            correction = math_utils.matmul(math_utils.matmul(Kam, Kmm_inv), Kma)
            Kff = math_utils.subtract(Kaa, correction)
        else:
            Kff = Kaa

        alpha = self.model.rayleigh_alpha if self.model.damping_model == 'rayleigh' else 0.0
        beta = self.model.rayleigh_beta if self.model.damping_model == 'rayleigh' else 0.0
        Cff = math_utils.zeros(len(retained), len(retained))
        for i in range(len(retained)):
            for j in range(len(retained)):
                Cff[i][j] = alpha * Maa[i][j] + beta * Kff[i][j]

        return Kff, Maa, Cff, condensed

    def assemble_dynamic_data(self, K_full: list, matrix_type: str = 'lumped', rho: float = None) -> DynamicAssemblyData:
        """Build and cache full/reduced dynamic assembly data."""
        M_full = self.assemble_mass_matrix(matrix_type, rho)
        C_full = self.assemble_damping_matrix(K_full, M_full)
        active_dynamic_dofs = self.get_active_dynamic_dofs(M_full)
        Kff, Mff, Cff, condensed = self.reduce_dynamic_matrices(K_full, M_full, C_full, active_dynamic_dofs)

        return DynamicAssemblyData(
            K=K_full,
            M=M_full,
            C=C_full,
            Kff=Kff,
            Mff=Mff,
            Cff=Cff,
            dof_map=self.model.cached_dof_map.copy() if self.model.cached_dof_map else {},
            free_dofs=list(range(self.num_active_dofs)),
            active_dynamic_dofs=active_dynamic_dofs,
            condensed_massless_dofs=condensed,
            unit_system=getattr(self.model, 'unit_system', 'kN_m_tonne'),
            rayleigh_alpha=self.model.rayleigh_alpha,
            rayleigh_beta=self.model.rayleigh_beta,
        )
