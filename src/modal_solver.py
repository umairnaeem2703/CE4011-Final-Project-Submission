# src/modal_solver.py

import math

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
        
        # Regularize the mass matrix to prevent singularities from massless DOFs
        # (e.g., rotational DOFs in frames where rotational inertia is neglected)
        for i in range(self.n):
            if self.M[i][i] < 1e-9:
                self.M[i][i] = 1e-9
                
        self.results = []

    def solve(self, r: list, num_modes: int = 10) -> list:
        """
        Executes the full modal analysis pipeline, sorts the modes, extracts
        the specified number of fundamental modes, and computes physical properties.
        """
        if self.n == 0:
            return []

        try:
            # 1. Cholesky Decomposition of Mass Matrix: M = L * L^T
            L = self._cholesky(self.M)
            
            # 2. Invert Lower Triangular Matrix L
            L_inv = self._invert_lower_triangular(L)
            L_inv_T = self._transpose(L_inv)
            
            # 3. Transform to Standard Eigenvalue Problem: A = L^-1 * K * L^-T
            temp = self._matmul(L_inv, self.K)
            A = self._matmul(temp, L_inv_T)
            
            # 4. Extract eigenvalues and standard eigenvectors using Jacobi method
            lambdas, Y = self._jacobi(A)
            
            # 5. Transform standard eigenvectors back to physical coordinates: Phi = L^-T * Y
            Phi_matrix = self._matmul(L_inv_T, Y)
        except Exception as e:
            raise ModalSolverError(f"Eigensolver failed to converge or encountered singularity: {str(e)}")
            
        # Extract columns into individual vector lists
        Phi = []
        for j in range(self.n):
            col = [Phi_matrix[i][j] for i in range(self.n)]
            Phi.append(col)
            
        # 6. Mass-Orthonormalization of Eigenvectors (Phi^T * M * Phi = I)
        for j in range(self.n):
            M_phi = self._mat_vec_mul(self.M, Phi[j])
            m_i = self._dot(Phi[j], M_phi)
            scale = 1.0 / math.sqrt(m_i) if m_i > 0 else 1.0
            for i in range(self.n):
                Phi[j][i] *= scale
                
        # 7. Sort by eigenvalue in ascending order (Fundamental mode first)
        sorted_pairs = sorted(zip(lambdas, Phi), key=lambda x: x[0])
        
        # Limit to requested number of modes
        num_modes = min(num_modes, self.n)
        sorted_pairs = sorted_pairs[:num_modes]
        
        # 8. Calculate total reactive physical mass in the direction of r
        M_r = self._mat_vec_mul(self.M, r)
        total_mass_dir = self._dot(r, M_r)
        
        # 9. Compute Modal Properties
        self.results = []
        for i, (lam, phi) in enumerate(sorted_pairs):
            # Angular Frequency (omega)
            omega_sq = lam if lam > 0 else 0.0
            omega = math.sqrt(omega_sq)
            
            # Frequency (Hz) and Period (s)
            freq = omega / (2.0 * math.pi)
            period = 1.0 / freq if freq > 1e-9 else float('inf')
            
            # Modal Participation Factor & Effective Mass
            # (Modal mass is strictly 1.0 due to orthonormalization)
            M_phi = self._mat_vec_mul(self.M, phi)
            gamma = self._dot(phi, M_r)
            eff_mass = gamma**2
            mass_part_pct = (eff_mass / total_mass_dir * 100.0) if total_mass_dir > 1e-9 else 0.0
            
            self.results.append({
                "mode": i + 1,
                "eigenvalue": lam,
                "omega": omega,
                "freq_hz": freq,
                "period_s": period,
                "part_factor": gamma,
                "eff_mass": eff_mass,
                "mass_part_pct": mass_part_pct,
                "phi": phi
            })
            
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
        for res in self.results:
            cumulative_mass += res['mass_part_pct']
            print(f"{res['mode']:<6} | {res['freq_hz']:<12.4f} | {res['period_s']:<12.4f} | "
                  f"{res['part_factor']:<15.4f} | {res['eff_mass']:<12.4f} | {res['mass_part_pct']:<6.2f}%")
        
        print("-" * 85)
        print(f"Cumulative Mass Participation: {cumulative_mass:.2f}%")
        print("="*85 + "\n")

    def export_educational_output(self, filepath: str, modal_results: list):
        """Exports detailed modal properties and mode shape vectors to a text file."""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("STRUCTURAL MODAL ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"{'Mode':<6} {'Freq (Hz)':<12} {'Period (s)':<12} {'Eff. Mass':<12} {'Mass Part (%)':<15}\n")
            f.write("-" * 70 + "\n")
            for res in modal_results:
                f.write(f"{res['mode']:<6} {res['freq_hz']:<12.4f} {res['period_s']:<12.4f} "
                        f"{res['eff_mass']:<12.4f} {res['mass_part_pct']:<6.2f}%\n")
            
            f.write("\n\n")
            f.write("MASS-ORTHONORMALIZED MODE SHAPES (EIGENVECTORS)\n")
            f.write("=" * 70 + "\n")
            
            for res in modal_results:
                f.write(f"\nMode {res['mode']} (f = {res['freq_hz']:.4f} Hz, T = {res['period_s']:.4f} s)\n")
                f.write("-" * 40 + "\n")
                f.write(f"{'DOF':<8} {'Displacement':<15}\n")
                for i, val in enumerate(res['phi']):
                    f.write(f"{i:<8} {val:<15.6e}\n")

    # ==========================================
    # CORE ALGORITHMS & NATIVE MATH HELPERS
    # ==========================================

    def _jacobi(self, A: list, tol: float = 1e-12, max_iter: int = 1000):
        n = self.n
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
        n = self.n
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
        n = self.n
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
        return [sum(A[i][j] * v[j] for j in range(self.n)) for i in range(self.n)]

    def _dot(self, v1: list, v2: list):
        return sum(x * y for x, y in zip(v1, v2))