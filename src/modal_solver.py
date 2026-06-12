# src/modal_solver.py

import math
from results import ModalResults

class ModalSolverError(Exception):
    """Custom exception raised for errors during modal analysis."""
    pass

class ModalSolver:
    """
    Solves the generalized eigenvalue problem [K]{phi} = w^2 [M]{phi} entirely from scratch.
    It utilizes the Jacobi Eigenvalue Algorithm augmented with Cholesky decomposition 
    to handle non-diagonal or consistent mass matrices without using NumPy.
    """
    
    def __init__(self, K: list, M: list):
        self.n = len(K)
        if self.n == 0:
            raise ModalSolverError("Stiffness matrix is empty.")
            
        # Deep copy matrices to prevent modifying the originals
        self.K = [row[:] for row in K]
        self.M = [row[:] for row in M]
        
        self.results = None

    def solve(self, r: list | None = None, num_modes: int = 10) -> ModalResults:
        """
        Executes the full modal analysis pipeline, sorts the modes, extracts
        the specified number of fundamental modes, and computes physical properties.
        """
        if self.n == 0:
            return []

        if r is None:
            r = [1.0] * self.n
        if len(r) != self.n:
            raise ModalSolverError("Influence vector length must match matrix size.")

        active, massless_coupled, disconnected = self._dynamic_dofs()
        if not active:
            raise ModalSolverError("No positive-mass dynamic DOFs available for modal analysis.")

        K_work = self._condense_stiffness(active, massless_coupled)
        M_work = self._submatrix(self.M, active, active)
        r_work = [r[i] for i in active]
        n_work = len(active)

        try:
            # 1. Cholesky Decomposition of Mass Matrix: M = L * L^T
            L = self._cholesky(M_work)
            
            # 2. Invert Lower Triangular Matrix L
            L_inv = self._invert_lower_triangular(L)
            L_inv_T = self._transpose(L_inv)
            
            # 3. Transform to Standard Eigenvalue Problem: A = L^-1 * K * L^-T
            temp = self._matmul(L_inv, K_work)
            A = self._matmul(temp, L_inv_T)
            
            # 4. Extract eigenvalues and standard eigenvectors using Jacobi method
            lambdas, Y = self._jacobi(A)
            
            # 5. Transform standard eigenvectors back to physical coordinates: Phi = L^-T * Y
            Phi_matrix = self._matmul(L_inv_T, Y)
        except Exception as e:
            raise ModalSolverError(f"Eigensolver failed to converge or encountered singularity: {str(e)}")
            
        # Extract columns into individual vector lists
        Phi = []
        for j in range(n_work):
            col = [Phi_matrix[i][j] for i in range(n_work)]
            Phi.append(col)
            
        # 6. Mass-Orthonormalization of Eigenvectors (Phi^T * M * Phi = I)
        for j in range(n_work):
            M_phi = self._mat_vec_mul(M_work, Phi[j])
            m_i = self._dot(Phi[j], M_phi)
            scale = 1.0 / math.sqrt(m_i) if m_i > 0 else 1.0
            for i in range(n_work):
                Phi[j][i] *= scale
                
        # 7. Sort by eigenvalue in ascending order (Fundamental mode first)
        sorted_pairs = sorted(zip(lambdas, Phi), key=lambda x: x[0])
        
        # Limit to requested number of modes
        sorted_pairs = [(lam, phi) for lam, phi in sorted_pairs if lam > 1e-10]
        num_modes_requested = num_modes
        num_modes = min(num_modes, len(sorted_pairs))
        sorted_pairs = sorted_pairs[:num_modes]
        
        # 8. Calculate total reactive physical mass in the direction of r
        M_r = self._mat_vec_mul(M_work, r_work)
        total_mass_dir = self._dot(r_work, M_r)
        
        # 9. Compute Modal Properties
        eigenvalues = []
        frequencies = []
        periods = []
        mode_shapes = []
        modal_masses = []
        participation_factors = []
        effective_masses = []
        mass_participation_ratios = []
        for i, (lam, phi) in enumerate(sorted_pairs):
            # Angular Frequency (omega)
            omega_sq = lam if lam > 0 else 0.0
            omega = math.sqrt(omega_sq)
            
            # Frequency (Hz) and Period (s)
            freq = omega / (2.0 * math.pi)
            period = 1.0 / freq if freq > 1e-9 else float('inf')
            
            # Modal Participation Factor & Effective Mass
            # (Modal mass is strictly 1.0 due to orthonormalization)
            M_phi = self._mat_vec_mul(M_work, phi)
            modal_mass = self._dot(phi, M_phi)
            gamma = self._dot(phi, M_r)
            eff_mass = gamma**2
            mass_ratio = (eff_mass / total_mass_dir) if total_mass_dir > 1e-9 else 0.0
            full_phi = self._expand_condensed_mode(phi, active, massless_coupled)

            eigenvalues.append(lam)
            frequencies.append(freq)
            periods.append(period)
            mode_shapes.append(full_phi)
            modal_masses.append(modal_mass)
            participation_factors.append(gamma)
            effective_masses.append(eff_mass)
            mass_participation_ratios.append(mass_ratio)

        self.results = ModalResults(
            K=[row[:] for row in self.K],
            M=[row[:] for row in self.M],
            eigenvalues=eigenvalues,
            frequencies=frequencies,
            periods=periods,
            mode_shapes=mode_shapes,
            modal_masses=modal_masses,
            participation_factors=participation_factors,
            effective_masses=effective_masses,
            mass_participation_ratios=mass_participation_ratios,
            influence_vector=r[:],
            total_participating_mass=total_mass_dir,
            num_modes_requested=num_modes_requested,
            num_modes_extracted=len(eigenvalues),
        )
        return self.results

    def print_summary(self):
        """Prints a neatly formatted console summary of the modal analysis results."""
        if not self.results:
            print("No modal results available.")
            return
            
        print("\n" + "="*85)
        print(f"{'MODAL ANALYSIS SUMMARY':^85}")
        print("="*85)
        print(f"{'Mode':<6} | {'Freq (Hz)':<12} | {'Period (s)':<12} | {'Part. Factor':<15} | {'Eff. Mass':<12} | {'Mass Part (%)':<15}")
        print("-" * 85)
        
        cumulative_mass = 0.0
        for i, freq in enumerate(self.results.frequencies):
            mass_part_pct = self.results.mass_participation_ratios[i] * 100.0
            cumulative_mass += mass_part_pct
            print(f"{i + 1:<6} | {freq:<12.4f} | {self.results.periods[i]:<12.4f} | "
                  f"{self.results.participation_factors[i]:<15.4f} | {self.results.effective_masses[i]:<12.4f} | {mass_part_pct:<6.2f}%")
        
        print("-" * 85)
        print(f"Cumulative Mass Participation: {cumulative_mass:.2f}%")
        print("="*85 + "\n")

    def export_educational_output(self, filepath: str, modal_results: ModalResults):
        """Exports detailed modal properties and mode shape vectors to a text file."""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("STRUCTURAL MODAL ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"{'Mode':<6} {'Freq (Hz)':<12} {'Period (s)':<12} {'Eff. Mass':<12} {'Mass Part (%)':<15}\n")
            f.write("-" * 70 + "\n")
            for i, freq in enumerate(modal_results.frequencies):
                f.write(f"{i + 1:<6} {freq:<12.4f} {modal_results.periods[i]:<12.4f} "
                        f"{modal_results.effective_masses[i]:<12.4f} {modal_results.mass_participation_ratios[i] * 100.0:<6.2f}%\n")
            
            f.write("\n\n")
            f.write("MASS-ORTHONORMALIZED MODE SHAPES (EIGENVECTORS)\n")
            f.write("=" * 70 + "\n")
            
            for mode_index, shape in enumerate(modal_results.mode_shapes):
                f.write(f"\nMode {mode_index + 1} (f = {modal_results.frequencies[mode_index]:.4f} Hz, T = {modal_results.periods[mode_index]:.4f} s)\n")
                f.write("-" * 40 + "\n")
                f.write(f"{'DOF':<8} {'Displacement':<15}\n")
                for i, val in enumerate(shape):
                    f.write(f"{i:<8} {val:<15.6e}\n")

    # ==========================================
    # CORE ALGORITHMS & NATIVE MATH HELPERS
    # ==========================================

    def _jacobi(self, A: list, tol: float = 1e-12, max_iter: int = 1000):
        n = len(A)
        V = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        D = [row[:] for row in A]
        
        for _ in range(max_iter):
            max_val = 0.0
            p, q = 0, 1
            for i in range(n):
                for j in range(i + 1, n):
                    if abs(D[i][j]) > max_val:
                        max_val = abs(D[i][j])
                        p, q = i, j
                        
            if max_val < tol:
                break
                
            diff = D[q][q] - D[p][p]
            if abs(D[p][q]) < 1e-15:
                c, s = 1.0, 0.0
            else:
                phi = diff / (2.0 * D[p][q])
                t = 1.0 / (abs(phi) + math.sqrt(phi**2 + 1.0))
                if phi < 0.0:
                    t = -t
                c = 1.0 / math.sqrt(1.0 + t**2)
                s = t * c
                
            tau = s / (1.0 + c)
            temp_Dpq = D[p][q]
            
            D[p][p] = D[p][p] - t * temp_Dpq
            D[q][q] = D[q][q] + t * temp_Dpq
            D[p][q] = D[q][p] = 0.0
            
            for i in range(n):
                if i != p and i != q:
                    temp_p = D[i][p]
                    temp_q = D[i][q]
                    D[i][p] = D[p][i] = temp_p - s * (temp_q + tau * temp_p)
                    D[i][q] = D[q][i] = temp_q + s * (temp_p - tau * temp_q)
                    
            for i in range(n):
                temp_p = V[i][p]
                temp_q = V[i][q]
                V[i][p] = temp_p - s * (temp_q + tau * temp_p)
                V[i][q] = temp_q + s * (temp_p - tau * temp_q)
                
        eigenvalues = [D[i][i] for i in range(n)]
        return eigenvalues, V

    def _cholesky(self, A: list):
        n = len(A)
        L = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1):
                s = sum(L[i][k] * L[j][k] for k in range(j))
                if i == j:
                    L[i][i] = math.sqrt(max(A[i][i] - s, 1e-15))
                else:
                    L[i][j] = (1.0 / L[j][j]) * (A[i][j] - s)
        return L

    def _invert_lower_triangular(self, L: list):
        n = len(L)
        inv = [[0.0] * n for _ in range(n)]
        for i in range(n):
            inv[i][i] = 1.0 / L[i][i]
            for j in range(i):
                s = sum(L[i][k] * inv[k][j] for k in range(j, i))
                inv[i][j] = -s / L[i][i]
        return inv

    def _transpose(self, A: list):
        return [[A[j][i] for j in range(len(A))] for i in range(len(A[0]))]

    def _matmul(self, A: list, B: list):
        rows_A, cols_A = len(A), len(A[0])
        rows_B, cols_B = len(B), len(B[0])
        result = [[0.0] * cols_B for _ in range(rows_A)]
        for i in range(rows_A):
            for j in range(cols_B):
                for k in range(cols_A):
                    result[i][j] += A[i][k] * B[k][j]
        return result

    def _mat_vec_mul(self, A: list, v: list):
        return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]

    def _dot(self, v1: list, v2: list):
        return sum(x * y for x, y in zip(v1, v2))

    def _dynamic_dofs(self):
        active = []
        disconnected = []
        for i in range(self.n):
            row_mass = sum(abs(value) for value in self.M[i])
            col_mass = sum(abs(self.M[j][i]) for j in range(self.n))
            stiffness_coupling = sum(abs(value) for value in self.K[i]) + sum(abs(self.K[j][i]) for j in range(self.n))
            if row_mass + col_mass > 1e-10:
                active.append(i)
            elif stiffness_coupling <= 1e-10:
                disconnected.append(i)
        massless_coupled = [i for i in range(self.n) if i not in active and i not in disconnected]
        return active, massless_coupled, disconnected

    def _submatrix(self, A: list, rows: list, cols: list):
        return [[A[i][j] for j in cols] for i in rows]

    def _condense_stiffness(self, active: list, massless: list):
        Kaa = self._submatrix(self.K, active, active)
        if not massless:
            return Kaa

        Kab = self._submatrix(self.K, active, massless)
        Kba = self._submatrix(self.K, massless, active)
        Kbb = self._submatrix(self.K, massless, massless)
        correction = [[0.0 for _ in active] for _ in active]
        for col in range(len(active)):
            rhs = [Kba[row][col] for row in range(len(massless))]
            solved_col = self._gaussian_solve(Kbb, rhs)
            for i in range(len(active)):
                correction[i][col] = sum(Kab[i][j] * solved_col[j] for j in range(len(massless)))

        return [[Kaa[i][j] - correction[i][j] for j in range(len(active))] for i in range(len(active))]

    def _expand_condensed_mode(self, phi_active: list, active: list, massless: list):
        full_phi = [0.0] * self.n
        for reduced_i, original_i in enumerate(active):
            full_phi[original_i] = phi_active[reduced_i]
        if massless:
            Kbb = self._submatrix(self.K, massless, massless)
            Kba = self._submatrix(self.K, massless, active)
            rhs = [-sum(Kba[i][j] * phi_active[j] for j in range(len(active))) for i in range(len(massless))]
            phi_massless = self._gaussian_solve(Kbb, rhs)
            for reduced_i, original_i in enumerate(massless):
                full_phi[original_i] = phi_massless[reduced_i]
        return full_phi

    def _gaussian_solve(self, A: list, b: list):
        n = len(b)
        aug = [A[i][:] + [b[i]] for i in range(n)]
        for col in range(n):
            pivot = max(range(col, n), key=lambda row: abs(aug[row][col]))
            if abs(aug[pivot][col]) < 1e-14:
                raise ModalSolverError("Cannot statically condense singular massless stiffness block.")
            aug[col], aug[pivot] = aug[pivot], aug[col]
            for row in range(col + 1, n):
                factor = aug[row][col] / aug[col][col]
                for k in range(col, n + 1):
                    aug[row][k] -= factor * aug[col][k]

        x = [0.0] * n
        for row in range(n - 1, -1, -1):
            rhs = aug[row][n] - sum(aug[row][col] * x[col] for col in range(row + 1, n))
            x[row] = rhs / aug[row][row]
        return x
