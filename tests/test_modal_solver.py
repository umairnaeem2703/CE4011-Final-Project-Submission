import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from modal_solver import ModalSolver


def _modal_mass(phi, M):
    M_phi = [sum(M[i][j] * phi[j] for j in range(len(phi))) for i in range(len(phi))]
    return sum(phi[i] * M_phi[i] for i in range(len(phi)))


def test_sdof_modal_frequency():
    """Verify: SDOF frequency f = sqrt(k/m) / (2*pi)."""
    results = ModalSolver([[8.0]], [[2.0]]).solve(r=[1.0], num_modes=1)

    assert abs(results.frequencies[0] - (2.0 / (2.0 * math.pi))) < 1e-12


def test_modal_mass_normalization():
    """Verify: each extracted mode is mass-normalized to phi^T M phi = 1."""
    M = [[2.0, 0.0], [0.0, 8.0]]
    results = ModalSolver([[18.0, 0.0], [0.0, 8.0]], M).solve(r=[1.0, 1.0], num_modes=2)

    assert all(abs(_modal_mass(phi, M) - 1.0) < 1e-12 for phi in results.mode_shapes)


def test_modal_participation_effective_mass():
    """Verify: orthogonal diagonal modes recover total participating mass."""
    results = ModalSolver([[2.0, 0.0], [0.0, 8.0]], [[2.0, 0.0], [0.0, 8.0]]).solve(
        r=[1.0, 1.0],
        num_modes=2,
    )

    assert abs(sum(results.effective_masses) - results.total_participating_mass) < 1e-12
